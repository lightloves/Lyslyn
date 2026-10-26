"""Live Hot-Reload Watcher for the Lyslyn Toolchain.

Monitors source scripts and project files, automatically restarting
the runtime process upon code modifications without manual re-execution.
"""
import os
import sys
import time
import signal
import subprocess
from typing import List, Dict, Optional, Set


class FileWatcher:
    """Monitors files for modifications and triggers process reload."""
    def __init__(self, target_file: str, script_args: Optional[List[str]] = None):
        self.target_file = os.path.abspath(target_file)
        self.script_args = script_args or []
        self.base_dir = os.path.dirname(self.target_file) or "."
        self.current_process: Optional[subprocess.Popen] = None
        self._file_mtimes: Dict[str, float] = {}

    def _collect_watched_files(self) -> Set[str]:
        """Find all .lys and .env files in the project tree to watch."""
        watched = {self.target_file}
        for root, dirs, files in os.walk(self.base_dir):
            # Skip hidden directories, git, and virtualenvs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv")]
            for f in files:
                if f.endswith(".lys") or f == ".env" or f == "lyslyn.json":
                    watched.add(os.path.join(root, f))
        return watched

    def _has_changes(self) -> Optional[str]:
        """Check if any watched file has changed. Returns filename if changed."""
        watched = self._collect_watched_files()
        
        # Check existing and new files
        for fpath in watched:
            try:
                mtime = os.path.getmtime(fpath)
            except OSError:
                continue

            prev = self._file_mtimes.get(fpath)
            if prev is None:
                self._file_mtimes[fpath] = mtime
            elif mtime > prev:
                self._file_mtimes[fpath] = mtime
                return fpath

        # Check deleted files
        deleted = [f for f in self._file_mtimes if f not in watched]
        for f in deleted:
            del self._file_mtimes[f]
            return f

        return None

    def start_process(self) -> None:
        """Spawn the user script in a child process."""
        self.stop_process()

        cmd = [sys.executable, "-m", "lyslyn.cli", self.target_file] + self.script_args
        env = dict(os.environ)
        # Ensure project root is in PYTHONPATH
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        py_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{project_root}:{py_path}" if py_path else project_root

        self.current_process = subprocess.Popen(cmd, env=env)

    def stop_process(self) -> None:
        """Terminate the active child process cleanly."""
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1.5)
            except (subprocess.TimeoutExpired, Exception):
                try:
                    self.current_process.kill()
                    self.current_process.wait(timeout=1.0)
                except Exception:
                    pass
            self.current_process = None

    def run(self) -> None:
        """Main watch loop."""
        rel_target = os.path.relpath(self.target_file)
        print(f"\033[96m👀 [Lyslyn Watcher]\033[0m Monitoring '\033[1m{rel_target}\033[0m' and dependencies...")
        print(f"\033[90mPress Ctrl+C to stop watch mode.\033[0m\n")

        # Initialize timestamps
        for f in self._collect_watched_files():
            try:
                self._file_mtimes[f] = os.path.getmtime(f)
            except OSError:
                pass

        self.start_process()

        try:
            while True:
                time.sleep(0.35)
                changed_file = self._has_changes()
                if changed_file:
                    now = time.strftime("%H:%M:%S")
                    rel_changed = os.path.relpath(changed_file)
                    print(f"\n\033[93m🔄 [{now}] File change detected:\033[0m \033[1m{rel_changed}\033[0m. Restarting server...")
                    self.start_process()

        except KeyboardInterrupt:
            print("\n\033[90mStopping Lyslyn watcher...\033[0m")
            self.stop_process()
            sys.exit(0)


def watch_file(filepath: str, script_args: Optional[List[str]] = None) -> None:
    watcher = FileWatcher(filepath, script_args)
    watcher.run()

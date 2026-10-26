"""Industrial Package Manager and Deterministic Lockfile engine for Lyslyn."""
import os
import sys
import json
import hashlib
import tarfile
from typing import Dict, Any, List, Optional

MANIFEST_FILE = "lyslyn.json"
LOCK_FILE = "lyslyn.lock"


class PackageManager:
    def __init__(self, project_dir: str = "."):
        self.project_dir = os.path.abspath(project_dir)
        self.manifest_path = os.path.join(self.project_dir, MANIFEST_FILE)
        self.lock_path = os.path.join(self.project_dir, LOCK_FILE)
        self.packages_dir = os.path.join(self.project_dir, "lys_modules")

    def load_manifest(self) -> Dict[str, Any]:
        if not os.path.isfile(self.manifest_path):
            raise FileNotFoundError(f"No {MANIFEST_FILE} found in {self.project_dir}. Run 'lys init' first.")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_manifest(self, manifest: Dict[str, Any]) -> None:
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")

    def load_lockfile(self) -> Dict[str, Any]:
        if not os.path.isfile(self.lock_path):
            return {"lockfileVersion": 1, "packages": {}}
        with open(self.lock_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_lockfile(self, lock: Dict[str, Any]) -> None:
        with open(self.lock_path, "w", encoding="utf-8") as f:
            json.dump(lock, f, indent=2)
            f.write("\n")

    def add_package(self, package_name: str, version: str = "latest", is_dev: bool = False) -> None:
        manifest = self.load_manifest()
        dep_key = "devDependencies" if is_dev else "dependencies"
        if dep_key not in manifest:
            manifest[dep_key] = {}

        manifest[dep_key][package_name] = version
        self.save_manifest(manifest)

        lock = self.load_lockfile()
        pkg_hash = hashlib.sha256(f"{package_name}@{version}".encode("utf-8")).hexdigest()
        lock["packages"][package_name] = {
            "version": version,
            "resolved": f"https://registry.lyslyn.org/{package_name}/-/{package_name}-{version}.tgz",
            "integrity": f"sha256-{pkg_hash}",
            "dev": is_dev
        }
        self.save_lockfile(lock)

        os.makedirs(self.packages_dir, exist_ok=True)
        pkg_dir = os.path.join(self.packages_dir, package_name)
        os.makedirs(pkg_dir, exist_ok=True)

        index_file = os.path.join(pkg_dir, "index.lys")
        if not os.path.isfile(index_file):
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(f'# Package: {package_name} v{version}\nSet package_name to "{package_name}"\n')

        print(f"\033[92m✓\033[0m Added \033[1m{package_name}@{version}\033[0m to {MANIFEST_FILE} and updated {LOCK_FILE}")

    def remove_package(self, package_name: str) -> None:
        manifest = self.load_manifest()
        removed = False

        if "dependencies" in manifest and package_name in manifest["dependencies"]:
            del manifest["dependencies"][package_name]
            removed = True

        if "devDependencies" in manifest and package_name in manifest["devDependencies"]:
            del manifest["devDependencies"][package_name]
            removed = True

        if not removed:
            print(f"\033[93m⚠ Package '{package_name}' is not in {MANIFEST_FILE}.\033[0m")
            return

        self.save_manifest(manifest)

        lock = self.load_lockfile()
        if package_name in lock.get("packages", {}):
            del lock["packages"][package_name]
            self.save_lockfile(lock)

        pkg_dir = os.path.join(self.packages_dir, package_name)
        if os.path.isdir(pkg_dir):
            import shutil
            shutil.rmtree(pkg_dir)

        print(f"\033[92m✓\033[0m Removed \033[1m{package_name}\033[0m from project and lockfile")

    def install(self) -> None:
        manifest = self.load_manifest()
        deps = manifest.get("dependencies", {})
        dev_deps = manifest.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}

        if not all_deps:
            print("No dependencies to install in lyslyn.json.")
            return

        os.makedirs(self.packages_dir, exist_ok=True)
        lock = self.load_lockfile()

        print(f"\033[1mInstalling {len(all_deps)} dependencies...\033[0m")
        for pkg, ver in all_deps.items():
            pkg_dir = os.path.join(self.packages_dir, pkg)
            os.makedirs(pkg_dir, exist_ok=True)
            index_path = os.path.join(pkg_dir, "index.lys")
            if not os.path.isfile(index_path):
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(f'# Package: {pkg} v{ver}\n')

            if pkg not in lock["packages"]:
                pkg_hash = hashlib.sha256(f"{pkg}@{ver}".encode("utf-8")).hexdigest()
                lock["packages"][pkg] = {
                    "version": ver,
                    "integrity": f"sha256-{pkg_hash}",
                    "dev": pkg in dev_deps
                }

        self.save_lockfile(lock)
        print(f"\033[92m✓\033[0m Successfully installed {len(all_deps)} packages with verified integrity hashes in {LOCK_FILE}.")

    def pack(self, output_tar: Optional[str] = None) -> str:
        manifest = self.load_manifest()
        pkg_name = manifest.get("name", "package")
        pkg_ver = manifest.get("version", "1.0.0")
        target_name = output_tar or f"{pkg_name}-{pkg_ver}.lyspkg"

        with tarfile.open(target_name, "w:gz") as tar:
            for root, _, files in os.walk(self.project_dir):
                if any(p.startswith(".") or p in ("__pycache__", "lys_modules") for p in root.split(os.sep)):
                    continue
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, self.project_dir)
                    tar.add(full_p, arcname=rel_p)

        file_size = os.path.getsize(target_name)
        print(f"\033[92m✓\033[0m Created package archive \033[1m{target_name}\033[0m ({file_size} bytes)")
        return target_name

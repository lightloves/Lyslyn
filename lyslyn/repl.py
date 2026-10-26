"""Interactive REPL shell for Lyslyn."""
import sys
import os
from .lexer import Lexer
from .parser import Parser
from .interpreter import Interpreter
from .diagnostics import LyslynError


BANNER = r"""
  _               _             
 | |   _   _ ___| |_   _ _ __   
 | |  | | | / __| | | | | '_ \  
 | |__| |_| \__ \ | |_| | | | | 
 |_____\__, |___/_|\__, |_| |_|  v1.0.0
       |___/       |___/         
 Lyslyn — The English-Structured Programming Language
 Type .help for commands, .exit or Ctrl+D to exit.
"""


def start_repl() -> None:
    print(BANNER)
    interp = Interpreter(filename="<repl>")

    try:
        import readline
        histfile = os.path.expanduser("~/.lyslyn_history")
        try:
            readline.read_history_file(histfile)
        except FileNotFoundError:
            pass
        import atexit
        atexit.register(readline.write_history_file, histfile)
    except ImportError:
        pass

    buffer_lines = []

    while True:
        try:
            prompt = " ...> " if buffer_lines else "lyslyn> "
            try:
                line = input(prompt)
            except EOFError:
                print("\nGoodbye!")
                break

            stripped = line.strip()

            if not buffer_lines and stripped.startswith("."):
                cmd = stripped.lower()
                if cmd in (".exit", ".quit"):
                    print("Goodbye!")
                    break
                elif cmd == ".help":
                    print("""
Lyslyn REPL Commands:
  .help      Show this help message
  .vars      Display defined variables and constants
  .clear     Clear the terminal screen
  .exit      Exit the REPL shell
""")
                    continue
                elif cmd == ".vars":
                    print("Current Environment Variables:")
                    for k, v in interp.environment.values.items():
                        if not k.startswith("_") and k not in interp.globals.constants:
                            print(f"  {k} = {interp.stringify_val(v)}")
                    continue
                elif cmd == ".clear":
                    os.system("clear" if os.name == "posix" else "cls")
                    continue
                else:
                    print(f"Unknown command '{cmd}'. Type .help for commands.")
                    continue

            buffer_lines.append(line)

            if line.rstrip().endswith(":"):
                continue

            if len(buffer_lines) > 1 and stripped != "":
                continue

            source = "\n".join(buffer_lines)
            buffer_lines = []

            if not source.strip():
                continue

            lexer = Lexer(source, filename="<repl>")
            tokens = lexer.tokenize()
            parser = Parser(tokens, filename="<repl>", source=source)
            program = parser.parse()

            result = None
            for stmt in program.statements:
                result = interp.execute(stmt)

            from .ast_nodes import ExprStmt
            if program.statements and isinstance(program.statements[-1], ExprStmt) and result is not None:
                print(f"=> {interp.stringify_val(result)}")

        except KeyboardInterrupt:
            buffer_lines = []
            print("\nKeyboardInterrupt")
        except LyslynError as e:
            buffer_lines = []
            print(e.format_diagnostic(color=True))
        except Exception as e:
            buffer_lines = []
            print(f"\033[91mError\033[0m: {e}")

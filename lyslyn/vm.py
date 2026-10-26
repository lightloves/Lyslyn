"""Stack-based Virtual Machine for executing Lyslyn bytecode."""
import sys
from typing import Any, Dict, List, Optional
from .opcodes import OpCode
from .chunk import Chunk
from .builtins import get_global_builtins
from .values import LyslynBuiltin


class CallFrame:
    def __init__(self, chunk: Chunk, ip: int = 0, slots_offset: int = 0):
        self.chunk = chunk
        self.ip = ip
        self.slots_offset = slots_offset


class VM:
    def __init__(self, script_args: Optional[List[str]] = None):
        self.stack: List[Any] = []
        self.frames: List[CallFrame] = []
        self.globals: Dict[str, Any] = {}

        for name, fn in get_global_builtins().items():
            self.globals[name] = fn
        self.globals["args"] = script_args or []

    def run(self, chunk: Chunk) -> Any:
        self.stack = []
        self.frames = [CallFrame(chunk, ip=0, slots_offset=0)]

        frame = self.frames[-1]

        while True:
            instruction = frame.chunk.code[frame.ip]
            frame.ip += 1

            if instruction == OpCode.OP_CONSTANT:
                const_idx = frame.chunk.code[frame.ip]
                frame.ip += 1
                self.stack.append(frame.chunk.constants[const_idx])

            elif instruction == OpCode.OP_NIL:
                self.stack.append(None)

            elif instruction == OpCode.OP_TRUE:
                self.stack.append(True)

            elif instruction == OpCode.OP_FALSE:
                self.stack.append(False)

            elif instruction == OpCode.OP_POP:
                if self.stack:
                    self.stack.pop()

            elif instruction == OpCode.OP_DUP:
                self.stack.append(self.stack[-1])

            elif instruction == OpCode.OP_DEF_GLOBAL:
                const_idx = frame.chunk.code[frame.ip]
                frame.ip += 1
                name = frame.chunk.constants[const_idx]
                val = self.stack.pop()
                self.globals[name] = val

            elif instruction == OpCode.OP_GET_GLOBAL:
                const_idx = frame.chunk.code[frame.ip]
                frame.ip += 1
                name = frame.chunk.constants[const_idx]
                if name in self.globals:
                    self.stack.append(self.globals[name])
                else:
                    raise NameError(f"Undefined global variable '{name}'")

            elif instruction == OpCode.OP_SET_GLOBAL:
                const_idx = frame.chunk.code[frame.ip]
                frame.ip += 1
                name = frame.chunk.constants[const_idx]
                self.globals[name] = self.stack[-1]

            elif instruction == OpCode.OP_GET_LOCAL:
                slot = frame.chunk.code[frame.ip]
                frame.ip += 1
                self.stack.append(self.stack[frame.slots_offset + slot])

            elif instruction == OpCode.OP_SET_LOCAL:
                slot = frame.chunk.code[frame.ip]
                frame.ip += 1
                self.stack[frame.slots_offset + slot] = self.stack[-1]

            elif instruction == OpCode.OP_ADD:
                b = self.stack.pop()
                a = self.stack.pop()
                if isinstance(a, str) or isinstance(b, str):
                    self.stack.append(str(a) + str(b))
                elif isinstance(a, list) and isinstance(b, list):
                    self.stack.append(a + b)
                else:
                    self.stack.append(a + b)

            elif instruction == OpCode.OP_SUB:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)

            elif instruction == OpCode.OP_MUL:
                b = self.stack.pop()
                a = self.stack.pop()
                if isinstance(a, str) and isinstance(b, int):
                    self.stack.append(a * b)
                else:
                    self.stack.append(a * b)

            elif instruction == OpCode.OP_DIV:
                b = self.stack.pop()
                a = self.stack.pop()
                if b == 0:
                    raise ZeroDivisionError("Division by zero in VM")
                res = a / b
                if isinstance(res, float) and res.is_integer() and isinstance(a, int) and isinstance(b, int):
                    res = int(res)
                self.stack.append(res)

            elif instruction == OpCode.OP_MOD:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a % b)

            elif instruction == OpCode.OP_NEG:
                self.stack[-1] = -self.stack[-1]

            elif instruction == OpCode.OP_EQUAL:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a == b)

            elif instruction == OpCode.OP_GREATER:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a > b)

            elif instruction == OpCode.OP_LESS:
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a < b)

            elif instruction == OpCode.OP_NOT:
                val = self.stack.pop()
                self.stack.append(not bool(val))

            elif instruction == OpCode.OP_JUMP:
                offset = (frame.chunk.code[frame.ip] << 8) | frame.chunk.code[frame.ip + 1]
                frame.ip += 2 + offset

            elif instruction == OpCode.OP_JUMP_IF_FALSE:
                offset = (frame.chunk.code[frame.ip] << 8) | frame.chunk.code[frame.ip + 1]
                frame.ip += 2
                if not bool(self.stack[-1]):
                    frame.ip += offset

            elif instruction == OpCode.OP_LOOP:
                offset = (frame.chunk.code[frame.ip] << 8) | frame.chunk.code[frame.ip + 1]
                frame.ip += 2 - offset

            elif instruction == OpCode.OP_BUILD_LIST:
                count = frame.chunk.code[frame.ip]
                frame.ip += 1
                items = [self.stack.pop() for _ in range(count)]
                items.reverse()
                self.stack.append(items)

            elif instruction == OpCode.OP_BUILD_MAP:
                count = frame.chunk.code[frame.ip]
                frame.ip += 1
                entries = {}
                for _ in range(count):
                    v = self.stack.pop()
                    k = self.stack.pop()
                    entries[str(k)] = v
                self.stack.append(entries)

            elif instruction == OpCode.OP_INDEX_GET:
                idx = self.stack.pop()
                target = self.stack.pop()
                if isinstance(target, (list, tuple, str)):
                    if idx == "length":
                        self.stack.append(len(target))
                    else:
                        self.stack.append(target[int(idx)])
                elif isinstance(target, dict):
                    self.stack.append(target.get(str(idx), None))
                else:
                    self.stack.append(getattr(target, str(idx), None))

            elif instruction == OpCode.OP_INDEX_SET:
                val = self.stack.pop()
                idx = self.stack.pop()
                target = self.stack.pop()
                if isinstance(target, list):
                    target[int(idx)] = val
                elif isinstance(target, dict):
                    target[str(idx)] = val
                else:
                    setattr(target, str(idx), val)
                self.stack.append(val)

            elif instruction == OpCode.OP_PRINT:
                count = frame.chunk.code[frame.ip]
                frame.ip += 1
                args = [str(self.stack.pop()) for _ in range(count)]
                args.reverse()
                print(*args)
                self.stack.append(None)

            elif instruction == OpCode.OP_CALL:
                arg_count = frame.chunk.code[frame.ip]
                frame.ip += 1

                args = [self.stack.pop() for _ in range(arg_count)]
                args.reverse()

                callee = self.stack.pop()

                if isinstance(callee, LyslynBuiltin):
                    res = callee.call(args)
                    self.stack.append(res)
                elif callable(callee):
                    res = callee(*args)
                    self.stack.append(res)
                elif isinstance(callee, dict) and callee.get("type") == "function":
                    fn_chunk = Chunk.deserialize(bytes.fromhex(callee["chunk"]))
                    slots_offset = len(self.stack)
                    for a in args:
                        self.stack.append(a)
                    new_frame = CallFrame(fn_chunk, ip=0, slots_offset=slots_offset)
                    self.frames.append(new_frame)
                    frame = self.frames[-1]
                else:
                    raise TypeError(f"Cannot call non-callable object {type(callee).__name__}")

            elif instruction == OpCode.OP_RETURN:
                ret_val = self.stack.pop()
                finished_frame = self.frames.pop()

                while len(self.stack) > finished_frame.slots_offset:
                    self.stack.pop()

                self.stack.append(ret_val)

                if not self.frames:
                    return ret_val
                frame = self.frames[-1]

            elif instruction == OpCode.OP_HALT:
                if self.stack:
                    return self.stack[-1]
                return None

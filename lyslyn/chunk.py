"""Bytecode Chunk and Disassembler for Lyslyn VM."""
import json
import struct
from typing import Any, List, Tuple, Optional
from .opcodes import OpCode

MAGIC_HEADER = b"LYSC\x01\x00"


class Chunk:
    def __init__(self, name: str = "<main>"):
        self.name = name
        self.code: List[int] = []
        self.constants: List[Any] = []
        self.lines: List[int] = []

    def write(self, byte_val: int, line: int) -> int:
        offset = len(self.code)
        self.code.append(int(byte_val))
        self.lines.append(int(line))
        return offset

    def add_constant(self, value: Any) -> int:
        for idx, const in enumerate(self.constants):
            if const == value and type(const) is type(value):
                return idx
        self.constants.append(value)
        return len(self.constants) - 1

    def disassemble(self, title: Optional[str] = None) -> str:
        header = f"=== Bytecode Disassembly: {title or self.name} ==="
        out = [header]
        offset = 0
        while offset < len(self.code):
            offset, line_str = self.disassemble_instruction(offset)
            out.append(line_str)
        out.append("=" * len(header))
        return "\n".join(out)

    def disassemble_instruction(self, offset: int) -> Tuple[int, str]:
        line = self.lines[offset]
        line_str = f"{line:4d} | " if offset == 0 or self.lines[offset] != self.lines[offset - 1] else "     | "
        opcode_num = self.code[offset]

        try:
            opcode = OpCode(opcode_num)
            op_name = opcode.name
        except ValueError:
            return offset + 1, f"{offset:04d}  {line_str}UNKNOWN_OPCODE({opcode_num})"

        if opcode in (
            OpCode.OP_CONSTANT, OpCode.OP_DEF_GLOBAL,
            OpCode.OP_GET_GLOBAL, OpCode.OP_SET_GLOBAL
        ):
            const_idx = self.code[offset + 1]
            const_val = self.constants[const_idx] if const_idx < len(self.constants) else "?"
            val_repr = repr(const_val)
            if len(val_repr) > 30:
                val_repr = val_repr[:27] + "..."
            return offset + 2, f"{offset:04d}  {line_str}{op_name:<18} #{const_idx:<3} ({val_repr})"

        if opcode in (
            OpCode.OP_GET_LOCAL, OpCode.OP_SET_LOCAL,
            OpCode.OP_GET_UPVALUE, OpCode.OP_SET_UPVALUE,
            OpCode.OP_CALL, OpCode.OP_PRINT,
            OpCode.OP_BUILD_LIST, OpCode.OP_BUILD_MAP
        ):
            slot = self.code[offset + 1]
            return offset + 2, f"{offset:04d}  {line_str}{op_name:<18} {slot}"

        if opcode in (OpCode.OP_JUMP, OpCode.OP_JUMP_IF_FALSE, OpCode.OP_LOOP):
            jump_offset = (self.code[offset + 1] << 8) | self.code[offset + 2]
            target = offset + 3 - jump_offset if opcode == OpCode.OP_LOOP else offset + 3 + jump_offset
            return offset + 3, f"{offset:04d}  {line_str}{op_name:<18} -> {target:04d}"

        return offset + 1, f"{offset:04d}  {line_str}{op_name}"

    def serialize(self) -> bytes:
        """Serialize chunk to binary format (.lysc)."""
        data = bytearray(MAGIC_HEADER)
        meta = {
            "name": self.name,
            "constants": self.constants
        }
        meta_bytes = json.dumps(meta).encode("utf-8")
        data.extend(struct.pack(">I", len(meta_bytes)))
        data.extend(meta_bytes)

        data.extend(struct.pack(">I", len(self.code)))
        data.extend(bytes(self.code))

        data.extend(struct.pack(">I", len(self.lines)))
        for line in self.lines:
            data.extend(struct.pack(">H", min(65535, line)))

        return bytes(data)

    @classmethod
    def deserialize(cls, data: bytes) -> "Chunk":
        """Deserialize chunk from binary format."""
        if not data.startswith(MAGIC_HEADER):
            raise ValueError("Invalid Lyslyn compiled bytecode file: bad magic header")

        offset = len(MAGIC_HEADER)
        meta_len = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4

        meta_bytes = data[offset:offset + meta_len]
        offset += meta_len
        meta = json.loads(meta_bytes.decode("utf-8"))

        chunk = cls(name=meta.get("name", "<main>"))
        chunk.constants = meta.get("constants", [])

        code_len = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        chunk.code = list(data[offset:offset + code_len])
        offset += code_len

        lines_len = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        for _ in range(lines_len):
            chunk.lines.append(struct.unpack(">H", data[offset:offset + 2])[0])
            offset += 2

        return chunk

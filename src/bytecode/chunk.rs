use crate::bytecode::opcodes::OpCode;
use crate::values::Value;

#[derive(Clone)]
pub struct Chunk {
    pub name: String,
    pub code: Vec<u8>,
    pub constants: Vec<Value>,
    pub lines: Vec<usize>,
}

impl Chunk {
    pub fn new(name: impl Into<String>) -> Self {
        Chunk {
            name: name.into(),
            code: Vec::new(),
            constants: Vec::new(),
            lines: Vec::new(),
        }
    }

    pub fn write_byte(&mut self, byte: u8, line: usize) -> usize {
        let offset = self.code.len();
        self.code.push(byte);
        self.lines.push(line);
        offset
    }

    pub fn write_opcode(&mut self, op: OpCode, line: usize) -> usize {
        self.write_byte(op as u8, line)
    }

    pub fn write_u16(&mut self, val: u16, line: usize) {
        self.write_byte((val >> 8) as u8, line);
        self.write_byte((val & 0xff) as u8, line);
    }

    pub fn add_constant(&mut self, value: Value) -> u16 {
        for (i, c) in self.constants.iter().enumerate() {
            if c == &value {
                return i as u16;
            }
        }
        self.constants.push(value);
        (self.constants.len() - 1) as u16
    }

    pub fn disassemble(&self, title: Option<&str>) -> String {
        let mut out = String::new();
        let title_str = title.unwrap_or(&self.name);
        out.push_str(&format!("=== Disassembly: {} ===\n", title_str));

        let mut offset = 0;
        while offset < self.code.len() {
            let (next_offset, line_str) = self.disassemble_instruction(offset);
            out.push_str(&line_str);
            out.push('\n');
            offset = next_offset;
        }

        out.push_str("=============================\n");
        out
    }

    pub fn disassemble_instruction(&self, offset: usize) -> (usize, String) {
        let line = self.lines[offset];
        let line_prefix = if offset == 0 || self.lines[offset] != self.lines[offset - 1] {
            format!("{:4} | ", line)
        } else {
            "     | ".to_string()
        };

        let byte = self.code[offset];
        if let Some(op) = OpCode::from_u8(byte) {
            match op {
                OpCode::Constant => {
                    if offset + 2 < self.code.len() {
                        let idx = ((self.code[offset + 1] as u16) << 8) | (self.code[offset + 2] as u16);
                        let val_str = if (idx as usize) < self.constants.len() {
                            format!("{}", self.constants[idx as usize])
                        } else {
                            "<unknown>".to_string()
                        };
                        let s = format!("{:04} {}{:16} {:4} ('{}')", offset, line_prefix, "CONSTANT", idx, val_str);
                        return (offset + 3, s);
                    }
                }
                OpCode::DefGlobal | OpCode::GetGlobal | OpCode::SetGlobal | OpCode::GetModule => {
                    if offset + 2 < self.code.len() {
                        let idx = ((self.code[offset + 1] as u16) << 8) | (self.code[offset + 2] as u16);
                        let val_str = if (idx as usize) < self.constants.len() {
                            format!("{}", self.constants[idx as usize])
                        } else {
                            "<unknown>".to_string()
                        };
                        let s = format!("{:04} {}{:16} {:4} ('{}')", offset, line_prefix, format!("{:?}", op), idx, val_str);
                        return (offset + 3, s);
                    }
                }
                OpCode::GetLocal | OpCode::SetLocal | OpCode::GetUpvalue | OpCode::SetUpvalue => {
                    if offset + 2 < self.code.len() {
                        let slot = ((self.code[offset + 1] as u16) << 8) | (self.code[offset + 2] as u16);
                        let s = format!("{:04} {}{:16} slot:{}", offset, line_prefix, format!("{:?}", op), slot);
                        return (offset + 3, s);
                    }
                }
                OpCode::Jump | OpCode::JumpIfFalse | OpCode::Loop => {
                    if offset + 2 < self.code.len() {
                        let jmp = ((self.code[offset + 1] as u16) << 8) | (self.code[offset + 2] as u16);
                        let target = if op == OpCode::Loop {
                            offset.saturating_add(3).saturating_sub(jmp as usize)
                        } else {
                            offset + 3 + (jmp as usize)
                        };
                        let s = format!("{:04} {}{:16} -> {:04}", offset, line_prefix, format!("{:?}", op), target);
                        return (offset + 3, s);
                    }
                }
                OpCode::Call => {
                    if offset + 1 < self.code.len() {
                        let arity = self.code[offset + 1];
                        let s = format!("{:04} {}{:16} args:{}", offset, line_prefix, "CALL", arity);
                        return (offset + 2, s);
                    }
                }
                _ => {
                    let s = format!("{:04} {}{:?}", offset, line_prefix, op);
                    return (offset + 1, s);
                }
            }
        }

        let op_str = format!("{:04} {}{:#04x}", offset, line_prefix, byte);
        (offset + 1, op_str)
    }
}

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
        let op_str = format!("{:04} {}{:?}", offset, line_prefix, byte);
        (offset + 1, op_str)
    }
}

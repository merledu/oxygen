import re

# RISC-V Instruction formats and opcodes based on the provided PDF
INSTRUCTION_SET = {
    'R': {
        'opcodes': {'ADD': '0110011', 'SUB': '0110011', 'SLL': '0110011', 'SRL': '0110011', 'SRA': '0110011'},
        'funct3': {'ADD': '000', 'SUB': '000', 'SLL': '001', 'SRL': '101', 'SRA': '101'},
        'funct7': {'ADD': '0000000', 'SUB': '0100000', 'SLL': '0000000', 'SRL': '0000000', 'SRA': '0100000'}
    },
    'I': {
        'opcodes': {'ADDI': '0010011', 'SLLI': '0010011', 'SRLI': '0010011', 'SRAI': '0010011'},
        'funct3': {'ADDI': '000', 'SLLI': '001', 'SRLI': '101', 'SRAI': '101'},
        'funct7': {'SLLI': '0000000', 'SRLI': '0000000', 'SRAI': '0100000'}
    },
    'S': {
        'opcodes': {'SB': '0100011', 'SH': '0100011', 'SW': '0100011'},
        'funct3': {'SB': '000', 'SH': '001', 'SW': '010'}
    },
    'B': {
        'opcodes': {'BEQ': '1100011', 'BNE': '1100011', 'BLT': '1100011', 'BGE': '1100011', 'BLTU': '1100011', 'BGEU': '1100011'},
        'funct3': {'BEQ': '000', 'BNE': '001', 'BLT': '100', 'BGE': '101', 'BLTU': '110', 'BGEU': '111'}
    },
    'U': {
        'opcodes': {'LUI': '0110111', 'AUIPC': '0010111'}
    },
    'J': {
        'opcodes': {'JAL': '1101111'}
    }
}

# Registers mapping
REGISTER_MAP = {
    'x0': '00000', 'x1': '00001', 'x2': '00010', 'x3': '00011', 'x4': '00100',
    'x5': '00101', 'x6': '00110', 'x7': '00111', 'x8': '01000', 'x9': '01001',
    'x10': '01010', 'x11': '01011', 'x12': '01100', 'x13': '01101', 'x14': '01110',
    'x15': '01111', 'x16': '10000', 'x17': '10001', 'x18': '10010', 'x19': '10011',
    'x20': '10100', 'x21': '10101', 'x22': '10110', 'x23': '10111', 'x24': '11000',
    'x25': '11001', 'x26': '11010', 'x27': '11011', 'x28': '11100', 'x29': '11101',
    'x30': '11110', 'x31': '11111'
}

# Helper function to convert binary string to hex
def bin_to_hex(binary_str):
    return hex(int(binary_str, 2))[2:].zfill(8)

# Function to encode R-type instruction
def encode_r_type(instruction, rd, rs1, rs2):
    opcode = INSTRUCTION_SET['R']['opcodes'][instruction]
    funct3 = INSTRUCTION_SET['R']['funct3'][instruction]
    funct7 = INSTRUCTION_SET['R']['funct7'][instruction]
    rd_bin = REGISTER_MAP[rd]
    rs1_bin = REGISTER_MAP[rs1]
    rs2_bin = REGISTER_MAP[rs2]
    binary_str = f"{funct7}{rs2_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"
    return bin_to_hex(binary_str)

# Function to encode I-type instruction
def encode_i_type(instruction, rd, rs1, imm):
    opcode = INSTRUCTION_SET['I']['opcodes'][instruction]
    funct3 = INSTRUCTION_SET['I']['funct3'][instruction]
    rd_bin = REGISTER_MAP[rd]
    rs1_bin = REGISTER_MAP[rs1]
    imm_bin = format(int(imm), '012b')
    binary_str = f"{imm_bin}{rs1_bin}{funct3}{rd_bin}{opcode}"
    return bin_to_hex(binary_str)

# Function to encode S-type instruction
def encode_s_type(instruction, rs1, rs2, imm):
    opcode = INSTRUCTION_SET['S']['opcodes'][instruction]
    funct3 = INSTRUCTION_SET['S']['funct3'][instruction]
    rs1_bin = REGISTER_MAP[rs1]
    rs2_bin = REGISTER_MAP[rs2]
    imm_bin = format(int(imm), '012b')
    imm11_5 = imm_bin[:7]
    imm4_0 = imm_bin[7:]
    binary_str = f"{imm11_5}{rs2_bin}{rs1_bin}{funct3}{imm4_0}{opcode}"
    return bin_to_hex(binary_str)

# Function to encode B-type instruction
def encode_b_type(instruction, rs1, rs2, imm):
    opcode = INSTRUCTION_SET['B']['opcodes'][instruction]
    funct3 = INSTRUCTION_SET['B']['funct3'][instruction]
    rs1_bin = REGISTER_MAP[rs1]
    rs2_bin = REGISTER_MAP[rs2]
    imm_bin = format(int(imm), '013b')
    imm_bin2 = ''.join(reversed(str(imm_bin)))
    imm12 = imm_bin2[12]
    imm10_5 = imm_bin2[5:11]
    imm4_1 = imm_bin2[1:5]
    imm11 = imm_bin2[11]
    binary_str = f"{imm12}{imm10_5}{rs2_bin}{rs1_bin}{funct3}{imm4_1}{imm11}{opcode}"
    print(binary_str)
    return bin_to_hex(binary_str)

# Function to encode U-type instruction
def encode_u_type(instruction, rd, imm):
    opcode = INSTRUCTION_SET['U']['opcodes'][instruction]
    rd_bin = REGISTER_MAP[rd]
    imm_bin = format(int(imm), '020b')
    binary_str = f"{imm_bin}{rd_bin}{opcode}"
    return bin_to_hex(binary_str)

# Function to encode J-type instruction
def encode_j_type(instruction, rd, imm):
    opcode = INSTRUCTION_SET['J']['opcodes'][instruction]
    rd_bin = REGISTER_MAP[rd]
    imm_bin = format(int(imm), '021b')
    imm20 = imm_bin[0]
    imm10_1 = imm_bin[1:11]
    imm11 = imm_bin[11]
    imm19_12 = imm_bin[12:20]
    binary_str = f"{imm20}{imm19_12}{imm11}{imm10_1}{rd_bin}{opcode}"
    return bin_to_hex(binary_str)

def handle_pseudo_instruction(pseudo_instruction):
    # Handle common pseudo-instructions
    if pseudo_instruction.startswith('li'):
        # li rd, imm -> addi rd, x0, imm
        match = re.match(r'li\s+(\w+),\s*(-?\d+)', pseudo_instruction)
        if match:
            rd = int(match.group(1)[1:])  # Strip 'x' from register name
            imm = int(match.group(2))
            return f"addi x{rd}, x0, {imm}"
    elif pseudo_instruction.startswith('mv'):
        # mv rd, rs -> addi rd, rs, 0
        match = re.match(r'mv\s+(\w+),\s+(\w+)', pseudo_instruction)
        if match:
            rd = int(match.group(1)[1:])  # Strip 'x' from register name
            rs = int(match.group(2)[1:])
            return f"addi x{rd}, x{rs}, 0"
    elif pseudo_instruction.startswith('j'):
        # j label -> jal x0, label
        match = re.match(r'j\s+(\w+)', pseudo_instruction)
        if match:
            label = match.group(1)
            return f"jal x0, {label}"
    elif pseudo_instruction.startswith('jr'):
        # jr rs -> jalr x0, rs, 0
        match = re.match(r'jr\s+(\w+)', pseudo_instruction)
        if match:
            rs = int(match.group(1)[1:])  # Strip 'x' from register name
            return f"jalr x0, x{rs}, 0"
    elif pseudo_instruction.startswith('ret'):
        # ret -> jalr x0, x1, 0
        return "jalr x0, x1, 0"
    elif pseudo_instruction.startswith('nop'):
        # nop -> addi x0, x0, 0
        return "addi x0, x0, 0"
    elif pseudo_instruction.startswith('la'):
        # la rd, symbol -> auipc rd, symbol[31:12] + addi rd, rd, symbol[11:0]
        match = re.match(r'la\s+(\w+),\s+(\w+)', pseudo_instruction)
        if match:
            rd = int(match.group(1)[1:])  # Strip 'x' from register name
            symbol = match.group(2)
            # This requires symbol resolution, which is complex; placeholder
            return f"auipc x{rd}, {symbol}[31:12] + addi x{rd}, x{rd}, {symbol}[11:0]"
    
    return pseudo_instruction

# Main function to convert instructions to hex
def convert_instructions_to_hex(file_path):
    with open('riscv_instructions.txt', 'r') as file:
        lines = file.readlines()
        print(lines)
    
    hex_instructions = []
    for line in lines:
        parts = re.split(r',\s*|\s+', line.strip())
        instruction = parts[0].upper()
        
        if instruction in INSTRUCTION_SET['R']['opcodes']:
            rd, rs1, rs2 = parts[1], parts[2], parts[3]
            hex_value = encode_r_type(instruction, rd, rs1, rs2)
        elif instruction in INSTRUCTION_SET['I']['opcodes']:
            rd, rs1, imm = parts[1], parts[2], parts[3]
            hex_value = encode_i_type(instruction, rd, rs1, imm)
        elif instruction in INSTRUCTION_SET['S']['opcodes']:
            rs1, rs2, imm = parts[1], parts[2], parts[3]
            hex_value = encode_s_type(instruction, rs1, rs2, imm)
        elif instruction in INSTRUCTION_SET['B']['opcodes']:
            rs1, rs2, imm = parts[1], parts[2], parts[3]
            hex_value = encode_b_type(instruction, rs1, rs2, imm)
        elif instruction in INSTRUCTION_SET['U']['opcodes']:
            rd, imm = parts[1], parts[2]
            hex_value = encode_u_type(instruction, rd, imm)
        elif instruction in INSTRUCTION_SET['J']['opcodes']:
            rd, imm = parts[1], parts[2]
            hex_value = encode_j_type(instruction, rd, imm)
        else:
            raise ValueError(f"Unknown instruction: {instruction}")

        hex_instructions.append(hex_value)
    
    return hex_instructions

# Example usage
file_path = '/home/merl/Desktop/interprator/riscv_instructions.txt'  # Text file containing RISC-V instructions
hex_values = convert_instructions_to_hex(file_path)
print(hex_values)
for hex_value in hex_values:
    print(hex_value)
    
import re

# Define the formats for each type of instruction
FORMATS = {
    'R': '{funct7:07}{rs2:05}{rs1:05}{funct3:03}{rd:05}{opcode:07}',
    'I': '{imm:012}{rs1:05}{funct3:03}{rd:05}{opcode:07}',
    'S': '{imm_11_5:07}{rs2:05}{rs1:05}{funct3:03}{imm_4_0:05}{opcode:07}',
    'B': '{imm_12}{imm_10_5:06}{rs2:05}{rs1:05}{funct3:03}{imm_4_1:04}{imm_11}{opcode:07}',
    'U': '{imm:020}{rd:05}{opcode:07}',
    'J': '{imm_20}{imm_10_1:010}{imm_11}{imm_19_12:08}{rd:05}{opcode:07}',
}

# Define the opcode, funct3, and funct7 for each instruction
INSTRUCTION_SET = {
    'add':  ('0110011', '000', '0000000', 'R'),
    'sub':  ('0110011', '000', '0100000', 'R'),
    'xor':  ('0110011', '100', '0000000', 'R'),
    'or':   ('0110011', '110', '0000000', 'R'),
    'and':  ('0110011', '111', '0000000', 'R'),
    'sll':  ('0110011', '001', '0000000', 'R'),
    'srl':  ('0110011', '101', '0000000', 'R'),
    'sra':  ('0110011', '101', '0100000', 'R'),
    'addi': ('0010011', '000', None, 'I'),
    'xori': ('0010011', '100', None, 'I'),
    'ori':  ('0010011', '110', None, 'I'),
    'andi': ('0010011', '111', None, 'I'),
    'lb':   ('0000011', '000', None, 'LI'),
    'lh':   ('0000011', '001', None, 'LI'),
    'lw':   ('0000011', '010', None, 'LI'),
    'lbu':  ('0000011', '100', None, 'LI'),
    'lhu':  ('0000011', '101', None, 'LI'),
    'sb':   ('0100011', '000', None, 'S'),
    'sh':   ('0100011', '001', None, 'S'),
    'sw':   ('0100011', '010', None, 'S'),
    'beq':  ('1100011', '000', None, 'B'),
    'bne':  ('1100011', '001', None, 'B'),
    'blt':  ('1100011', '100', None, 'B'),
    'bge':  ('1100011', '101', None, 'B'),
    'bltu': ('1100011', '110', None, 'B'),
    'bgeu': ('1100011', '111', None, 'B'),
    'jal':  ('1101111', None, None, 'J'),
    'jalr': ('1100111', '000', None, 'I'),
    'lui':  ('0110111', None, None, 'U'),
    'auipc':('0010111', None, None, 'U'),
    'ecall':('1110011', '000', '0000000', 'I'),
    'ebreak':('1110011', '000', '0000001', 'I'),
}

PSEUDO_INSTRUCTION_SET = {
    'nop': 'addi x0,x0,0',
    'li': 'addi {rd},x0,{imm}',
    'mv': 'addi {rd},{rs},0',
    # 'seqz': 'sltiu {rd}, {rs}, 1',
    # 'snez': 'sltu {rd}, x0, {rs}',
    # 'slz': 'slt {rd}, {rs}, x0',
    # 'sgtz': 'slt {rd}, x0, {rs}',
    'beqz': 'beq {rs},x0,{offset}',
    'bnez': 'bne {rs},x0, {offset}',
    'blez': 'bge {rs},x0,{offset}',
    'bgez': 'blt {rs},x0,{offset}',
    'bltz': 'blt {rs},x0,{offset}',
    'bgtz': 'blt x0,{rs},{offset}',
    'j': 'jal x0,{a}',
    'jr': 'jalr x0,{a},0',
    'ret': 'jalr x0,x1,0'
}

def register_to_bin(register):
    """Convert register name to binary representation"""
    if register.startswith('x'):
        x = int(register[1:])
        x = '{0:05b}'.format(x)
        
        return x
        # return int(register[1:])
    raise ValueError(f"Unknown register: {register}")

def imm_to_bin(imm, length):
    """Convert immediate value to binary representation of given length"""
    value = int(imm)
    if value < 0:
        value = (1 << length) + value
    return format(value, f'0{length}b')


def parse_instruction(instruction):
    
    """Parse the instruction into its binary components"""
    parts = re.split(r'\s|,', instruction.strip())
    inst_name = parts[0]
    print(parts)
    print (inst_name)
    if inst_name in PSEUDO_INSTRUCTION_SET:
        base_inst = PSEUDO_INSTRUCTION_SET[inst_name]
        # print(base_inst)
        # print(inst_name[0])
        
        if (inst_name == 'nop'):
            return parse_instruction(base_inst)
        elif(inst_name[0] == 'b'):
            return parse_instruction(base_inst.format(rs=parts[1], offset=parts[2]))
        elif(inst_name[0] == 'j'):
            return parse_instruction(base_inst.format(a=parts[1]))
        elif(inst_name == 'ret'):
            return parse_instruction(base_inst)
        elif (inst_name == 'li'):
            return parse_instruction(base_inst.format(rd=parts[1], imm=parts[2]))
        elif (inst_name == 'mv'):
            return parse_instruction(base_inst.format(rd=parts[1], rs=parts[2]))
    
    print(inst_name)
    opcode, funct3, funct7, inst_type = INSTRUCTION_SET[inst_name]
    print(funct7)
    if inst_type == 'R':
        rd = register_to_bin(parts[1])
        rs1 = register_to_bin(parts[2])
        rs2 = register_to_bin(parts[3])
        return FORMATS['R'].format(funct7=funct7, rs2=rs2, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)
    
    elif inst_type == 'I':
        # print(parts)
        rd = register_to_bin(parts[1])
        # print(parts[2])
        rs1 = register_to_bin(parts[2])
        imm = imm_to_bin(parts[3], 12)
        # return '{imm:012}{rs1:05}{funct3:03}{rd:05}{opcode:07}'.format(imm=imm, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)
        # print (FORMATS['I'].format(imm=imm, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode))
        return FORMATS['I'].format(imm=imm, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)
    
    
    elif inst_type == 'S':
        rs1 = register_to_bin(parts[1])
        rs2 = register_to_bin(parts[2])
        imm = imm_to_bin(parts[3], 12)
        imm_11_5 = imm[:7]
        imm_4_0 = imm[7:]
        return FORMATS['S'].format(imm_11_5=imm_11_5, rs2=rs2, rs1=rs1, funct3=funct3, imm_4_0=imm_4_0, opcode=opcode)
    
    elif inst_type == 'B':
        rs1 = register_to_bin(parts[1])
        rs2 = register_to_bin(parts[2])
        
        # imm_bin = format(int(imm), '013b')
        # imm_bin2 = ''.join(reversed(str(imm_bin)))
        # imm12 = imm_bin2[12]
        # imm10_5 = imm_bin2[5:11]
        # imm4_1 = imm_bin2[1:5]
        # imm11 = imm_bin2[11]
        # binary_str = f"{imm12}{imm10_5}{rs2_bin}{rs1_bin}{funct3}{imm4_1}{imm11}{opcode}"
        
        
        imm = imm_to_bin(parts[3], 13)
        
        
        # imm_bin2 = ''.join(reversed(str(imm_bin)))
        # imm_12 = imm_bin2[12]
        # imm_10_5 = imm_bin2[5:11]
        # imm_4_1 = imm_bin2[1:5]
        # imm_11 = imm_bin2[11]
        imm_12 = imm[0]
        imm_10_5 = imm[2:8]
        imm_4_1 = imm[8:12]
        imm_11 = imm[1]
        print (FORMATS['B'].format(imm_12=imm_12, imm_10_5=imm_10_5, rs2=rs2, rs1=rs1, funct3=funct3, imm_4_1=imm_4_1, imm_11=imm_11, opcode=opcode))
        return FORMATS['B'].format(imm_12=imm_12, imm_10_5=imm_10_5, rs2=rs2, rs1=rs1, funct3=funct3, imm_4_1=imm_4_1, imm_11=imm_11, opcode=opcode)
    
    elif inst_type == 'U':
        rd = register_to_bin(parts[1])
        imm = imm_to_bin(parts[2], 20)
        return FORMATS['U'].format(imm=imm, rd=rd, opcode=opcode)
    
    elif inst_type == 'J':
        rd = register_to_bin(parts[1])
        # print("rd : " ,rd)
        # print("imm no bin " ,parts[2])
        imm = imm_to_bin(parts[2], 21)
        print(imm)
        # imm = ''.join(reversed(str(imm)))
        imm_20 = imm[0]
        imm_10_1 = imm[10:20]
        # print("imm 10_1 :",imm_10_1)
        imm_11 = imm[9]
        imm_19_12 = imm[1:9]
        # print("bin imm " ,imm)
        
        # print("imm broken : ",imm_20,imm_10_1,imm_11,imm_19_12,rd,opcode, end=" ")
        return FORMATS['J'].format(imm_20=imm_20, imm_10_1=imm_10_1, imm_11=imm_11, imm_19_12=imm_19_12, rd=rd, opcode=opcode)
    elif inst_type == 'LI':
        rd = register_to_bin(parts[1])
        rs1 = register_to_bin(parts[3])
        imm = imm_to_bin(parts[2],12)
        return FORMATS['I'].format(imm=imm, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)
        

def convert_to_hex(bin_str):
    """Convert binary string to hexadecimal"""
    # print(bin_str)
    hex_str = hex(int(bin_str, 2))[2:].zfill(8)
    return hex_str

def main(instructions_str):
    # Split the input string into individual instructions
    instructions = instructions_str.splitlines()
    
    # Process each instruction and convert it to hex
    hex_lines = []
    for instruction in instructions:
        bin_str = parse_instruction(instruction)
        hex_str = convert_to_hex(bin_str)
        hex_lines.append(hex_str)
    
    # Join the hex strings with newline characters
    hex_output = '\n'.join(hex_lines)
    
    return hex_output

# def main(input_file, output_file):
#     with open(input_file, 'r') as file:
#         instructions = file.readlines()
    
#     with open(output_file, 'w') as file:
#         for instruction in instructions:
#             bin_str = parse_instruction(instruction)
#             hex_str = convert_to_hex(bin_str)
#             file.write(hex_str + '\n')

if __name__ == '__main__':
    # Example input string
    instructions_str = "add x1,x2,x3"
    hex_output = main(instructions_str)
    print(hex_output)

# if __name__ == '__main__':
#     input_file = 'instructions.txt'
#     output_file = 'instructions_hex.txt'
#     main(input_file, output_file)
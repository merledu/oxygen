import re

# Define the formats for each type of instruction
FORMATS = {
    'R': '{funct7:07}{rs2:05}{rs1:05}{funct3:03}{rd:05}{opcode:07}',
    'I': '{imm:012}{rs1:05}{funct3:03}{rd:05}{opcode:07}',
    'S': '{imm_11_5:07}{rs2:05}{rs1:05}{funct3:03}{imm_4_0:05}{opcode:07}',
    'B': '{imm_12}{imm_10_5:06}{rs2:05}{rs1:05}{funct3:03}{imm_4_1:04}{imm_11}{opcode:07}',
    'U': '{imm:020}{rd:05}{opcode:07}',
    'J': '{imm_20}{imm_10_1:010}{imm_11}{imm_19_12:08}{rd:05}{opcode:07}',
    # C custom formats
    'CR': '{funct4:04}{rd_rs1:05}{rs2:05}{opcode:02}',#mv,add
    'CR(1)': '{funct4:06}{rd_rs1:03}{funct2:02}{rs2:03}{opcode:02}',#and,or,xor,sub,addw,subw
    'CR(2)': '{funct4:04}{imm:10}{opcode:02}',#ebreak
    'CR(3)': '{funct4:04}{rd_rs1:05}{rs2:05}{opcode:02}',#jr,jalr
    'CI': '{funct3:03}{imm:01}{rd_rs1:05}{imm:05}{opcode:02}',#slli,nop
    'CI(1)': '{funct3:03}{imm:01}{rd:05}{imm:05}{opcode:02}',#lwsp,Flwsp
    'CI(2)': '{funct3:03}{imm:01}{rd:05}{imm:05}{opcode:02}',#ldsp,fldsp
    'CI(3)': '{funct3:03}{imm:01}{rd:05}{imm:05}{opcode:02}',#lqsp
    'CI(4)': '{funct3:03}{imm:01}{rd:05}{imm:05}{opcode:02}',#li,lui
    'CI(5)': '{funct3:03}{imm:01}{rd:05}{imm:05}{opcode:02}',#addi,addiw
    'CI(6)': '{funct3:03}{imm:01}{rd:05}{imm:05}{opcode:02}',#addi16sp
    'CSS(1)': '{funct3:03}{imm:06}{rs2:05}{opcode:02}',#swsp,fswsp
    'CSS(2)': '{funct3:03}{imm:06}{rs2:05}{opcode:02}',#sdsp,fsdsp
    'CSS(3)': '{funct3:03}{imm:06}{rs2:05}{opcode:02}',#sqsp
    'CIW': '{funct3:03}{imm:08}{rd:03}{opcode:02}',#addi4spn
    'CL': '{funct3:03}{imm:03}{rs1:03}{imm:02}{rd:03}{opcode:02}',
    'CL(1)': '{funct3:03}{imm:03}{rs1:03}{imm:02}{rd:03}{opcode:02}',#lw,flw
    'CL(2)': '{funct3:03}{imm:03}{rs1:03}{imm:02}{rd:03}{opcode:02}',#ld,lq,fld
    'CS': '{funct3:03}{imm:03}{rd_rs1:03}{imm:02}{rs2:03}{opcode:02}',
    'CS(1)': '{funct3:03}{imm:03}{rd_rs1:03}{imm:02}{rs2:03}{opcode:02}',#sw,fsw
    'CS(2)': '{funct3:03}{imm:03}{rd_rs1:03}{imm:02}{rs2:03}{opcode:02}',#sd,fsd
    'CS(3)': '{funct3:03}{imm:03}{rd_rs1:03}{imm:02}{rs2:03}{opcode:02}',#sq    
    'CA': '{funct6:06}{rd_rs1:03}{rs2:03}{opcode:02}',
    'CB': '{funct3:03}{offset:08}{rd_rs1:03}{offset:03}{opcode:02}',
    'CB(1)': '{funct3:03}{offset:03}{rs1:03}{offset:05}{opcode:02}',#beqz,bnez
    'CB(2)': '{funct3:03}{offset:01}{funct2:02}{rs1:03}{offset:05}{opcode:02}',#srli,srai,andi
    'CJ': '{funct3:03}{jump_target:11}{opcode:02}'#j,jal
}

Registers_ABI = {
        'zero': 'x0',
        'ra': 'x1',
        'sp': 'x2',
        'gp': 'x3',
        'tp': 'x4',
        't0': 'x5',
        't1': 'x6',
        't2': 'x7',
        's0': 'x8',
        's1': 'x9',
        'a0': 'x10',
        'a1': 'x11',
        'a2': 'x12',
        'a3': 'x13',
        'a4': 'x14',
        'a5': 'x15',
        'a6': 'x16',
        'a7': 'x17',
        's2': 'x18',
        's3': 'x19',
        's4': 'x20',
        's5': 'x21',
        's6': 'x22',
        's7': 'x23',
        's8': 'x24',
        's9': 'x25',
        's10': 'x26',
        's11': 'x27',
        't3': 'x28',
        't4': 'x29',
        't5': 'x30',
        't6': 'x31'
    }

INSTRUCTION_SET = {
    'add':     ('0110011', '000', '0000000', 'R'),
    'sub':     ('0110011', '000', '0100000', 'R'),
    'xor':     ('0110011', '100', '0000000', 'R'),
    'or':      ('0110011', '110', '0000000', 'R'),
    'and':     ('0110011', '111', '0000000', 'R'),
    'sll':     ('0110011', '001', '0000000', 'R'),
    'srl':     ('0110011', '101', '0000000', 'R'),
    'sra':     ('0110011', '101', '0100000', 'R'),
    'addi':    ('0010011', '000', None, 'I'),
    'xori':    ('0010011', '100', None, 'I'),
    'ori':     ('0010011', '110', None, 'I'),
    'andi':    ('0010011', '111', None, 'I'),
    'lb':      ('0000011', '000', None, 'LI'),
    'lh':      ('0000011', '001', None, 'LI'),
    'lw':      ('0000011', '010', None, 'LI'),
    'lbu':     ('0000011', '100', None, 'LI'),
    'lhu':     ('0000011', '101', None, 'LI'),
    'sb':      ('0100011', '000', None, 'S'),
    'sh':      ('0100011', '001', None, 'S'),
    'sw':      ('0100011', '010', None, 'S'),
    'beq':     ('1100011', '000', None, 'B'),
    'bne':     ('1100011', '001', None, 'B'),
    'blt':     ('1100011', '100', None, 'B'),
    'bge':     ('1100011', '101', None, 'B'),
    'bltu':    ('1100011', '110', None, 'B'),
    'bgeu':    ('1100011', '111', None, 'B'),
    'jal':     ('1101111', None, None, 'J'),
    'jalr':    ('1100111', '000', None, 'I'),
    'lui':     ('0110111', None, None, 'U'),
    'auipc':   ('0010111', None, None, 'U'),
    'ecall':   ('1110011', '000', '0000000', 'I'),
    'ebreak':  ('1110011', '000', '0000001', 'I'),
    # M extension instructions
    'mul':     ('0110011', '000', '0000001', 'R'),
    'mulh':    ('0110011', '001', '0000001', 'R'),
    'mulhsu':  ('0110011', '010', '0000001', 'R'),
    'mulhu':   ('0110011', '011', '0000001', 'R'),
    'div':     ('0110011', '100', '0000001', 'R'),
    'divu':    ('0110011', '101', '0000001', 'R'),
    'rem':     ('0110011', '110', '0000001', 'R'),
    'remu':    ('0110011', '111', '0000001', 'R'),
    # F extension instructions
    'flw':     ('0000111', '010', None, 'LI'),
    'fsw':     ('0100111', '010', None, 'S'),
    'fadd.s':  ('1010011', '000', '0000000', 'R'),
    'fsub.s':  ('1010011', '000', '0000100', 'R'),
    'fmul.s':  ('1010011', '000', '0001000', 'R'),
    'fdiv.s':  ('1010011', '000', '0001100', 'R'),
    'fsqrt.s': ('1010011', '000', '0101100', 'R'),
    'fsgnj.s': ('1010011', '000', '0010000', 'R'),
    'fsgnjn.s':('1010011', '000', '0010001', 'R'),
    'fsgnjx.s':('1010011', '000', '0010010', 'R'),
    'fmin.s':  ('1010011', '000', '0010100', 'R'),
    'fmax.s':  ('1010011', '000', '0010101', 'R'),
    'fcvt.w.s':('1010011', '000', '1100000', 'R'),
    'fcvt.wu.s':('1010011', '000', '1100001', 'R'),
    'fmv.x.w': ('1010011', '000', '1110000', 'R'),
    'feq.s':   ('1010011', '000', '1010000', 'R'),
    'flt.s':   ('1010011', '000', '1010001', 'R'),
    'fle.s':   ('1010011', '000', '1010010', 'R'),
    'fclass.s':('1010011', '000', '1110001', 'R'),
    'fcvt.s.w':('1010011', '000', '1101000', 'R'),
    'fcvt.s.wu':('1010011', '000', '1101001', 'R'),
    'fmv.w.x': ('1010011', '000', '1111000', 'R'),
}

C_INST_SET  = {
    # RV32C (Compressed) extension instructions
    'c.add':    ('10', None, '1001', 'CR'),
    'c.mv':     ('10', None, '1000', 'CR'),
    
    'c.or':     ('01', '10', '100011', 'CR(1)'),
    'c.and':    ('01', '11', '100011', 'CR(1)'),
    'c.sub':    ('01', '00', '100011', 'CR(1)'),
    'c.subw':   ('01', '00', '100111', 'CR(1)'),
    'c.xor':    ('01', '01', '100011', 'CR(1)'),
    'c.addw':   ('01', '01', '100111', 'CR(1)'),
    
    'c.ebreak': ('10', None, '1001', 'CR(2)'),
    
    'c.jalr':   ('10', None, '1001', 'CR(3)'),
    'c.jr':     ('10', None, '1000', 'CR(3)'),
    
    
    
    'c.nop':    ('01', '000', None, 'CI'),
    'c.slli':   ('10', '000', None, 'CI'),
    
    'c.flwsp':  ('10', '011', None, 'CI(1)'),
    'c.lwsp':   ('10', '010', None, 'CI(1)'),
    
    'c.fldsp':  ('10', '001', None, 'CI(2)'),
    'c.ldsp':   ('10', '011', None, 'CI(2)'),
    #CI(3) ins missing
    'c.li':     ('01', '010', None, 'CI(4)'),
    'c.lui':    ('01', '011', None, 'CI(4)'),
    
    'c.addi':   ('01', '000', None, 'CI(5)'),
    'c.addiw':   ('01', '001', None, 'CI(5)'),
    
    'c.addi16sp':('01', '011', None, 'CI(6)'),
    
    
    
    'c.addi4spn':('00', '000', None, 'CIW'),
    
    
    
    'c.beqz':   ('01', '110', None, 'CB(1)'),
    'c.bnez':   ('01', '111', None, 'CB(1)'),
    
    'c.srai':   ('01', '100', '01', 'CB(2)'),
    'c.srli':   ('01', '100', '00', 'CB(2)'),
    'c.andi':   ('01', '100', '10', 'CB(2)'),
    
    
    'c.fswsp':  ('10', '111', None, 'CSS(1)'),
    'c.swsp':   ('10', '110', None, 'CSS(1)'),
    
    'c.sdsp':  ('10', '111', None, 'CSS(2)'),
    'c.fsdsp':  ('10', '101', None, 'CSS(2)'),
    
    'c.sqsp':  ('10', '101', None, 'CSS(3)'),
    
    
    
    'c.flw':    ('00', '011', None, 'CL(1)'),
    'c.lw':     ('00', '010', None, 'CL(1)'),
    
    'c.fld':    ('00', '001', None, 'CL(2)'),
    'c.ld':     ('00', '011', None, 'CL(2)'),
    
    
    
    'c.j':      ('01', '101', None, 'CJ'),
    'c.jal':    ('01', '001', None, 'CJ'),
    
    
    
    'c.fsw':    ('00', '111', None, 'CS(1)'),
    'c.sw':     ('00', '110', None, 'CS(1)'),
    
    'c.sd':    ('00', '111', None, 'CS(2)'),
    'c.fsd':    ('00', '101', None, 'CS(2)'),
    
    
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
def replace_labels_with_immediates(instructions):
    # Split the instructions into a list of lines
    lines = instructions.split('\n')
    print(lines)
    # First pass: Identify labels and their addresses
    labels = {}
    address = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            label = line.split(':')[0].strip()
            labels[label] = address
            print(label)
        else:
            print(address , " " , line)
            address += 4
            print(labels)
            
            

    # Second pass: Calculate immediates and replace labels
    result = []
    address = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            label = line.split(':')[0].strip()
            line = line.split(':')[1].strip()
            if not line:
                continue
        if line[0].lower()=='b':
            parts = line.split(',')
            label = parts[-1].strip()
            if label in labels:
                immediate = labels[label] - address
                new_line = f"{parts[0]},{parts[1]},{immediate}"
                result.append(new_line)
        elif line[0].lower()=='j':
            parts = line.split(' ')
            label = parts[-1].strip()
            if (label in labels):
                immediate = labels[label]-address
                new_line = f"{parts[0]} {immediate}"
                result.append(new_line)
                
            else:
                result.append(line)
        else:
            result.append(line)
        address += 4
    
    return '\n'.join(result)

def register_to_bin(register):
    """Convert register name to binary representation"""
    if register in Registers_ABI:
        x = Registers_ABI[register]
        
        x = int(x[1:])
        print(x)
        x = '{0:05b}'.format(x)
        return x
    
    elif register.startswith('x'):
        x = int(register[1:])
        x = '{0:05b}'.format(x)
        
        return x
        # return int(register[1:])
    
    raise ValueError(f"Unknown register: {register}")

def imm_to_bin(imm, length):
    """Convert immediate value to binary representation of given length"""
    x = eval(imm)
    value = int(x)
    if value < 0:
        value = (1 << length) + value
    return format(value, f'0{length}b')


def parse_instruction(instruction):
    """Parse the instruction into its binary components"""
    parts = re.split(r'\s|,', instruction.strip())
    while('' in parts):
        parts.remove('')
    print("after remove : " ,parts)
    inst_name = parts[0]
    print(parts)
    # print (inst_name)
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
    elif inst_name in C_INST_SET:
        opcode, funct3, funct4, inst_type = C_INST_SET[inst_name]
        if inst_type == 'CSS':
            rs2 = register_to_bin(parts[1])
            imm = imm_to_bin(parts[2],6)
            return FORMATS['CSS'].format(funct3=funct3, imm=imm, rs2=rs2, opcode=opcode)
        elif inst_type == 'CIW':
            rd=register_to_bin(parts[1])
            imm = imm_to_bin(parts[2],8)
            return FORMATS['CIW'].format(funct3=funct3, imm=imm, rd=rd, opcode=opcode)
        elif inst_type == 'CL':
            rd = register_to_bin(parts[1])
            rs1 = register_to_bin(parts[3])
            
            
            
        elif inst_type == 'CJ':
            imm=imm_to_bin(parts[1],11)
            return FORMATS['CJ'].format(funct3=funct3, offset=imm, opcode=opcode)
        elif inst_type == 'CR':
            rd_rs1 = register_to_bin(parts[1])
            rs2 = register_to_bin(parts[2])
            return FORMATS['CR'].format(funct4=funct4,rd_rs1=rd_rs1,rs2=rs2,opcode=opcode)
    # print(inst_name)
    opcode, funct3, funct7, inst_type = INSTRUCTION_SET[inst_name]
    
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
        imm = imm_to_bin(parts[2], 21)
        imm_20 = imm[0]
        imm_10_1 = imm[10:20]
        imm_11 = imm[9]
        imm_19_12 = imm[1:9]
        return FORMATS['J'].format(imm_20=imm_20, imm_10_1=imm_10_1, imm_11=imm_11, imm_19_12=imm_19_12, rd=rd, opcode=opcode)
    
    elif inst_type == 'LI':
        rd = register_to_bin(parts[1])
        if (len(parts) == 3):
            offset_base_str = parts[2]
            print(offset_base_str)
            match_brackets = re.match(r'^([^(]+)\(([^)]+)\)$', offset_base_str)
            if match_brackets:
                imm = imm_to_bin(int(match_brackets.group(1),16),12)
                rs1 = register_to_bin(match_brackets.group(2))
            else:
                imm = imm_to_bin(str(imm_value),12)
                rs1 = register_to_bin(offset_base_str)
        else:
            rs1 = register_to_bin(parts[3])
            immediate = parts[2]
            if immediate.startswith('0x') or immediate.startswith('-0x'):
                imm_value = int(immediate, 16)
                imm = imm_to_bin(str(imm_value),12)
            else:
                imm_value = int(immediate)
                imm = imm_to_bin(str(imm_value),12)
        
        return FORMATS['I'].format(imm=imm, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)
        

def convert_to_hex(bin_str):
    """Convert binary string to hexadecimal"""
    # print(bin_str)
    hex_str = hex(int(bin_str, 2))[2:].zfill(8)
    return hex_str

def main(instructions_str):
    instructions_str = replace_labels_with_immediates(instructions_str)
    if ('(' or ')' in instructions_str):
       
        instructions_str=instructions_str.replace('(', ' ')
        instructions_str=instructions_str.replace(')', ' ')
    
    


    instructions = instructions_str.lower().splitlines()
    while '' in instructions:
        instructions.remove('')
    
    # if ('(' or ')' in instructions):
    #     print(instructions)
    #     instructions.replace('(', ' ')
    #     instructions.replace(')', ' ')
    
    hex_lines = []
    for instruction in instructions:
        
        bin_str = parse_instruction((instruction))
        hex_str = convert_to_hex(bin_str)
        hex_lines.append(hex_str)
    
    # Join the hex strings with newline characters
    hex_output = '\n'.join(hex_lines)
    print(hex_output)
    
    return hex_output

def checkpsudo (instructions_str):
    instructions_str = replace_labels_with_immediates(instructions_str)
    inss = instructions_str.splitlines()
    while '' in inss:
        inss.remove('')
    retinstructions = []
    for instruction in inss:
        parts = re.split(r'\s|,', instruction.strip())
        while('' in parts):
            parts.remove('')
        inst_name = parts[0]
        print("parts in check " ,parts)
        # print (inst_name)
        if inst_name in PSEUDO_INSTRUCTION_SET:
            
            base_inst = PSEUDO_INSTRUCTION_SET[inst_name]
            # print(base_inst)
            # print(inst_name[0])
            
            if (inst_name == 'nop'):
                retinstructions.append(base_inst)
            elif(inst_name[0] == 'b'):
                retinstructions.append(base_inst.format(rs=parts[1], offset=parts[2]))
            elif(inst_name[0] == 'j'):
                retinstructions.append(base_inst.format(a=parts[1]))
            elif(inst_name == 'ret'):
                retinstructions.append(base_inst)
            elif (inst_name == 'li'):
                retinstructions.append((base_inst.format(rd=parts[1], imm=parts[2])))
            elif (inst_name == 'mv'):
                retinstructions.append(base_inst.format(rd=parts[1], rs=parts[2]))
        else :
            retinstructions.append(instruction)         
    return retinstructions

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

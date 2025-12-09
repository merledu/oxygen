import re

# Define the formats for each type of instruction
FORMATS = {
    'R': '{funct7:07}{rs2:05}{rs1:05}{funct3:03}{rd:05}{opcode:07}',
    'I': '{imm:012}{rs1:05}{funct3:03}{rd:05}{opcode:07}',
    'S': '{imm_11_5:07}{rs2:05}{rs1:05}{funct3:03}{imm_4_0:05}{opcode:07}',
    'B': '{imm_12}{imm_10_5:06}{rs2:05}{rs1:05}{funct3:03}{imm_4_1:04}{imm_11}{opcode:07}',
    'U': '{imm:020}{rd:05}{opcode:07}',
    'J': '{imm_20}{imm_10_1:010}{imm_11}{imm_19_12:08}{rd:05}{opcode:07}',
    # Vector Extension Formats
    'V': '{funct6:06}{vm:01}{vs2:05}{rs1:05}{funct3:03}{vd:05}{opcode:07}', # OPIVV, OPMVV, OPFVV
    'V_IV': '{funct6:06}{vm:01}{vs2:05}{imm:05}{funct3:03}{vd:05}{opcode:07}', # OPIVI
    'V_X': '{funct6:06}{vm:01}{vs2:05}{rs1:05}{funct3:03}{vd:05}{opcode:07}', # OPIVX
    # Compressed Formats (16-bit)
    'CR': '{funct4:04}{rd:05}{rs2:05}{opcode:02}',
    'CI': '{funct3:03}{imm:01}{rd:05}{imm_4_0:05}{opcode:02}',
    'CSS': '{funct3:03}{imm:06}{rs2:05}{opcode:02}',
    'CIW': '{funct3:03}{imm:08}{rd:03}{opcode:02}',
    'CL': '{funct3:03}{imm_5_3:03}{rs1:03}{imm_2_6:02}{rd:03}{opcode:02}',
    'CS': '{funct3:03}{imm_5_3:03}{rs1:03}{imm_2_6:02}{rs2:03}{opcode:02}',
    'CB': '{funct3:03}{offset:08}{rs1:03}{opcode:02}', # Simplified for now
    'CJ': '{funct3:03}{offset:011}{opcode:02}',
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
    'slt':     ('0110011', '010', '0000000', 'R'),
    'sltu':    ('0110011', '011', '0000000', 'R'),
    'slti':    ('0010011', '010', None, 'I'),
    'sltiu':   ('0010011', '011', None, 'I'),
    'fence':   ('0001111', '000', None, 'I'),
    'fence.i': ('0001111', '001', None, 'I'),
    'csrrw':   ('1110011', '001', None, 'I'),
    'csrrs':   ('1110011', '010', None, 'I'),
    'csrrc':   ('1110011', '011', None, 'I'),
    'csrrwi':  ('1110011', '101', None, 'I'),
    'csrrsi':  ('1110011', '110', None, 'I'),
    'csrrci':  ('1110011', '111', None, 'I'),
    # C extension instructions
    'c.addi4spn': ('00', '000', None, 'CIW'),
    'c.lw':       ('00', '010', None, 'CL'),
    'c.sw':       ('00', '110', None, 'CS'),
    'c.addi':     ('01', '000', None, 'CI'),
    'c.jal':      ('01', '001', None, 'CJ'),
    'c.li':       ('01', '010', None, 'CI'),
    'c.addi16sp': ('01', '011', None, 'CI'),
    'c.lui':      ('01', '011', None, 'CI'),
    'c.srli':     ('01', '100', None, 'CB'),
    'c.srai':     ('01', '100', None, 'CB'),
    'c.andi':     ('01', '100', None, 'CB'),
    'c.sub':      ('01', '100', None, 'CA'),
    'c.xor':      ('01', '100', None, 'CA'),
    'c.or':       ('01', '100', None, 'CA'),
    'c.and':      ('01', '100', None, 'CA'),
    'c.j':        ('01', '101', None, 'CJ'),
    'c.beqz':     ('01', '110', None, 'CB'),
    'c.bnez':     ('01', '111', None, 'CB'),
    'c.slli':     ('10', '000', None, 'CI'),
    'c.fldsp':    ('10', '001', None, 'CI'),
    'c.lwsp':     ('10', '010', None, 'CI'),
    'c.flwsp':    ('10', '011', None, 'CI'),
    'c.jr':       ('10', '100', None, 'CR'),
    'c.mv':       ('10', '100', None, 'CR'),
    'c.ebreak':   ('10', '100', None, 'CR'),
    'c.jalr':     ('10', '100', None, 'CR'),
    'c.add':      ('10', '100', None, 'CR'),
    'c.fsdsp':    ('10', '101', None, 'CSS'),
    'c.swsp':     ('10', '110', None, 'CSS'),
    'c.fswsp':    ('10', '111', None, 'CSS'),
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
    # D extension instructions (double-precision floating-point)
    'fld':     ('0000011', '011', None, 'LI'), # Load Double
    'fsd':     ('0100011', '011', None, 'S'),  # Store Double
    'fadd.d':  ('1010011', '001', '0000000', 'R'),
    'fsub.d':  ('1010011', '001', '0000100', 'R'),
    'fmul.d':  ('1010011', '001', '0001000', 'R'),
    'fdiv.d':  ('1010011', '001', '0001100', 'R'),
    'fsqrt.d': ('1010011', '001', '0101100', 'R'),
    'fsgnj.d': ('1010011', '001', '0010000', 'R'),
    'fsgnjn.d':('1010011', '001', '0010001', 'R'),
    'fsgnjx.d':('1010011', '001', '0010010', 'R'),
    'fmin.d':  ('1010011', '001', '0010100', 'R'),
    'fmax.d':  ('1010011', '001', '0010101', 'R'),
    'fcvt.s.d':('1010011', '000', '0100000', 'R'),
    'fcvt.d.s':('1010011', '001', '0100000', 'R'),
    'fcvt.w.d':('1010011', '001', '1100000', 'R'),
    'fcvt.wu.d':('1010011', '001', '1100001', 'R'),
    'fmv.x.d': ('1010011', '001', '1110000', 'R'),
    'feq.d':   ('1010011', '001', '1010000', 'R'),
    'flt.d':   ('1010011', '001', '1010001', 'R'),
    'fle.d':   ('1010011', '001', '1010010', 'R'),
    'fclass.d':('1010011', '001', '1110001', 'R'),
    'fcvt.d.w':('1010011', '001', '1101000', 'R'),
    'fcvt.d.wu':('1010011', '001', '1101001', 'R'),
    'fmv.d.x': ('1010011', '001', '1111000', 'R'),
    # V extension instructions
    'vsetvli': ('1010111', '111', None, 'I'), # Special I-type
    'vle8.v':  ('0000111', '000', '000000', 'V'), # Width encoded in funct3
    'vle16.v': ('0000111', '101', '000000', 'V'),
    'vle32.v': ('0000111', '110', '000000', 'V'),
    'vle64.v': ('0000111', '111', '000000', 'V'),
    'vse8.v':  ('0100111', '000', '000000', 'V'),
    'vse16.v': ('0100111', '101', '000000', 'V'),
    'vse32.v': ('0100111', '110', '000000', 'V'),
    'vse64.v': ('0100111', '111', '000000', 'V'),
    'vadd.vv': ('1010111', '000', '000000', 'V'),
    'vadd.vx': ('1010111', '100', '000000', 'V'),
    'vadd.vi': ('1010111', '011', '000000', 'V'),
    'vsub.vv': ('1010111', '000', '000010', 'V'),
    'vsub.vx': ('1010111', '100', '000010', 'V'),
    'vrsub.vx':('1010111', '100', '000011', 'V'),
    'vrsub.vi':('1010111', '011', '000011', 'V'),
    'vmul.vv': ('1010111', '000', '100101', 'V'),
    'vmul.vx': ('1010111', '100', '100101', 'V'),
    'vdiv.vv': ('1010111', '000', '100001', 'V'),
    'vdiv.vx': ('1010111', '100', '100001', 'V'),
    'vmax.vv': ('1010111', '000', '000110', 'V'),
    'vmax.vx': ('1010111', '100', '000110', 'V'),
    'vmin.vv': ('1010111', '000', '000101', 'V'),
    'vmin.vx': ('1010111', '100', '000101', 'V'),
    'vand.vv': ('1010111', '000', '001001', 'V'),
    'vand.vx': ('1010111', '100', '001001', 'V'),
    'vand.vi': ('1010111', '011', '001001', 'V'),
    'vor.vv':  ('1010111', '000', '001010', 'V'),
    'vor.vx':  ('1010111', '100', '001010', 'V'),
    'vor.vi':  ('1010111', '011', '001010', 'V'),
    'vxor.vv': ('1010111', '000', '001011', 'V'),
    'vxor.vx': ('1010111', '100', '001011', 'V'),
    'vxor.vi': ('1010111', '011', '001011', 'V'),
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
    elif register.startswith('v'):
        v = int(register[1:])
        v = '{0:05b}'.format(v)
        return v
    elif register.startswith('f'):
        f = int(register[1:])
        f = '{0:05b}'.format(f)
        return f
    elif register in ['zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2', 's0', 's1', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 't3', 't4', 't5', 't6']:
        # Map ABI names to x registers
        abi_map = {
            'zero': 0, 'ra': 1, 'sp': 2, 'gp': 3, 'tp': 4, 't0': 5, 't1': 6, 't2': 7,
            's0': 8, 's1': 9, 'a0': 10, 'a1': 11, 'a2': 12, 'a3': 13, 'a4': 14, 'a5': 15,
            'a6': 16, 'a7': 17, 's2': 18, 's3': 19, 's4': 20, 's5': 21, 's6': 22, 's7': 23,
            's8': 24, 's9': 25, 's10': 26, 's11': 27, 't3': 28, 't4': 29, 't5': 30, 't6': 31
        }
        x = abi_map[register]
        return '{0:05b}'.format(x)
        
    raise ValueError(f"Unknown register: {register}")

def imm_to_bin(imm, length):
    """Convert immediate value to binary representation of given length"""
    value = int(imm)
    if value < 0:
        value = (1 << length) + value
    return format(value, f'0{length}b')


def parse_instruction(instruction):
    """Parse the instruction into its binary components"""
    try:
        parts = re.split(r'\s|,', instruction.strip())
        parts = [p for p in parts if p] # Remove empty strings
        if not parts:
            return "" # Should be handled by main, but just in case
            
        inst_name = parts[0]
        
        if inst_name in PSEUDO_INSTRUCTION_SET:
            base_inst = PSEUDO_INSTRUCTION_SET[inst_name]
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
        
        if inst_name not in INSTRUCTION_SET:
            raise ValueError(f"Unknown instruction: {inst_name}")

        inst_info = INSTRUCTION_SET[inst_name]
        opcode = inst_info[0]
        inst_type = inst_info[3]
        
        if inst_type == 'R':
            funct3 = inst_info[1]
            funct7 = inst_info[2]
            rd = register_to_bin(parts[1])
            rs1 = register_to_bin(parts[2])
            rs2 = register_to_bin(parts[3])
            return FORMATS['R'].format(funct7=funct7, rs2=rs2, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)
        
        elif inst_type == 'I':
            funct3 = inst_info[1]
            rd = register_to_bin(parts[1])
            
            # Handle special I-type instructions like fence, ecall, ebreak which have fixed operands or different parsing
            if inst_name in ['fence', 'fence.i', 'ecall', 'ebreak']:
                 # These usually don't have standard rd, rs1, imm parsing in the same way, or are fixed.
                 # For simplicity, assuming standard I-format with 0s if not specified, but INSTRUCTION_SET defines them.
                 # ecall/ebreak are defined with fixed funct3/funct7/opcode.
                 # If parts has less args, we might need to handle defaults.
                 if inst_name in ['ecall', 'ebreak']:
                     return FORMATS['I'].format(imm='000000000000', rs1='00000', funct3=funct3, rd='00000', opcode=opcode)
                 if inst_name == 'fence':
                     # fence pred, succ
                     # For now, just return 0s for simplicity or parse if needed.
                     return FORMATS['I'].format(imm='000000000000', rs1='00000', funct3=funct3, rd='00000', opcode=opcode)

            if inst_name.startswith('csr'):
                # csr instructions: csrrw rd, csr, rs1
                # csr is 12-bit imm
                csr = imm_to_bin(parts[2], 12)
                rs1 = register_to_bin(parts[3])
                return FORMATS['I'].format(imm=csr, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)

            rs1 = register_to_bin(parts[2])
            imm = imm_to_bin(parts[3], 12)
            return FORMATS['I'].format(imm=imm, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)
        
        elif inst_type == 'S':
            funct3 = inst_info[1]
            rs2 = register_to_bin(parts[1]) # src
            rs1 = register_to_bin(parts[2]) # base
            imm = imm_to_bin(parts[3], 12)
            imm_11_5 = imm[:7]
            imm_4_0 = imm[7:]
            return FORMATS['S'].format(imm_11_5=imm_11_5, rs2=rs2, rs1=rs1, funct3=funct3, imm_4_0=imm_4_0, opcode=opcode)
        
        elif inst_type == 'B':
            funct3 = inst_info[1]
            rs1 = register_to_bin(parts[1])
            rs2 = register_to_bin(parts[2])
            imm = imm_to_bin(parts[3], 13)
            imm_12 = imm[0]
            imm_10_5 = imm[2:8]
            imm_4_1 = imm[8:12]
            imm_11 = imm[1]
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
            funct3 = inst_info[1]
            rd = register_to_bin(parts[1])
            rs1 = register_to_bin(parts[3])
            imm = imm_to_bin(parts[2],12)
            return FORMATS['I'].format(imm=imm, rs1=rs1, funct3=funct3, rd=rd, opcode=opcode)

        elif inst_type == 'V':
            funct3 = inst_info[1]
            funct6 = inst_info[2]
            vd = register_to_bin(parts[1])
            vm = '1' # Masking disabled by default for now
            
            if inst_name.startswith('vle') or inst_name.startswith('vse'):
                 # Load/Store: vle8.v vd, (rs1) -> parts: [vle8.v, vd, (rs1)]
                 mem_op = parts[2].strip('()')
                 rs1 = register_to_bin(mem_op)
                 # For Load: vd=vd, rs1=rs1, vs2=0 (lumop), vm=1
                 return FORMATS['V'].format(funct6=funct6, vm=vm, vs2='00000', rs1=rs1, funct3=funct3, vd=vd, opcode=opcode)

            vs2 = register_to_bin(parts[2])
            
            if inst_name.endswith('.vi'):
                 imm = imm_to_bin(parts[3], 5)
                 return FORMATS['V_IV'].format(funct6=funct6, vm=vm, vs2=vs2, imm=imm, funct3=funct3, vd=vd, opcode=opcode)
            elif inst_name.endswith('.vx'):
                 rs1 = register_to_bin(parts[3])
                 return FORMATS['V_X'].format(funct6=funct6, vm=vm, vs2=vs2, rs1=rs1, funct3=funct3, vd=vd, opcode=opcode)
            else:
                 # .vv
                 vs1 = register_to_bin(parts[3])
                 return FORMATS['V'].format(funct6=funct6, vm=vm, vs2=vs2, rs1=vs1, funct3=funct3, vd=vd, opcode=opcode)

        # Compressed Instructions
        elif inst_type == 'CR':
            funct4 = inst_info[1]
            rd = register_to_bin(parts[1])
            rs2 = register_to_bin(parts[2])
            return FORMATS['CR'].format(funct4=funct4, rd=rd, rs2=rs2, opcode=opcode)
        
        elif inst_type == 'CI':
            funct3 = inst_info[1]
            rd = register_to_bin(parts[1])
            imm = imm_to_bin(parts[2], 6) # 6-bit imm for CI
            imm_val = imm[0]
            imm_4_0 = imm[1:]
            return FORMATS['CI'].format(funct3=funct3, imm=imm_val, rd=rd, imm_4_0=imm_4_0, opcode=opcode)
            
        elif inst_type == 'CSS':
            funct3 = inst_info[1]
            rs2 = register_to_bin(parts[1])
            imm = imm_to_bin(parts[2], 6)
            return FORMATS['CSS'].format(funct3=funct3, imm=imm, rs2=rs2, opcode=opcode)

        elif inst_type == 'CIW':
            funct3 = inst_info[1]
            rd = register_to_bin(parts[1])
            # rd' is 3 bits (x8-x15)
            rd_val = int(rd, 2)
            if not (8 <= rd_val <= 15): raise ValueError("CIW rd must be x8-x15")
            rd_3 = format(rd_val - 8, '03b')
            imm = imm_to_bin(parts[2], 8)
            return FORMATS['CIW'].format(funct3=funct3, imm=imm, rd=rd_3, opcode=opcode)

        elif inst_type == 'CL' or inst_type == 'CS':
            funct3 = inst_info[1]
            rd_rs2 = register_to_bin(parts[1]) # rd for CL, rs2 for CS
            # rd'/rs2' must be x8-x15
            val = int(rd_rs2, 2)
            if not (8 <= val <= 15): raise ValueError("CL/CS register must be x8-x15")
            reg_3 = format(val - 8, '03b')
            
            # Address parsing: offset(rs1)
            # parts[2] is "offset(rs1)"
            match = re.match(r'(-?\d+)\((.*)\)', parts[2])
            if match:
                offset = match.group(1)
                rs1_name = match.group(2)
                rs1 = register_to_bin(rs1_name)
                rs1_val = int(rs1, 2)
                if not (8 <= rs1_val <= 15): raise ValueError("CL/CS rs1 must be x8-x15")
                rs1_3 = format(rs1_val - 8, '03b')
                
                imm = imm_to_bin(offset, 5) # 5-bit offset (scaled? usually scaled by 4 for word)
                # Assuming raw immediate for now, or need to handle scaling based on instruction
                imm_5_3 = imm[0:3]
                imm_2_6 = imm[3:5] # This split depends on specific format
                
                if inst_type == 'CL':
                     return FORMATS['CL'].format(funct3=funct3, imm_5_3=imm_5_3, rs1=rs1_3, imm_2_6=imm_2_6, rd=reg_3, opcode=opcode)
                else:
                     return FORMATS['CS'].format(funct3=funct3, imm_5_3=imm_5_3, rs1=rs1_3, imm_2_6=imm_2_6, rs2=reg_3, opcode=opcode)
            else:
                 raise ValueError("Invalid address format for CL/CS")

        elif inst_type == 'CB':
            funct3 = inst_info[1]
            rs1 = register_to_bin(parts[1])
            rs1_val = int(rs1, 2)
            if not (8 <= rs1_val <= 15): raise ValueError("CB rs1 must be x8-x15")
            rs1_3 = format(rs1_val - 8, '03b')
            offset = imm_to_bin(parts[2], 8)
            return FORMATS['CB'].format(funct3=funct3, offset=offset, rs1=rs1_3, opcode=opcode)

        elif inst_type == 'CJ':
            funct3 = inst_info[1]
            offset = imm_to_bin(parts[1], 11)
            return FORMATS['CJ'].format(funct3=funct3, offset=offset, opcode=opcode)
        
        else:
            raise ValueError(f"Unsupported instruction type: {inst_type}")
    except IndexError:
        raise ValueError("Invalid number of operands or malformed instruction")
        

def convert_to_hex(bin_str):
    """Convert binary string to hexadecimal"""
    # print(bin_str)
    length = len(bin_str)
    hex_len = length // 4
    hex_str = hex(int(bin_str, 2))[2:].zfill(hex_len)
    return hex_str

def main(instructions_str):
    # Split the input string into individual instructions
    instructions = instructions_str.splitlines()
    
    # Process each instruction and convert it to hex
    output_lines = []
    for i, instruction in enumerate(instructions):
        instruction = instruction.strip()
        if not instruction:
            continue
            
        try:
            bin_str = parse_instruction(instruction)
            hex_str = convert_to_hex(bin_str)
            output_lines.append(hex_str)
        except Exception as e:
            error_msg = f"Error on line {i+1}: '{instruction}' -> {str(e)}"
            output_lines.append(error_msg)
    
    # Join the hex strings with newline characters
    hex_output = '\n'.join(output_lines)
    
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

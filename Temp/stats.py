def count_instructions(instruction_string):
    lines = instruction_string.splitlines()
    total_instructions = 0
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.endswith(":") and len(stripped_line.split(":")[1].strip()) == 0:
            continue
        total_instructions += 1
    return total_instructions



def count_jump_instructions(instruction_string):
    lines = instruction_string.splitlines()
    jump_instructions = 0
    for line in lines:
        stripped_line = line.strip()
        if ":" in stripped_line:
            jump_instructions += 1
    return jump_instructions



def count_data_transfer_instructions(instruction_string):
    data_transfer_ops = ["sw", "sb", "sh", "lb", "lh", "lw", "lbu", "lhu"]
    lines = instruction_string.splitlines()
    data_transfer_instructions = 0
    for line in lines:
        stripped_line = line.strip()
        if any(op in stripped_line for op in data_transfer_ops):
            data_transfer_instructions += 1
    return data_transfer_instructions


def count_alu_instructions(instruction_string):
    alu_ops = [
        "add", "sub", "xor", "sll", "srl", "sra", "slt", "addi", "xori", "ori", "andi", 
        "slli", "srli", "srai", "slti", "sltiu", "sltu", "li", "lui", "mul", "mulh", 
        "auipc", "mulhsu", "mulhu", "div", "divu", "rem", "remu"
    ]
    lines = instruction_string.splitlines()
    alu_instructions = 0
    for line in lines:
        stripped_line = line.strip()
        if any(op in stripped_line for op in alu_ops):
            alu_instructions += 1
    return alu_instructions


def count_i_ins(instruction_string):
    i_ops = [
        "add", "addi", "sub", "lui", "auipc", "xor", "xori", "or", "ori", "and", "andi", "slt", "slti", "sltu"
        , "sltiu", "beq", "bne", "blt", "bge", "bltu", "bgeu", "jal", "jalr", "lb", "lh", "lw", "lbu", "lhu"
        , "sb", "sh", "sw", "sll", "slli", "srl", "srli", "sra", "srai", "li"
    ]
    lines = instruction_string.splitlines()
    i_instruction=0
    for line in lines:
        stripped_line = line.strip()
        if any(op in stripped_line for op in i_ops):
            i_instruction += 1
    return i_instruction


def count_m_ins(instruction_string):
    m_ops = [
        "mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu"
    ]
    lines = instruction_string.splitlines()
    m_instruction = 0
    for line in lines:
        stripped_line = line.strip()
        if any(op in stripped_line for op in m_ops):
            m_instruction += 1
    return m_instruction


def count_sup_ins(instruction_string):
    s_ops = [
        "lui", "auipc", "C.lui"
    ]
    lines = instruction_string.splitlines()
    s_instruction = 0
    for line in lines:
        stripped_line = line.strip()
        if any(op in stripped_line for op in s_ops):
            s_instruction += 1
    return s_instruction


def count_f_ins(instruction_string):
    f_ops = [
        "fmv", "fcvt", "fl", "fs", "fadd", "fsub", "fmul", "fdiv", "fsqrt", "fmadd", "fmsub", "fnmsub", "fnmadd",
        "fsgnj", "fsgnjn", "fsgnjx", "fmin", "fmax", "feq", "flt", "fle", "fclass"
    ]
    lines = instruction_string.splitlines()
    f_instruction = 0
    for line in lines:
        stripped_line = line.strip()
        if any(op in stripped_line for op in f_ops):
            f_instruction += 1
    return f_instruction


def count_c_ins(instruction_string):
    c_ops = [
        "c."
    ]
    lines = instruction_string.splitlines()
    c_instruction = 0
    for line in lines:
        stripped_line = line.strip()
        if any(op in stripped_line for op in c_ops):
            c_instruction += 1
    return c_instruction


def get_instruction_stats(instruction_string):
    instruction_result = count_instructions(instruction_string)
    jump_instruction_result = count_jump_instructions(instruction_string)
    data_transfer_instruction_result = count_data_transfer_instructions(instruction_string)
    alu_instruction_result = count_alu_instructions(instruction_string)
    i_instruction_result = count_i_ins(instruction_string)
    m_instruction_result = count_m_ins(instruction_string)
    s_instruction_result = count_sup_ins(instruction_string)
    f_instruction_result = count_f_ins(instruction_string)
    c_instruction_result = count_c_ins(instruction_string)
    
    # print(instruction_result)
    # print(i_instruction_result)
    # print(m_instruction_result)

    return instruction_result,jump_instruction_result, data_transfer_instruction_result, alu_instruction_result, i_instruction_result, m_instruction_result, s_instruction_result, f_instruction_result, c_instruction_result

    

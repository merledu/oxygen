def count_instructions(instruction_string):
    lines = instruction_string.splitlines()
    total_instructions = 0
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.endswith(":") and len(stripped_line.split(":")[1].strip()) == 0:
            continue
        total_instructions += 1
    return {total_instructions}



def count_jump_instructions(instruction_string):
    lines = instruction_string.splitlines()
    jump_instructions = 0
    for line in lines:
        stripped_line = line.strip()
        if ":" in stripped_line:
            jump_instructions += 1
    return {jump_instructions}



def count_data_transfer_instructions(instruction_string):
    data_transfer_ops = ["sw", "sb", "sh", "lb", "lh", "lw", "lbu", "lhu"]
    lines = instruction_string.splitlines()
    data_transfer_instructions = 0
    for line in lines:
        stripped_line = line.strip()
        if any(op in stripped_line for op in data_transfer_ops):
            data_transfer_instructions += 1
    return {data_transfer_instructions}


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


def get_instruction_stats(instruction_string):
    instruction_result = count_instructions(instruction_string)
    jump_instruction_result = count_jump_instructions(instruction_string)
    data_transfer_instruction_result = count_data_transfer_instructions(instruction_string)
    alu_instruction_result = count_alu_instructions(instruction_string)
    
    print(instruction_result)
    print(jump_instruction_result)
    print(data_transfer_instruction_result)
    print(alu_instruction_result)
    
    return {'total_ins' : instruction_result, 'jump_ins' : jump_instruction_result, 'data_transfer_ins' : data_transfer_instruction_result, 'alu_ins' : alu_instruction_result}

    

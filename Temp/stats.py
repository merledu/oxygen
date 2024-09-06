def count_instructions(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            total_instructions = 0

            for line in lines:
                stripped_line = line.strip()

                # Ignore lines that contain just ':' or ':' followed by whitespace
                if stripped_line.endswith(":") and stripped_line[:-1].strip() == "":
                    continue

                total_instructions += 1

            return f"total instructions are {total_instructions}"
    except FileNotFoundError:
        return "File not found. Please check the file path."


def count_jump_instructions(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            jump_instructions = 0

            for line in lines:
                stripped_line = line.strip()
                if ":" in stripped_line:
                    jump_instructions += 1

            return f"total jump instructions are {jump_instructions}"
    except FileNotFoundError:
        return "File not found. Please check the file path."


def count_data_transfer_instructions(file_path):
    data_transfer_ops = ["sw", "sb", "sh", "lb", "lh", "lw", "lbu", "lhu"]
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            data_transfer_instructions = 0

            for line in lines:
                stripped_line = line.strip()
                if any(op in stripped_line for op in data_transfer_ops):
                    data_transfer_instructions += 1

            return f"total data transfer instructions are {data_transfer_instructions}"
    except FileNotFoundError:
        return "File not found. Please check the file path."


def count_alu_instructions(file_path):
    alu_ops = [
        "add", "sub", "xor", "sll", "srl", "sra", "slt", "addi", "xori", "ori", "andi", 
        "slli", "srli", "srai", "slti", "sltiu", "sltu", "li", "lui", "mul", "mulh", 
        "auipc", "mulhsu", "mulhu", "div", "divu", "rem", "remu"
    ]
    
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            alu_instructions = 0

            for line in lines:
                stripped_line = line.strip()
                if any(op in stripped_line for op in alu_ops):
                    alu_instructions += 1

            return f"total ALU instructions are {alu_instructions}"
    except FileNotFoundError:
        return "File not found. Please check the file path."



file_path = "ins.txt"  # Replace with your file path
instruction_result = count_instructions(file_path)
jump_instruction_result = count_jump_instructions(file_path)
data_transfer_instruction_result = count_data_transfer_instructions(file_path)
alu_instruction_result = count_alu_instructions(file_path)

print(instruction_result)
print(jump_instruction_result)
print(data_transfer_instruction_result)
print(alu_instruction_result)

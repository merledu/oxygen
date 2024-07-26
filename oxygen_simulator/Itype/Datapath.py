class RISCVSimulator:
    def __init__(self):
       
        self.registers = [0] * 32
        
        self.pc = 0
       
        self.memory = {}

    def execute_instruction(self, instruction):
        
        opcode = instruction & 0x7F
        if opcode == 0x33:  # Rtype 
            self.execute_r_type(instruction)
        elif opcode == 0x13:  # Itype
            self.execute_i_type(instruction)
        elif opcode == 0x23:  # Stype 
            self.execute_s_type(instruction)
        elif opcode == 0x63:  # Btype
            self.execute_b_type(instruction)
        elif opcode == 0x37:  # Utype 
            self.execute_u_type(instruction)
        elif opcode == 0x6F:  # Jtype 
            self.execute_j_type(instruction)
        
    def execute_r_type(self, instruction):
        
        funct7 = (instruction >> 25) & 0x7F
        rs2 = (instruction >> 20) & 0x1F
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F
        
        #  ADD 
        if funct3 == 0x0 and funct7 == 0x00:
            self.registers[rd] = self.registers[rs1] + self.registers[rs2]
        # SUB 
        elif funct3 == 0x0 and funct7 == 0x20:
            self.registers[rd] = self.registers[rs1] - self.registers[rs2]
        

    def execute_i_type(self, instruction):
        
        imm = (instruction >> 20) & 0xFFF
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F

        # ADDI 
        if funct3 == 0x0:
            self.registers[rd] = self.registers[rs1] + self.sign_extend(imm, 12)
        

    def execute_s_type(self, instruction):
        
        imm = ((instruction >> 25) << 5) | ((instruction >> 7) & 0x1F)
        rs2 = (instruction >> 20) & 0x1F
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        opcode = instruction & 0x7F

        #SW
        if funct3 == 0x2:
            address = self.registers[rs1] + self.sign_extend(imm, 12)
            self.memory[address] = self.registers[rs2]
        

    def execute_b_type(self, instruction):
       
        imm = ((instruction >> 31) << 12) | (((instruction >> 7) & 0x1) << 11) | \
              (((instruction >> 25) & 0x3F) << 5) | (((instruction >> 8) & 0xF) << 1)
        rs2 = (instruction >> 20) & 0x1F
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        opcode = instruction & 0x7F

        #BEQ
        if funct3 == 0x0:
            if self.registers[rs1] == self.registers[rs2]:
                self.pc += self.sign_extend(imm, 13) - 4  # Adjust for the increment after execution
       

    def execute_u_type(self, instruction):
       
        imm = instruction & 0xFFFFF000
        rd = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F

        #LUI
        if opcode == 0x37:
            self.registers[rd] = imm
        

    def execute_j_type(self, instruction):
        
        imm = ((instruction >> 31) << 20) | (((instruction >> 21) & 0x3FF) << 1) | \
              (((instruction >> 20) & 0x1) << 11) | (((instruction >> 12) & 0xFF) << 12)
        rd = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F

        # JAL
        if opcode == 0x6F:
            self.registers[rd] = self.pc + 4
            self.pc += self.sign_extend(imm, 21) - 4  # increment after execution
        

    def sign_extend(self, value, bits):
        # imm ka signextend
        if (value >> (bits - 1)) & 1:
            value -= 1 << bits
        return value

    def run(self, instructions):
        #input will be a list from hex dump code
        for instruction in instructions:
            self.execute_instruction(instruction)
            self.pc += 4

    def dump_registers(self):
        # register values ye main pa bhejna
        for i in range(32):
            print(f"x{i}: {hex(self.registers[i])}")


simulator = RISCVSimulator()
instructions = [
    0x00200093,  # addi x1, x0, 2
    0x00300113,  # addi x2, x0, 3
    0x002081B3,  # add x3, x1, x2
    0x00400023,  # sw x4, 0(x0)
    0x00100063,  # beq x0, x1, 4
    0x000002B7,  # lui x5, 0x2
    0x0000006F,  # jal x0, 0
]
simulator.run(instructions)
simulator.dump_registers()
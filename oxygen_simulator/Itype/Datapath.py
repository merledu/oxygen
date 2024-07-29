class RISCVSimulator:
    def __init__(self):
        self.registers = [0] * 32
        self.pc = 0
        self.memory = {}
        self.instruction_memory = {}
        self.pipeline = [None] * 5  # To store pipeline stages
        self.cycle = 0

    def load_instructions(self, instructions):
        for i, instruction in enumerate(instructions):
            self.instruction_memory[i * 4] = instruction
            
    def fetch(self):
        if self.pc in self.instruction_memory:
            self.pipeline[0] = self.instruction_memory[self.pc]
            self.pc += 4
        else:
            self.pipeline[0] = None

    def decode(self):
        self.pipeline[1] = self.pipeline[0]

    def execute_instruction(self, instruction):
        opcode = instruction & 0x7F
        if opcode == 0x33:  # Rtype 
            self.execute_r_type(instruction)
            self.pc+=4
        elif opcode == 0x13:  # Itype
            self.execute_i_type(instruction)
            self.pc+=4
        elif opcode == 0x23:  # Stype 
            self.execute_s_type(instruction)
            self.pc+=4
        elif opcode == 0x63:  # Btype
            self.execute_b_type(instruction)
        elif opcode == 0x37:  # Utype 
            self.execute_u_type(instruction)
        elif opcode == 0x6F:  # Jtype 
            self.execute_j_type(instruction)
        self.pipeline[2] = self.pipeline[1]

    def memory_access(self):
        self.pipeline[3] = self.pipeline[2]

    def write_back(self):
        self.pipeline[4] = self.pipeline[3]

    def cycle_pipeline(self):
        self.write_back()
        self.memory_access()
        self.execute()
        self.decode()
        self.fetch()
        self.cycle += 1
        
    def execute_r_type(self, instruction):
        
        funct7 = (instruction >> 25) & 0x7F
        rs2 = (instruction >> 20) & 0x1F
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F
        
        # ADD 
        if funct3 == 0x0 and funct7 == 0x00:
            self.registers[rd] = self.registers[rs1] + self.registers[rs2]
        # SUB 
        elif funct3 == 0x0 and funct7 == 0x20:
            self.registers[rd] = self.registers[rs1] - self.registers[rs2]
        # SLL 
        elif funct3 == 0x1 and funct7 == 0x00:
            self.registers[rd] = self.registers[rs1] << self.registers[rs2]
        # SLT 
        elif funct3 == 0x2 and funct7 == 0x00:
            self.registers[rd] = 1 if self.registers[rs1] < self.registers[rs2] else 0
        # SLTU 
        elif funct3 == 0x3 and funct7 == 0x00:
            self.registers[rd] = 1 if self.registers[rs1] < self.registers[rs2] else 0
        # XOR 
        elif funct3 == 0x4 and funct7 == 0x00:
            self.registers[rd] = self.registers[rs1] ^ self.registers[rs2]
        # SRL 
        elif funct3 == 0x5 and funct7 == 0x00:
            self.registers[rd] = self.registers[rs1] >> self.registers[rs2]
        # SRA 
        elif funct3 == 0x5 and funct7 == 0x20:
            self.registers[rd] = self.registers[rs1] >> self.registers[rs2]
        # OR 
        elif funct3 == 0x6 and funct7 == 0x00:
            self.registers[rd] = self.registers[rs1] | self.registers[rs2]
        # AND 
        elif funct3 == 0x7 and funct7 == 0x00:
            self.registers[rd] = self.registers[rs1] & self.registers[rs2]

        

    def execute_i_type(self, instruction):
        
        imm = (instruction >> 20) & 0xFFF
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F
 
        # ADDI
        if funct3 == 0x0:
            self.registers[rd] = self.registers[rs1] + self.sign_extend(imm, 12)
        # SLLI
        elif funct3 == 0x1:
            self.registers[rd] = self.registers[rs1] << self.sign_extend(imm, 12)
        # SLTI
        elif funct3 == 0x2:
            self.registers[rd] = 1 if self.registers[rs1] < self.sign_extend(imm, 12) else 0
        # SLTIU
        elif funct3 == 0x3:
            self.registers[rd] = 1 if self.registers[rs1] < self.sign_extend(imm, 12) else 0
        # XORI
        elif funct3 == 0x4:
            self.registers[rd] = self.registers[rs1] ^ self.sign_extend(imm, 12)
        # SRLI
        elif funct3 == 0x5:
            self.registers[rd] = self.registers[rs1] >> self.sign_extend(imm, 12)
        # SRAI
        elif funct3 == 0x5 and imm & 0x400 == 0x400:
            self.registers[rd] = self.registers[rs1] >> self.sign_extend(imm, 12)
        # ORI
        elif funct3 == 0x6:
            self.registers[rd] = self.registers[rs1] | self.sign_extend(imm, 12)
        # ANDI
        elif funct3 == 0x7:
            self.registers[rd] = self.registers[rs1] & self.sign_extend(imm, 12)
        # JALR
        elif opcode == 0x67:
            self.registers[rd] = self.pc + 4
            self.pc = (self.registers[rs1] + self.sign_extend(imm, 12)) & 0xFFFFFFFE
        # LB
        elif funct3 == 0x0 and opcode == 0x3:
            self.registers[rd] = self.sign_extend(self.memory[self.registers[rs1] + self.sign_extend(imm, 12)], 8)
        # LH
        elif funct3 == 0x1 and opcode == 0x3:
            self.registers[rd] = self.sign_extend(self.memory[self.registers[rs1] + self.sign_extend(imm, 12)] << 8 | self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 1], 16)
        # LW
        elif funct3 == 0x2 and opcode == 0x3:
            self.registers[rd] = self.memory[self.registers[rs1] + self.sign_extend(imm, 12)] << 24 | self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 1] << 16 | self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 2] << 8 | self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 3]
        # LBU
        elif funct3 == 0x4 and opcode == 0x3:
            self.registers[rd] = self.memory[self.registers[rs1] + self.sign_extend(imm, 12)]
        # LHU
        elif funct3 == 0x5 and opcode == 0x3:
            self.registers[rd] = self.memory[self.registers[rs1] + self.sign_extend(imm, 12)] << 8 | self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 1]

    def execute_s_type(self, instruction):
        
        imm = ((instruction >> 25) << 5) | ((instruction >> 7) & 0x1F)
        rs2 = (instruction >> 20) & 0x1F
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        opcode = instruction & 0x7F

        
        # SB
        if funct3 == 0x0:
            self.memory[self.registers[rs1] + self.sign_extend(imm, 12)] = self.registers[rs2] & 0xFF
        # SH
        elif funct3 == 0x1:
            self.memory[self.registers[rs1] + self.sign_extend(imm, 12)] = self.registers[rs2] & 0xFF
            self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 1] = (self.registers[rs2] >> 8) & 0xFF
        # SW
        elif funct3 == 0x2:
            self.memory[self.registers[rs1] + self.sign_extend(imm, 12)] = self.registers[rs2] & 0xFF
            self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 1] = (self.registers[rs2] >> 8) & 0xFF
            self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 2] = (self.registers[rs2] >> 16) & 0xFF
            self.memory[self.registers[rs1] + self.sign_extend(imm, 12) + 3] = (self.registers[rs2] >> 24) & 0xFF
        
            

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
                self.pc += self.sign_extend(imm, 13)  
            else:
                self.pc += 4
                
        # BNE
        elif funct3 == 0x1:
            if self.registers[rs1] != self.registers[rs2]:
                self.pc += self.sign_extend(imm, 13) 
            else:
                self.pc += 4
        # BLT
        elif funct3 == 0x4:
            if self.registers[rs1] < self.registers[rs2]:
                self.pc += self.sign_extend(imm, 13) 
            else:
                self.pc += 4
        # BGE
        elif funct3 == 0x5:
            if self.registers[rs1] >= self.registers[rs2]:
                self.pc += self.sign_extend(imm, 13) 
            else:
                self.pc += 4
        # BLTU
        elif funct3 == 0x6:
            if self.registers[rs1] < self.registers[rs2]:
                self.pc += self.sign_extend(imm, 13) 
            else:
                self.pc += 4
        # BGEU
        elif funct3 == 0x7:
            if self.registers[rs1] >= self.registers[rs2]:
                self.pc += self.sign_extend(imm, 13)
            else:
                self.pc += 4 

    def execute_u_type(self, instruction):
       
        imm = instruction & 0xFFFFF000
        rd = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F

            # LUI
        if opcode == 0x37:
            self.registers[rd] = imm
        # AUIPC
        elif opcode == 0x17:
            self.registers[rd] = self.pc + imm
        

    def execute_j_type(self, instruction):
        
        imm = ((instruction >> 31) << 20) | (((instruction >> 21) & 0x3FF) << 1) | \
              (((instruction >> 20) & 0x1) << 11) | (((instruction >> 12) & 0xFF) << 12)
        rd = (instruction >> 7) & 0x1F
        opcode = instruction & 0x7F

        # JAL
        if opcode == 0x6F:
            self.registers[rd] = self.pc + 4
            self.pc += self.sign_extend(imm, 21)  # increment after execution
        
        

    def sign_extend(self, value, bits):
        # imm ka signextend
        if (value >> (bits - 1)) & 1:
            value -= 1 << bits
        return value

    def run(self, instructions):
        instructions = instructions.split('\n')
        instructions = list(filter(('').__ne__, instructions))
        for i in range(len(instructions)):
            hex_int = int(instructions[i], 16)
            instructions[i]=hex_int
            
        self.load_instructions(instructions)
        while self.pc < len(instructions) * 4:
            instruction = self.instruction_memory[self.pc]
            self.execute_instruction(instruction)
        
        return self.registers

    def dump_registers(self):
        # register values ye main pa bhejna
        for i in range(32):
            print(f"x{i}: {hex(self.registers[i])}")


simulator = RISCVSimulator()
instructions = """
00100093
00500113
00208663
00108093
ff9ff06f
00000013
"""
print(simulator.run(instructions))

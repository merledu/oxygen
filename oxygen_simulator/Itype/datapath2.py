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

    def run(self, instructions):
        instructions = instructions.split('\n')
        instructions = list(filter(('').__ne__, instructions))
        for i in range(len(instructions)):
            hex_int = int(instructions[i], 16)
            instructions[i] = hex_int
            
        self.load_instructions(instructions)
        while self.pc < len(instructions) * 4:
            self.cycle_pipeline()
        
        return self.registers

    def dump_registers(self):
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
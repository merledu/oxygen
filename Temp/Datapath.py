import math

class RISCVSimulator:
    def __init__(self):
        self.registers = [0] * 32
        self.pc = 0
        self.memory = {}
        self.instruction_memory = {}
        self.instruction_memory = {}
        self.f_registers = [0.0] * 32 
        # Vector registers: 32 registers, each is a list of bytes (or ints). 
        # Assuming VLEN=128 bits (16 bytes) for simulation.
        self.v_registers = [[0]*16 for _ in range(32)]
        self.VLEN = 128 # bits
        self.ELEN = 8 # Element width in bits (default 8 for vle8.v)

    def load_instructions(self, instructions):
        current_addr = 0
        for instruction in instructions:
            # instruction is an integer
            # Determine length based on value range or just store it?
            # If it's > 0xFFFF, it's 32-bit. But what if it's a small 32-bit instruction?
            # Actually, RISC-V 32-bit instructions always have lower 2 bits = 11.
            # 16-bit instructions have lower 2 bits != 11.
            
            if (instruction & 0x3) == 0x3:
                length = 4
            else:
                length = 2
            
            self.instruction_memory[current_addr] = (instruction, length)
            current_addr += length
            
    def execute_instruction(self, instruction_info):
        instruction, length = instruction_info
        self.registers[0]=0
        
        # Check for Compressed
        if length == 2:
            self.execute_c_type(instruction)
            self.pc += 2
            self.registers[0]=0
            return


        opcode = instruction & 0x7F
        if opcode == 0x33:  # Rtype 
            self.execute_r_type(instruction)
            self.pc+=4
        elif opcode == 0x13 or opcode == 0x3:  # Itype
            self.execute_i_type(instruction)
            self.pc+=4
        elif opcode == 0x23:  # Stype 
            self.execute_s_type(instruction)
            self.pc+=4
        elif opcode == 0x63:  # Btype
            self.execute_b_type(instruction)
        elif opcode == 0x37:  # Utype 
            self.execute_u_type(instruction)
            self.pc+=4
        elif opcode == 0x6F:  # Jtype 
            self.execute_j_type(instruction)
        elif opcode == 0x43:  # Mtype
            self.execute_m_type(instruction)
            self.pc+=4
        elif opcode == 0x67:  # Ftype
            self.execute_f_type(instruction)
            self.pc+=4
        elif opcode == 0x53: # Ftype / Dtype
             self.execute_f_d_type(instruction)
             self.pc+=4
        elif opcode == 0x07: # FLW / FLD
             self.execute_f_d_load(instruction)
             self.pc+=4
        elif opcode == 0x27: # FSW / FSD
             self.execute_f_d_store(instruction)
             self.pc+=4
        elif opcode == 0x57: # Vtype
             self.execute_v_type(instruction)
             self.pc+=4
        elif opcode == 0x73: # System (ecall, ebreak)
             self.execute_system_type(instruction)
             self.pc+=4
        elif opcode == 0x0F: # Fence
             self.execute_fence_type(instruction)
             self.pc+=4
        else:
             print(f"Error: Unknown opcode {hex(opcode)} at PC {self.pc}")
             raise ValueError(f"Unknown opcode {hex(opcode)}")
        
        self.registers[0]=0

    def execute_c_type(self, instruction):
        # Decode Compressed Instruction
        opcode = instruction & 0x3
        funct3 = (instruction >> 13) & 0x7
        
        if opcode == 0: # Quadrant 0
            if funct3 == 0: # c.addi4spn
                rd = ((instruction >> 2) & 0x7) + 8
                imm = ((instruction >> 5) & 0x1) << 3 | ((instruction >> 6) & 0x1) << 2 | \
                      ((instruction >> 7) & 0xF) << 6 | ((instruction >> 11) & 0x3) << 4
                if imm == 0: raise ValueError("c.addi4spn imm=0")
                self.registers[rd] = self.registers[2] + imm
            elif funct3 == 2: # c.lw
                rs1 = ((instruction >> 7) & 0x7) + 8
                rd = ((instruction >> 2) & 0x7) + 8
                imm = ((instruction >> 6) & 0x1) << 2 | ((instruction >> 10) & 0x7) << 3 | ((instruction >> 5) & 0x1) << 6
                addr = self.registers[rs1] + imm
                self.registers[rd] = self.memory.get(addr, 0) | (self.memory.get(addr+1, 0) << 8) | \
                                     (self.memory.get(addr+2, 0) << 16) | (self.memory.get(addr+3, 0) << 24)
            elif funct3 == 6: # c.sw
                rs1 = ((instruction >> 7) & 0x7) + 8
                rs2 = ((instruction >> 2) & 0x7) + 8
                imm = ((instruction >> 6) & 0x1) << 2 | ((instruction >> 10) & 0x7) << 3 | ((instruction >> 5) & 0x1) << 6
                addr = self.registers[rs1] + imm
                val = self.registers[rs2]
                self.memory[addr] = val & 0xFF
                self.memory[addr+1] = (val >> 8) & 0xFF
                self.memory[addr+2] = (val >> 16) & 0xFF
                self.memory[addr+3] = (val >> 24) & 0xFF
            elif funct3 == 1: # c.fld
                rs1 = ((instruction >> 7) & 0x7) + 8
                rd = ((instruction >> 2) & 0x7) + 8
                imm = ((instruction >> 6) & 0x1) << 3 | ((instruction >> 10) & 0x7) << 4 | ((instruction >> 5) & 0x1) << 7
                addr = self.registers[rs1] + imm
                val = 0
                for i in range(8): val |= self.memory.get(addr+i, 0) << (i*8)
                self.f_registers[rd] = float(val) # Should interpret bits as double
            elif funct3 == 5: # c.fsd
                rs1 = ((instruction >> 7) & 0x7) + 8
                rs2 = ((instruction >> 2) & 0x7) + 8
                imm = ((instruction >> 6) & 0x1) << 3 | ((instruction >> 10) & 0x7) << 4 | ((instruction >> 5) & 0x1) << 7
                addr = self.registers[rs1] + imm
                val = int(self.f_registers[rs2])
                for i in range(8): self.memory[addr+i] = (val >> (i*8)) & 0xFF
            
        elif opcode == 1: # Quadrant 1
            if funct3 == 0: # c.addi
                rd = (instruction >> 7) & 0x1F
                imm = self.sign_extend(((instruction >> 2) & 0x1F) | ((instruction >> 12) & 0x1) << 5, 6)
                if rd != 0: self.registers[rd] += imm
            elif funct3 == 2: # c.li
                rd = (instruction >> 7) & 0x1F
                imm = self.sign_extend(((instruction >> 2) & 0x1F) | ((instruction >> 12) & 0x1) << 5, 6)
                if rd != 0: self.registers[rd] = imm
            elif funct3 == 3: # c.lui / c.addi16sp
                rd = (instruction >> 7) & 0x1F
                imm = self.sign_extend(((instruction >> 2) & 0x1F) | ((instruction >> 12) & 0x1) << 5, 6)
                # Check if rd is 2 (sp) -> c.addi16sp
                if rd == 2:
                    # imm format is different for addi16sp
                    # imm = nzimm[9] | nzimm[4|6|8:7|5] | nzimm[5]
                    # instruction bits: 12 | 6-2
                    # 12 -> 9
                    # 6 -> 4
                    # 5 -> 6
                    # 4-3 -> 8:7
                    # 2 -> 5
                    # Wait, standard encoding:
                    # imm[9] = inst[12]
                    # imm[4] = inst[6]
                    # imm[6] = inst[5]
                    # imm[8:7] = inst[4:3]
                    # imm[5] = inst[2]
                    imm16 = ((instruction >> 12) & 0x1) << 9 | ((instruction >> 6) & 0x1) << 4 | \
                            ((instruction >> 5) & 0x1) << 6 | ((instruction >> 3) & 0x3) << 7 | \
                            ((instruction >> 2) & 0x1) << 5
                    imm16 = self.sign_extend(imm16, 10) * 16 # Scaled by 16? No, bits are 9:4, so *16 is implicit in bit pos?
                    # Actually bits are 9,8,7,6,5,4. So it represents value * 16.
                    # My manual decoding above constructs the value / 16?
                    # bit 9 is at pos 9.
                    # So yes, the value constructed is the immediate.
                    # But wait, sign extension should be on bit 9?
                    # Yes, imm[9] is sign bit.
                    if (imm16 >> 9) & 1: imm16 -= 1024
                    self.registers[2] += imm16
                elif rd != 0: # c.lui
                    # imm is 17:12.
                    # inst[12] -> imm[17]
                    # inst[6:2] -> imm[16:12]
                    imm_lui = ((instruction >> 12) & 0x1) << 17 | ((instruction >> 2) & 0x1F) << 12
                    if (imm_lui >> 17) & 1: imm_lui -= 0x40000 # Sign extend 18 bits? No, LUI loads 20 bits.
                    # c.lui loads nzimm[17:12] into bits 17:12 of rd, sign extends bit 17.
                    # Wait, LUI loads 20 bits U-immediate. c.lui loads non-zero imm into 17:12.
                    # So value is sign_extend(imm, 6) << 12.
                    imm_val = self.sign_extend(((instruction >> 2) & 0x1F) | ((instruction >> 12) & 0x1) << 5, 6)
                    self.registers[rd] = imm_val << 12
            elif funct3 == 4: # ALU ops
                # sub, xor, or, and...
                # funct2 in 11:10
                funct2 = (instruction >> 10) & 0x3
                rd = ((instruction >> 7) & 0x7) + 8
                rs2 = ((instruction >> 2) & 0x7) + 8
                if funct2 == 0: # c.srli
                     shamt = ((instruction >> 2) & 0x1F) | ((instruction >> 12) & 0x1) << 5
                     self.registers[rd] >>= shamt
                elif funct2 == 1: # c.srai
                     shamt = ((instruction >> 2) & 0x1F) | ((instruction >> 12) & 0x1) << 5
                     self.registers[rd] >>= shamt # Python handles signed shift if value is signed?
                     # Need to ensure arithmetic shift behavior if simulating 32-bit words
                elif funct2 == 2: # c.andi
                     imm = self.sign_extend(((instruction >> 2) & 0x1F) | ((instruction >> 12) & 0x1) << 5, 6)
                     self.registers[rd] &= imm
                elif funct2 == 3: # c.sub, c.xor, c.or, c.and
                     # funct1 in 6:5, but instruction format for CA is different.
                     # 100 0 11 xxx 00 xxx 01 (c.sub)
                     # bit 12 is 0.
                     # bit 6:5 is op.
                     op_sub = (instruction >> 5) & 0x3
                     if op_sub == 0: # c.sub
                         self.registers[rd] -= self.registers[rs2]
                     elif op_sub == 1: # c.xor
                         self.registers[rd] ^= self.registers[rs2]
                     elif op_sub == 2: # c.or
                         self.registers[rd] |= self.registers[rs2]
                     elif op_sub == 3: # c.and
                         self.registers[rd] &= self.registers[rs2]
            elif funct3 == 1: # c.jal
                offset = self.sign_extend(((instruction >> 3) & 0x7) << 1 | ((instruction >> 11) & 0x1) << 4 | \
                                          ((instruction >> 2) & 0x1) << 5 | ((instruction >> 7) & 0x1) << 6 | \
                                          ((instruction >> 6) & 0x1) << 7 | ((instruction >> 9) & 0x3) << 8 | \
                                          ((instruction >> 8) & 0x1) << 10 | ((instruction >> 12) & 0x1) << 11, 12)
                self.registers[1] = self.pc + 2
                self.pc += offset
                self.pc -= 2 # Compensate for outer loop increment? No, outer loop adds 2.
                # Wait, if I change PC here, I should handle the return.
                # The caller adds 2. So I should subtract 2 from target?
                # Or better, set PC to target - 2.
                self.pc -= 2 
            elif funct3 == 5: # c.j
                offset = self.sign_extend(((instruction >> 3) & 0x7) << 1 | ((instruction >> 11) & 0x1) << 4 | \
                                          ((instruction >> 2) & 0x1) << 5 | ((instruction >> 7) & 0x1) << 6 | \
                                          ((instruction >> 6) & 0x1) << 7 | ((instruction >> 9) & 0x3) << 8 | \
                                          ((instruction >> 8) & 0x1) << 10 | ((instruction >> 12) & 0x1) << 11, 12)
                self.pc += offset
                self.pc -= 2
            elif funct3 == 6: # c.beqz
                rs1 = ((instruction >> 7) & 0x7) + 8
                offset = self.sign_extend(((instruction >> 3) & 0x3) << 1 | ((instruction >> 10) & 0x3) << 3 | \
                                          ((instruction >> 2) & 0x1) << 5 | ((instruction >> 5) & 0x3) << 6 | \
                                          ((instruction >> 12) & 0x1) << 8, 9)
                if self.registers[rs1] == 0:
                    self.pc += offset
                    self.pc -= 2
            elif funct3 == 7: # c.bnez
                rs1 = ((instruction >> 7) & 0x7) + 8
                offset = self.sign_extend(((instruction >> 3) & 0x3) << 1 | ((instruction >> 10) & 0x3) << 3 | \
                                          ((instruction >> 2) & 0x1) << 5 | ((instruction >> 5) & 0x3) << 6 | \
                                          ((instruction >> 12) & 0x1) << 8, 9)
                if self.registers[rs1] != 0:
                    self.pc += offset
                    self.pc -= 2
            # Add other Q1 instructions
            
        elif opcode == 2: # Quadrant 2
            if funct3 == 0: # c.slli
                rd = (instruction >> 7) & 0x1F
                shamt = ((instruction >> 2) & 0x1F) | ((instruction >> 12) & 0x1) << 5
                if rd != 0: self.registers[rd] <<= shamt
            elif funct3 == 2: # c.lwsp
                rd = (instruction >> 7) & 0x1F
                imm = ((instruction >> 4) & 0x7) << 2 | ((instruction >> 12) & 0x1) << 5 | ((instruction >> 2) & 0x3) << 6
                if rd != 0:
                    addr = self.registers[2] + imm
                    self.registers[rd] = self.memory.get(addr, 0) | (self.memory.get(addr+1, 0) << 8) | \
                                         (self.memory.get(addr+2, 0) << 16) | (self.memory.get(addr+3, 0) << 24)
            elif funct3 == 1: # c.fldsp
                rd = (instruction >> 7) & 0x1F
                imm = ((instruction >> 5) & 0x3) << 3 | ((instruction >> 12) & 0x1) << 5 | ((instruction >> 2) & 0x7) << 6
                addr = self.registers[2] + imm
                val = 0
                for i in range(8): val |= self.memory.get(addr+i, 0) << (i*8)
                self.f_registers[rd] = float(val)
            elif funct3 == 5: # c.fsdsp
                rs2 = (instruction >> 2) & 0x1F
                imm = ((instruction >> 10) & 0x7) << 3 | ((instruction >> 7) & 0x7) << 6
                addr = self.registers[2] + imm
                val = int(self.f_registers[rs2])
                for i in range(8): self.memory[addr+i] = (val >> (i*8)) & 0xFF
            elif funct3 == 4:
                if (instruction >> 12) & 0x1 == 0:
                    if (instruction >> 2) & 0x1F == 0: # c.jr
                        rs1 = (instruction >> 7) & 0x1F
                        if rs1 != 0:
                            self.pc = self.registers[rs1]
                            self.pc -= 2
                    else: # c.mv
                        rd = (instruction >> 7) & 0x1F
                        rs2 = (instruction >> 2) & 0x1F
                        if rd != 0 and rs2 != 0: self.registers[rd] = self.registers[rs2]
                else:
                    if (instruction >> 2) & 0x1F == 0: # c.jalr
                        rs1 = (instruction >> 7) & 0x1F
                        if rs1 != 0:
                            t = self.pc + 2
                            self.pc = self.registers[rs1]
                            self.registers[1] = t
                            self.pc -= 2
                        else: # c.ebreak
                             # print(f"C.EBREAK at PC {self.pc}")
                             pass
                    else: # c.add
                        rd = (instruction >> 7) & 0x1F
                        rs2 = (instruction >> 2) & 0x1F
                        if rd != 0 and rs2 != 0: self.registers[rd] += self.registers[rs2]
            elif funct3 == 6: # c.swsp
                rs2 = (instruction >> 2) & 0x1F
                imm = ((instruction >> 9) & 0xF) << 2 | ((instruction >> 7) & 0x3) << 6
                addr = self.registers[2] + imm
                val = self.registers[rs2]
                self.memory[addr] = val & 0xFF
                self.memory[addr+1] = (val >> 8) & 0xFF
                self.memory[addr+2] = (val >> 16) & 0xFF
                self.memory[addr+3] = (val >> 24) & 0xFF
            # Add other Q2 instructions

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
        # MUL
        elif funct3 == 0x0 and funct7 == 0x01:
            self.registers[rd] = self.registers[rs1] * self.registers[rs2]
        # MULH
        elif funct3 == 0x1 and funct7 == 0x01:
            self.registers[rd] = (self.registers[rs1] * self.registers[rs2]) >> 32
        # MULHU
        elif funct3 == 0x3 and funct7 == 0x01:
            self.registers[rd] = (self.registers[rs1] * self.registers[rs2]) & 0xFFFFFFFF >> 32
        # MULHSU
        elif funct3 == 0x2 and funct7 == 0x01:
            self.registers[rd] = (self.registers[rs1] * self.sign_extend(self.registers[rs2], 32)) >> 32
        # DIV
        elif funct3 == 0x4 and funct7 == 0x01:
            self.registers[rd] = self.registers[rs1] // self.registers[rs2]
        # DIVU
        elif funct3 == 0x5 and funct7 == 0x01:
            self.registers[rd] = self.registers[rs1] // self.registers[rs2]
        # REM
        elif funct3 == 0x6 and funct7 == 0x01:
            self.registers[rd] = self.registers[rs1] % self.registers[rs2]
        # REMU
        elif funct3 == 0x7 and funct7 == 0x01:
            self.registers[rd] = self.registers[rs1] % self.registers[rs2]

    # def execute_m_type(self, instruction):
    # # M-type instructions (e.g., MUL, DIV, REM)
    #     funct7 = (instruction >> 25) & 0x7F
    #     rs2 = (instruction >> 20) & 0x1F
    #     rs1 = (instruction >> 15) & 0x1F
    #     funct3 = (instruction >> 12) & 0x7
    #     rd = (instruction >> 7) & 0x1F
    #     opcode = instruction & 0x7F

            
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
        elif funct3 == 0x2 and opcode == 0x13:
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
        #old 
        # # LB
        # elif funct3 == 0x0 and opcode == 0x3:
        #     address = self.registers[rs1] + self.sign_extend(imm, 12)
        #     self.registers[rd] = self.sign_extend(self.memory.get(address, 0), 8)

        # # LH
        # elif funct3 == 0x1 and opcode == 0x3:
        #     address = self.registers[rs1] + self.sign_extend(imm, 12)
        #     self.registers[rd] = self.sign_extend((self.memory.get(address, 0) << 8 | self.memory.get(address + 1, 0)), 16)

        # # LW
        # elif funct3 == 0x2 and opcode == 0x3:
        #     address = self.registers[rs1] + self.sign_extend(imm, 12)
        #     self.registers[rd] = (
        #         self.memory.get(address, 0) << 24 |
        #         self.memory.get(address + 1, 0) << 16 |
        #         self.memory.get(address + 2, 0) << 8 |
        #         self.memory.get(address + 3, 0)
        #     )

        # # LBU
        # elif funct3 == 0x4 and opcode == 0x3:
        #     address = self.registers[rs1] + self.sign_extend(imm, 12)
        #     self.registers[rd] = self.memory.get(address, 0)

        # # LHU
        # elif funct3 == 0x5 and opcode == 0x3:
        #     address = self.registers[rs1] + self.sign_extend(imm, 12)
        #     self.registers[rd] = self.memory.get(address, 0) << 8 | self.memory.get(address + 1, 0)
        # LB
        elif funct3 == 0x0 and opcode == 0x3:
            print("hello")
            address = self.registers[rs1] + self.sign_extend(imm, 12)
            self.registers[rd] = self.sign_extend(self.memory.get((address), 0), 8)

        # LH
        elif funct3 == 0x1 and opcode == 0x3:
            address = self.registers[rs1] + self.sign_extend(imm, 12)
            self.registers[rd] = self.sign_extend((self.memory.get((address), 0) | self.memory.get((address + 1), 0)<<8),16)

        # LW
        elif funct3 == 0x2 and opcode == 0x3:
            address = self.registers[rs1] + self.sign_extend(imm, 12)
            print("check mem",self.memory.get((address), 0))
            self.registers[rd] = (
                self.memory.get((address), 0) |
                self.memory.get((address+ 1), 0) << 8 |
                self.memory.get((address + 2), 0) << 16 |
                self.memory.get((address + 3), 0) << 24
            )
            
        # LBU
        elif funct3 == 0x4 and opcode == 0x3:
            address = self.registers[rs1] + self.sign_extend(imm, 12)
            self.registers[rd] = self.memory.get((address, 0))

        # LHU
        elif funct3 == 0x5 and opcode == 0x3:
            address = self.registers[rs1] + self.sign_extend(imm, 12)
            self.registers[rd] = self.sign_extend(self.memory.get((address, 0))| self.memory.get((address + 1) << 8, 0),16)
            
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
        
        # FMV
        # ... implement moves if needed

    def execute_system_type(self, instruction):
        # ecall, ebreak
        # For simulation, maybe just print or stop?
        # ecall: environment call. ebreak: debugger break.
        # funct3=0, funct12 determines which one.
        funct3 = (instruction >> 12) & 0x7
        funct12 = (instruction >> 20) & 0xFFF
        
        if funct12 == 0: # ecall
            # System call simulation
            # Check a7 for syscall number?
            # For now, just print
            # print(f"ECALL at PC {self.pc}")
            pass
        elif funct12 == 1: # ebreak
            # print(f"EBREAK at PC {self.pc}")
            pass

    def execute_fence_type(self, instruction):
        # fence, fence.i
        # In a simple sequential simulator, these are NOPs.
        pass

    def execute_v_type(self, instruction):
        # Decode Vector Instruction
        # opcode is 0x57 (1010111) or 0x07 (0000111) for loads?
        # Wait, opcode for V is 0x57 (OP-V).
        # Loads/Stores are 0x07 (LOAD-FP) / 0x27 (STORE-FP) collision?
        # No, Vector Loads are 0x07 (0000111) same as FLW?
        # Actually, standard RISC-V Vector extension uses:
        # LOAD-FP (0x07): FLW, FLD, VLE... distinguished by width/funct3?
        # FLW: funct3=010. FLD: funct3=011.
        # VLE8: funct3=000.
        # So I need to update execute_f_d_load/store to dispatch to vector load/store if funct3 matches.
        
        # But here I am in execute_v_type which handles OP-V (0x57).
        
        funct6 = (instruction >> 26) & 0x3F
        vm = (instruction >> 25) & 0x1
        vs2 = (instruction >> 20) & 0x1F
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        vd = (instruction >> 7) & 0x1F
        
        # OPIVV (funct3=000), OPIVX (funct3=100), OPIVI (funct3=011)
        
        if funct3 == 0x0: # OPIVV
            if funct6 == 0x00: # vadd.vv
                for i in range(16): # Assuming VLEN=128, SEW=8
                    self.v_registers[vd][i] = (self.v_registers[rs1][i] + self.v_registers[vs2][i]) & 0xFF
            elif funct6 == 0x25: # vmul.vv
                 for i in range(16):
                     self.v_registers[vd][i] = (self.v_registers[rs1][i] * self.v_registers[vs2][i]) & 0xFF
                 
        elif funct3 == 0x4: # OPIVX
            if funct6 == 0x00: # vadd.vx
                scalar = self.registers[rs1]
                for i in range(16):
                    self.v_registers[vd][i] = (self.v_registers[vs2][i] + scalar) & 0xFF
                    
        elif funct3 == 0x3: # OPIVI
            if funct6 == 0x00: # vadd.vi
                imm = self.sign_extend(rs1, 5) # rs1 field holds imm
                for i in range(16):
                    self.v_registers[vd][i] = (self.v_registers[vs2][i] + imm) & 0xFF

    def execute_f_d_load(self, instruction):
        imm = (instruction >> 20) & 0xFFF
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd = (instruction >> 7) & 0x1F
        
        addr = self.registers[rs1] + self.sign_extend(imm, 12)
        
        if funct3 == 0x2: # FLW
            val = self.memory.get(addr, 0) | (self.memory.get(addr+1, 0) << 8) | \
                  (self.memory.get(addr+2, 0) << 16) | (self.memory.get(addr+3, 0) << 24)
            self.f_registers[rd] = float(val) 
            
        elif funct3 == 0x3: # FLD
            val = self.memory.get(addr, 0) | (self.memory.get(addr+1, 0) << 8) | \
                  (self.memory.get(addr+2, 0) << 16) | (self.memory.get(addr+3, 0) << 24) | \
                  (self.memory.get(addr+4, 0) << 32) | (self.memory.get(addr+5, 0) << 40) | \
                  (self.memory.get(addr+6, 0) << 48) | (self.memory.get(addr+7, 0) << 56)
            self.f_registers[rd] = float(val)
            
        elif funct3 == 0x0: # VLE8.V
             # Vector Load
             # For simplicity, assume VLEN=128, SEW=8
             for i in range(16):
                 self.v_registers[rd][i] = self.memory.get(addr + i, 0)

    def execute_f_d_store(self, instruction):
        imm = ((instruction >> 25) << 5) | ((instruction >> 7) & 0x1F)
        rs2 = (instruction >> 20) & 0x1F
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        
        addr = self.registers[rs1] + self.sign_extend(imm, 12)
        
        if funct3 == 0x2: # FSW
            val = int(self.f_registers[rs2])
            self.memory[addr] = val & 0xFF
            self.memory[addr+1] = (val >> 8) & 0xFF
            self.memory[addr+2] = (val >> 16) & 0xFF
            self.memory[addr+3] = (val >> 24) & 0xFF
        elif funct3 == 0x3: # FSD
            val = int(self.f_registers[rs2])
            self.memory[addr] = val & 0xFF
            self.memory[addr+1] = (val >> 8) & 0xFF
            self.memory[addr+2] = (val >> 16) & 0xFF
            self.memory[addr+3] = (val >> 24) & 0xFF
            self.memory[addr+4] = (val >> 32) & 0xFF
            self.memory[addr+5] = (val >> 40) & 0xFF
            self.memory[addr+6] = (val >> 48) & 0xFF
            self.memory[addr+7] = (val >> 56) & 0xFF
        elif funct3 == 0x0: # VSE8.V
             # Vector Store
             for i in range(16):
                 self.memory[addr + i] = self.v_registers[rs2][i] & 0xFF

    def execute_f_d_type(self, instruction):
        funct7 = (instruction >> 25) & 0x7F
        rs2 = (instruction >> 20) & 0x1F
        rs1 = (instruction >> 15) & 0x1F
        funct3 = (instruction >> 12) & 0x7
        rd = (instruction >> 7) & 0x1F
        
        # funct7: 5 bits opcode-like + 2 bits fmt.
        # Standard: funct7[6:2] is opcode, funct7[1:0] is fmt.
        # S = 00, D = 01.
        
        fmt = funct7 & 0x3
        op = funct7 >> 2
        
        # Helper to get value based on fmt
        val1 = self.f_registers[rs1]
        val2 = self.f_registers[rs2]
        
        # FADD
        if op == 0x00:
            self.f_registers[rd] = val1 + val2
        # FSUB
        elif op == 0x01:
            self.f_registers[rd] = val1 - val2
        # FMUL
        elif op == 0x02:
            self.f_registers[rd] = val1 * val2
        # FDIV
        elif op == 0x03:
            if val2 != 0:
                self.f_registers[rd] = val1 / val2
            else:
                self.f_registers[rd] = float('inf') # Handle div by zero
        # FSGNJ
        elif op == 0x04:
            if funct3 == 0: # fsgnj
                self.f_registers[rd] = math.copysign(val1, val2)
            elif funct3 == 1: # fsgnjn
                self.f_registers[rd] = math.copysign(val1, -val2)
            elif funct3 == 2: # fsgnjx
                # XOR sign bit. 
                # In python float, this is tricky. 
                # Simplified: if signs are same, result positive, else negative.
                s1 = math.copysign(1.0, val1)
                s2 = math.copysign(1.0, val2)
                self.f_registers[rd] = abs(val1) * (1.0 if s1 == s2 else -1.0)
        # FMIN/FMAX
        elif op == 0x05:
            if funct3 == 0: # fmin
                self.f_registers[rd] = min(val1, val2)
            elif funct3 == 1: # fmax
                self.f_registers[rd] = max(val1, val2)
        # FCVT.S.D / FCVT.D.S
        elif op == 0x08:
            # Conversion between float formats. Python uses double for all, so just copy.
            self.f_registers[rd] = val1
        # FSQRT
        elif op == 0x0B:
            if val1 >= 0:
                self.f_registers[rd] = math.sqrt(val1)
            else:
                self.f_registers[rd] = float('nan')
        # FEQ/FLT/FLE
        elif op == 0x14:
            res = 0
            if funct3 == 0: # feq
                res = 1 if val1 == val2 else 0
            elif funct3 == 1: # flt
                res = 1 if val1 < val2 else 0
            elif funct3 == 2: # fle
                res = 1 if val1 <= val2 else 0
            self.registers[rd] = res
        # FCLASS
        elif op == 0x1C:
            # Simplified fclass
            if math.isinf(val1):
                res = 1 << 0 if val1 < 0 else 1 << 7
            elif math.isnan(val1):
                res = 1 << 9 # qNaN
            elif val1 == 0:
                res = 1 << 3 if math.copysign(1.0, val1) < 0 else 1 << 4
            else:
                res = 1 << 1 if val1 < 0 else 1 << 6 # Normal
            self.registers[rd] = res
        # FCVT.W.S / FCVT.W.D
        elif op == 0x18:
            # Float to Int
            # Check rs2 (which is 00000 for W, 00001 for WU, 00010 for L, 00011 for LU)
            # Actually rs2 field holds the sub-opcode for conversion type in standard?
            # Standard: rs2=0 (W), 1 (WU), 2 (L), 3 (LU)
            if rs2 == 0: # W (32-bit signed)
                self.registers[rd] = int(val1) & 0xFFFFFFFF
                if self.registers[rd] & 0x80000000: self.registers[rd] -= 0x100000000
            elif rs2 == 1: # WU (32-bit unsigned)
                self.registers[rd] = int(val1) & 0xFFFFFFFF
            # Add L/LU if needed (64-bit)
        # FCVT.S.W / FCVT.D.W
        elif op == 0x1A:
            # Int to Float
            # rs2=0 (W), 1 (WU)
            int_val = self.registers[rs1]
            if rs2 == 0: # W
                self.f_registers[rd] = float(int_val)
            elif rs2 == 1: # WU
                self.f_registers[rd] = float(int_val & 0xFFFFFFFF)
        # FMV.X.W / FMV.X.D
        elif op == 0x1C and funct3 == 0:
             # Move float bits to int register
             # Python floats are doubles. 
             # For W (32-bit), we might need struct pack/unpack or just cast if we don't care about bit exactness for now.
             # But FMV.X.W moves bits.
             # Let's assume simple value move for simulation unless bit manipulation is required.
             self.registers[rd] = int(val1) 
        # FMV.W.X / FMV.D.X
        elif op == 0x1E and funct3 == 0:
             # Move int bits to float register
             self.f_registers[rd] = float(self.registers[rs1])

    def sign_extend(self, value, bits):
        # imm ka signextend
        if (value >> (bits - 1)) & 1:
            value -= 1 << bits
        return value

    def run(self, instructions):
        try:
            instructions = instructions.split('\n')
            instructions = list(filter(('').__ne__, instructions))
            parsed_instructions = []
            for i in range(len(instructions)):
                line = instructions[i].strip()
                if not line: continue
                if line.startswith('Error'):
                     print(line)
                     return []
                hex_int = int(line, 16)
                parsed_instructions.append(hex_int)
                
            self.load_instructions(parsed_instructions)
            
            # Calculate total size
            total_size = 0
            for inst in parsed_instructions:
                 if (inst & 0x3) == 0x3: total_size += 4
                 else: total_size += 2

            while self.pc < total_size:
                if self.pc not in self.instruction_memory:
                    break
                instruction_info = self.instruction_memory[self.pc]
                self.execute_instruction(instruction_info)
            return self.registers
        except Exception as e:
            print(f"Runtime Error: {str(e)}")
            return []
    

    def dump_registers(self):
        # register values ye main pa bhejna
        for i in range(32):
            print(f"x{i}: {hex(self.registers[i])}")
    
    def memory_dump(self):
        return self.memory



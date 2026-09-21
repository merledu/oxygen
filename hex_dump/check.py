import asyncio
import re
import time
from pexpect import EOF, TIMEOUT, spawn


ABI_REG_MAP = {
    'zero': 0, 'ra': 1, 'sp': 2, 'gp': 3, 'tp': 4,
    't0': 5, 't1': 6, 't2': 7, 's0': 8, 'fp': 8, 's1': 9,
    'a0': 10, 'a1': 11, 'a2': 12, 'a3': 13, 'a4': 14, 'a5': 15,
    'a6': 16, 'a7': 17, 's2': 18, 's3': 19, 's4': 20, 's5': 21,
    's6': 22, 's7': 23, 's8': 24, 's9': 25, 's10': 26, 's11': 27,
    't3': 28, 't4': 29, 't5': 30, 't6': 31
}

ABI_FREG_LIST = [
    'ft0', 'ft1', 'ft2', 'ft3', 'ft4', 'ft5', 'ft6', 'ft7',
    'fs0', 'fs1', 'fa0', 'fa1', 'fa2', 'fa3', 'fa4', 'fa5',
    'fa6', 'fa7', 'fs2', 'fs3', 'fs4', 'fs5', 'fs6', 'fs7',
    'fs8', 'fs9', 'fs10', 'fs11', 'ft8', 'ft9', 'ft10', 'ft11'
]
ABI_FREG_MAP = {name: i for i, name in enumerate(ABI_FREG_LIST)}
for i in range(32):
    ABI_FREG_MAP[f'f{i}'] = i

PROMPT_PATTERNS = [r'\r\n\(spike\)', TIMEOUT, EOF]


class Simulator:
    def __init__(self):
        self.spike_process = None
        self.vtype = False
        self.ftype = False
        self.dtype = False
        self.last_accessed = time.time()
        self.pc = 0x80000000
        self.registers = [0] * 32
        self.f_registers = [0.0] * 32
        self.d_registers = [0.0] * 32
        self.f_hex = ["0x0000000000000000"] * 32
        self.v_registers = [[0, 0] for _ in range(32)]
        self.vreg_elements = {
            '8': [[0] * 16 for _ in range(32)],
            '16': [[0] * 8 for _ in range(32)],
            '32': [[0] * 4 for _ in range(32)],
            '64': [[0] * 2 for _ in range(32)],
        }
        self.vector_status = {
            'vl': 0,
            'sew': 32,
            'lmul': 'm1',
            'vta': 'ta',
            'vma': 'ma'
        }
        self.memory = {}
        self.is_ended = False
        self.is_completed = False
        self.last_error = ""
        self.end_pc = None
        self.user_tmp = None
        self.lock = asyncio.Lock()

    def is_process_alive(self):
        return bool(self.spike_process and self.spike_process.isalive())

    def is_alive(self):
        return bool(self.is_process_alive() and not self.is_ended)

    def terminate(self):
        """Terminate the running Spike process and clean up."""
        if self.spike_process:
            try:
                self.spike_process.terminate(force=True)
                self.spike_process.close()
            except Exception:
                pass
            self.spike_process = None
        self.is_ended = True

    def _sync_start(self, command, setup_steps):
        self.spike_process = spawn(command, timeout=5)
        time.sleep(0.05)

        # Wait for initial prompt
        try:
            self.spike_process.expect([r'\r\n\(spike\)', r'\(spike\)', TIMEOUT, EOF])
        except Exception:
            self.is_ended = True
            return False

        # Step through the 5 bootrom instructions (0x1000 -> 0x1010)
        # plus any setup instructions (e.g. enabling mstatus.FS/VS)
        for _ in range(5 + setup_steps):
            self.spike_process.sendline('')
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx != 0:
                self.is_ended = True
                return False
            raw_output = self.spike_process.before.decode('utf-8', errors='replace')
            step_match = re.search(r'core\s+\d+:\s*(0x[0-9a-fA-F]+)', raw_output)
            if step_match:
                self.pc = int(step_match.group(1), 16)

        # Initialize register state
        self._sync_get_registers()
        return True

    async def start(self, command, vtype=False, ftype=False, dtype=False, setup_steps=0, end_pc=None, user_tmp=None):
        self.terminate()
        self.vtype = bool(vtype)
        self.ftype = bool(ftype or dtype)
        self.dtype = bool(dtype)
        self.last_accessed = time.time()
        self.pc = 0x80000000
        self.registers = [0] * 32
        self.f_registers = [0.0] * 32
        self.d_registers = [0.0] * 32
        self.f_hex = ["0x0000000000000000"] * 32
        self.v_registers = [[0, 0] for _ in range(32)]
        self.vreg_elements = {
            '8': [[0] * 16 for _ in range(32)],
            '16': [[0] * 8 for _ in range(32)],
            '32': [[0] * 4 for _ in range(32)],
            '64': [[0] * 2 for _ in range(32)],
        }
        self.vector_status = {
            'vl': 0,
            'sew': 32,
            'lmul': 'm1',
            'vta': 'ta',
            'vma': 'ma'
        }
        self.memory = {}
        self.is_ended = False
        self.is_completed = False
        self.last_error = ""
        self.end_pc = end_pc
        self.user_tmp = user_tmp

        await asyncio.to_thread(self._sync_start, command, setup_steps)

    def _sync_step(self):
        self.last_accessed = time.time()
        if not self.is_alive():
            return "Simulation ended"

        self.spike_process.sendline('')
        try:
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx != 0:
                self.is_ended = True
                return "Simulation ended"

            raw_output = self.spike_process.before.decode('utf-8', errors='replace').strip()
            # Check for explicit CPU traps
            trap_match = re.search(r'exception\s+(trap_[a-z_]+),\s*epc\s+(0x[0-9a-fA-F]+)', raw_output)
            if trap_match:
                trap_name = trap_match.group(1)
                epc_str = trap_match.group(2)
                epc_int = int(epc_str, 16)
                tval_match = re.search(r'tval\s+(0x[0-9a-fA-F]+)', raw_output)
                tval = tval_match.group(1) if tval_match else "0x0"
                self.is_ended = True

                # Check if this is normal end-of-program termination:
                # 1) Instruction executed was c.unimp / unimp
                # 2) epc reached or exceeded the end of the user's instructions
                is_normal_exit = (
                    trap_name == "trap_illegal_instruction" and (
                        "c.unimp" in raw_output or
                        "unimp" in raw_output or
                        (self.end_pc is not None and epc_int >= self.end_pc)
                    )
                )

                if is_normal_exit:
                    self.is_completed = True
                    self.last_error = ""
                    return "Program completed"

                if trap_name in ("trap_store_access_fault", "trap_load_access_fault"):
                    self.last_error = f"CPU Trap ({trap_name}): Access fault at address {tval}. In RISC-V hardware, address 0x0 is unmapped. RAM begins at 0x80000000. Use e.g. 'lui t0, 0x80001' before storing."
                elif trap_name == "trap_illegal_instruction":
                    self.last_error = f"CPU Trap ({trap_name}): Illegal instruction at {epc_str}."
                else:
                    self.last_error = f"CPU Trap ({trap_name}) at {epc_str}, tval={tval}."
                return "Simulation ended"

            if "trap_illegal_instruction" in raw_output or "trap_instruction_access_fault" in raw_output:
                self.is_ended = True
                if "c.unimp" in raw_output or "unimp" in raw_output:
                    self.is_completed = True
                    self.last_error = ""
                    return "Program completed"
                self.last_error = "CPU Trap: Execution halted."
                return "Simulation ended"

            # Parse core instruction line: core 0: <pc> (<hex>) <disasm>
            step_match = re.search(r'core\s+\d+:\s*(0x[0-9a-fA-F]+)\s*\((0x[0-9a-fA-F]+)\)\s*(.*)', raw_output)
            current_disasm = ""
            if step_match:
                exec_pc = int(step_match.group(1), 16)
                hex_inst = step_match.group(2)
                current_disasm = step_match.group(3).strip()
                self.pc = exec_pc
                if self.end_pc is not None and exec_pc >= self.end_pc:
                    self.is_completed = True

            # Update integer registers
            self._sync_get_registers()

            # 1. Check for memory store instructions (sb, sh, sw, sd, fsw, fsd, c.sw, c.sd)
            # Fast-path: check if --log-commits already printed the written address & value
            log_mem_match = re.search(r'\bmem\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)', raw_output)
            if log_mem_match:
                self._record_memory_write(log_mem_match.group(1), log_mem_match.group(2))
            else:
                store_match = re.search(r'\b(s[wbh]|c\.sw|c\.swsp|sd|c\.sd|c\.sdsp|fsw|fsd)\s+(\w+),\s*(-?\d+)\((\w+)\)', current_disasm)
                if store_match:
                    offset = int(store_match.group(3))
                    base_reg_name = store_match.group(4)
                    base_idx = ABI_REG_MAP.get(base_reg_name.lower(), -1)
                    if base_idx == -1 and base_reg_name.startswith('x'):
                        try:
                            base_idx = int(base_reg_name[1:])
                        except ValueError:
                            base_idx = -1

                    if 0 <= base_idx < 32:
                        target_addr = self.registers[base_idx] + offset
                        mem_val = self._sync_get_memory(hex(target_addr))
                        if mem_val:
                            self._record_memory_write(hex(target_addr), mem_val)

            # 2. Check for floating point update (Single or Double)
            if self.ftype:
                fp_match = re.search(r'\b(f[a-z\.]+|c\.flw|c\.fsd|c\.fld|c\.fsw)\s+([a-z0-9]+)', current_disasm)
                if fp_match:
                    fp_reg_name = fp_match.group(2).lower()
                    fp_idx = ABI_FREG_MAP.get(fp_reg_name, -1)
                    if 0 <= fp_idx < 32:
                        is_double_op = (
                            self.dtype or
                            '.d' in current_disasm or
                            'fld' in current_disasm or
                            'fsd' in current_disasm
                        )
                        if is_double_op:
                            d_val, h_val = self._sync_get_dregister(fp_idx)
                            self.d_registers[fp_idx] = d_val
                            self.f_registers[fp_idx] = float(d_val)
                            self.f_hex[fp_idx] = h_val
                        else:
                            f_val, h_val = self._sync_get_fregister(fp_idx)
                            self.f_registers[fp_idx] = f_val
                            self.d_registers[fp_idx] = float(f_val)
                            self.f_hex[fp_idx] = h_val

            # 3. Check for Vector CSR update (vsetvli / vsetivli)
            if self.vtype:
                vset_match = re.search(r'vset[i]?vli\s+(\w+),\s*(\w+),\s*(e\d+),\s*([m\d/]+)', current_disasm)
                if vset_match:
                    rd_name = vset_match.group(1).lower()
                    sew_str = vset_match.group(3)
                    lmul_str = vset_match.group(4)
                    rd_idx = ABI_REG_MAP.get(rd_name, -1)
                    if rd_idx == -1 and rd_name.startswith('x'):
                        try:
                            rd_idx = int(rd_name[1:])
                        except ValueError:
                            rd_idx = -1

                    if 0 <= rd_idx < 32:
                        self.vector_status['vl'] = self.registers[rd_idx]
                    self.vector_status['sew'] = int(sew_str[1:])
                    self.vector_status['lmul'] = lmul_str

                self._sync_get_registers_vtype()

            return current_disasm or raw_output

        except (EOF, TIMEOUT):
            self.is_ended = True
            return "Simulation ended"

    async def step(self):
        return await asyncio.to_thread(self._sync_step)

    def _sync_get_registers(self):
        if not self.is_process_alive():
            return self.registers

        self.spike_process.sendline('reg 0')
        try:
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx == 0:
                reg_output = self.spike_process.before.decode('utf-8', errors='replace')
                matches = re.findall(r'(\w+):\s+(0x[0-9a-fA-F]+)', reg_output)
                for reg_name, hex_val in matches:
                    idx_num = ABI_REG_MAP.get(reg_name.lower())
                    if idx_num is not None and 0 <= idx_num < 32:
                        self.registers[idx_num] = int(hex_val, 16)
                    elif reg_name.startswith('x'):
                        try:
                            num = int(reg_name[1:])
                            if 0 <= num < 32:
                                self.registers[num] = int(hex_val, 16)
                        except ValueError:
                            pass
                self.registers[0] = 0
            return self.registers
        except (EOF, TIMEOUT):
            return self.registers

    async def get_registers(self):
        return await asyncio.to_thread(self._sync_get_registers)

    def _sync_get_fregister(self, reg_num):
        if not self.is_process_alive() or not (0 <= reg_num < 32):
            return 0.0, "0x0000000000000000"
        abi_name = ABI_FREG_LIST[reg_num]

        # 1. Single precision float value
        self.spike_process.sendline(f'fregs 0 {abi_name}')
        f_val = 0.0
        try:
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx == 0:
                out = self.spike_process.before.decode('utf-8', errors='replace')
                last_line = out.splitlines()[-1].strip() if out.splitlines() else ""
                try:
                    f_val = float(last_line)
                except ValueError:
                    f_val = 0.0
        except (EOF, TIMEOUT):
            pass

        # 2. Raw 64-bit hex
        self.spike_process.sendline(f'freg 0 {abi_name}')
        h_val = "0x0000000000000000"
        try:
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx == 0:
                out = self.spike_process.before.decode('utf-8', errors='replace')
                last_line = out.splitlines()[-1].strip() if out.splitlines() else ""
                if last_line.startswith("0x"):
                    h_val = last_line
        except (EOF, TIMEOUT):
            pass

        return f_val, h_val

    async def get_fregister(self, reg_num):
        return await asyncio.to_thread(self._sync_get_fregister, reg_num)

    def _sync_get_dregister(self, reg_num):
        if not self.is_process_alive() or not (0 <= reg_num < 32):
            return 0.0, "0x0000000000000000"
        abi_name = ABI_FREG_LIST[reg_num]

        # 1. Double precision float value
        self.spike_process.sendline(f'fregd 0 {abi_name}')
        d_val = 0.0
        try:
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx == 0:
                out = self.spike_process.before.decode('utf-8', errors='replace')
                last_line = out.splitlines()[-1].strip() if out.splitlines() else ""
                try:
                    d_val = float(last_line)
                except ValueError:
                    d_val = 0.0
        except (EOF, TIMEOUT):
            pass

        # 2. Raw 64-bit hex
        self.spike_process.sendline(f'freg 0 {abi_name}')
        h_val = "0x0000000000000000"
        try:
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx == 0:
                out = self.spike_process.before.decode('utf-8', errors='replace')
                last_line = out.splitlines()[-1].strip() if out.splitlines() else ""
                if last_line.startswith("0x"):
                    h_val = last_line
        except (EOF, TIMEOUT):
            pass

        return d_val, h_val

    async def get_dregister(self, reg_num):
        return await asyncio.to_thread(self._sync_get_dregister, reg_num)

    def _sync_get_registers_vtype(self):
        if not self.is_process_alive():
            return self.v_registers

        self.spike_process.sendline('vreg 0')
        try:
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx == 0:
                raw_output = self.spike_process.before.decode('utf-8', errors='replace')
                reg_pattern = re.compile(r'v(\d+)\s*:\s*(?:\[1\]:\s*([0-9xa-fA-F]+))\s*\[0\]:\s*([0-9xa-fA-F]+)')
                for line in raw_output.splitlines():
                    match = reg_pattern.search(line)
                    if match:
                        num = int(match.group(1))
                        if 0 <= num < 32:
                            val1 = int(match.group(2), 16)
                            val0 = int(match.group(3), 16)
                            self.v_registers[num] = [val0, val1]

                            # 64-bit elements (2 per register)
                            self.vreg_elements['64'][num] = [val0, val1]
                            # 32-bit elements (4 per register)
                            self.vreg_elements['32'][num] = [
                                val0 & 0xFFFFFFFF,
                                (val0 >> 32) & 0xFFFFFFFF,
                                val1 & 0xFFFFFFFF,
                                (val1 >> 32) & 0xFFFFFFFF,
                            ]
                            # 16-bit elements (8 per register)
                            self.vreg_elements['16'][num] = [
                                (val0 >> (16 * i)) & 0xFFFF for i in range(4)
                            ] + [
                                (val1 >> (16 * i)) & 0xFFFF for i in range(4)
                            ]
                            # 8-bit elements (16 per register)
                            self.vreg_elements['8'][num] = [
                                (val0 >> (8 * i)) & 0xFF for i in range(8)
                            ] + [
                                (val1 >> (8 * i)) & 0xFF for i in range(8)
                            ]
            return self.v_registers
        except (EOF, TIMEOUT):
            return self.v_registers

    async def get_registers_vtype(self):
        return await asyncio.to_thread(self._sync_get_registers_vtype)

    def _sync_get_memory(self, addr):
        if not self.is_process_alive():
            return None
        try:
            addr_int = int(str(addr), 16) if str(addr).startswith('0x') else int(str(addr))
            if addr_int < 0x1000:
                return None
        except ValueError:
            return None
        self.spike_process.sendline(f'mem {addr}')
        try:
            idx = self.spike_process.expect(PROMPT_PATTERNS)
            if idx == 0:
                out = self.spike_process.before.decode('utf-8', errors='replace')
                last_line = out.splitlines()[-1].strip() if out.splitlines() else ""
                if re.match(r'^0x[0-9a-fA-F]+$', last_line):
                    return last_line
            return None
        except (EOF, TIMEOUT):
            return None

    async def get_memory(self, addr):
        return await asyncio.to_thread(self._sync_get_memory, addr)

    def _record_memory_write(self, addr_str, val_str):
        try:
            addr = int(str(addr_str), 16) if str(addr_str).startswith('0x') else int(str(addr_str))
            val_hex = str(val_str).lower().replace('0x', '')
            if len(val_hex) % 2 != 0:
                val_hex = '0' + val_hex
            num_bytes = len(val_hex) // 2
            for b in range(num_bytes):
                byte_hex = val_hex[len(val_hex) - 2 * (b + 1) : len(val_hex) - 2 * b]
                byte_addr = addr + b
                self.memory[f"0x{byte_addr:x}"] = byte_hex.lower()
        except Exception:
            self.memory[str(addr_str).lower()] = str(val_str).lower()

    def _sync_run(self, target_pc=None, max_steps=5000):
        self.last_accessed = time.time()
        if not self.is_alive():
            return self.registers

        steps = 0
        while self.is_alive() and steps < max_steps:
            self.spike_process.sendline('')
            try:
                idx = self.spike_process.expect(PROMPT_PATTERNS)
                if idx != 0:
                    self.is_ended = True
                    break

                raw_output = self.spike_process.before.decode('utf-8', errors='replace').strip()

                # Check for explicit CPU traps
                trap_match = re.search(r'exception\s+(trap_[a-z_]+),\s*epc\s+(0x[0-9a-fA-F]+)', raw_output)
                if trap_match:
                    trap_name = trap_match.group(1)
                    epc_str = trap_match.group(2)
                    epc_int = int(epc_str, 16)
                    self.is_ended = True

                    is_normal_exit = (
                        trap_name == "trap_illegal_instruction" and (
                            "c.unimp" in raw_output or
                            "unimp" in raw_output or
                            (self.end_pc is not None and epc_int >= self.end_pc)
                        )
                    )
                    if is_normal_exit:
                        self.is_completed = True
                        self.last_error = ""
                    else:
                        self.last_error = f"CPU Trap ({trap_name})"
                    break

                if "trap_illegal_instruction" in raw_output or "trap_instruction_access_fault" in raw_output:
                    self.is_ended = True
                    if "c.unimp" in raw_output or "unimp" in raw_output:
                        self.is_completed = True
                        self.last_error = ""
                    else:
                        self.last_error = "CPU Trap: Execution halted."
                    break

                # Parse PC
                step_match = re.search(r'core\s+\d+:\s*(0x[0-9a-fA-F]+)', raw_output)
                if step_match:
                    exec_pc = int(step_match.group(1), 16)
                    self.pc = exec_pc
                    if self.end_pc is not None and exec_pc >= self.end_pc:
                        self.is_completed = True

                # Parse register commit from --log-commits
                for m in re.finditer(r'\b(x\d+)\s+(0x[0-9a-fA-F]+)', raw_output):
                    reg_num = int(m.group(1)[1:])
                    if 0 < reg_num < 32:
                        self.registers[reg_num] = int(m.group(2), 16)

                # Parse memory commit from --log-commits
                for mem_match in re.finditer(r'\bmem\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)', raw_output):
                    self._record_memory_write(mem_match.group(1), mem_match.group(2))

                steps += 1

                if target_pc is not None and self.pc == target_pc:
                    break

                if self.is_completed:
                    break

            except (EOF, TIMEOUT):
                self.is_ended = True
                break

        # Sync all registers from Spike once at completion
        if self.is_process_alive():
            self._sync_get_registers()

        if self.vtype and self.is_process_alive():
            self._sync_get_registers_vtype()

        return self.registers

    async def run(self, target_pc=None, max_steps=5000):
        return await asyncio.to_thread(self._sync_run, target_pc, max_steps)
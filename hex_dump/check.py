import asyncio
import re
from pexpect import EOF, TIMEOUT, spawn
from globals import SPIKE,TMP_ELF

class Simulator:
    def __init__(self):
        self.spike_process = None
    
    def parse_registers(input_str):
    # Use regex to extract register names and values
        pattern = r'(\w+):\s+(0x[0-9a-fA-F]+)'
        matches = re.findall(pattern, input_str)

        # Create a dictionary with register names as keys and values as values
        register_dict = [int(value, 16) for _, value in matches]
        return register_dict

    async def start(self , command):
        if self.spike_process:
            self.terminate()  # Terminate the previous process if it's running
        # command = f'{SPIKE+"/spike"} -d --isa=rv32im {TMP_ELF}'
        self.spike_process = spawn(command)
        await asyncio.sleep(0.1)
        # Clear initial output
        self.spike_process.expect(['(spike)', TIMEOUT, EOF])
        await self.step()
        await self.step()
        await self.step()
        await self.step()
        await self.step()

    def terminate(self):
        """Terminate the current Spike process if it is running."""
        if self.spike_process:
            self.spike_process.terminate(force=True)  # Terminate the running process
            self.spike_process = None

    async def step(self):
        if not self.spike_process:
            return "Simulator not started"
        
        self.spike_process.sendline('')
        try:
            index = self.spike_process.expect(['(spike)', TIMEOUT, EOF])
            if index == 0:  # Matched '(spike)'
                output = self.spike_process.before.decode('utf-8').strip()
                return output
            elif index == 1:  # TIMEOUT
                return "Timeout occurred"
            else:  # EOF
                return "Simulation ended"
        except EOF:
            return "Simulation ended unexpectedly"

    async def get_registers(self):
        if not self.spike_process:
            return "Simulator not started"
        
        self.spike_process.sendline('reg 0')
        try:
            register_pattern = r'zero:.*\n(.*\n){7}\(spike\)'
            index = self.spike_process.expect([register_pattern, TIMEOUT, EOF])
            if index == 0:  # Matched '(spike)'
                output = self.spike_process.after.decode('utf-8').strip()
                return (output)
            elif index == 1:  # TIMEOUT
                return "Timeout occurred"
            else:  # EOF
                return "Simulation ended"
        except EOF:
            return "Simulation ended unexpectedly"

    async def get_registers_vtype(self):
        if not self.spike_process:
            return "Simulator not started"
        
        self.spike_process.sendline('vreg 0')
        # Get the output
        try:
        # Capture output until next (spike) prompt
            vector_pattern = r'VLEN=.*?(?=\(spike\))'
            
            index = self.spike_process.expect([vector_pattern, TIMEOUT, EOF])
            if index == 0:
                
                raw_output = self.spike_process.after.decode('utf-8').strip()
                raw_output = raw_output.replace("(spike)", "").strip()

                lines = raw_output.splitlines()
                result = {}

                # First line contains VLEN and ELEN
                header_match = re.search(r'VLEN=(\d+) bits; ELEN=(\d+) bits', lines[0])
                if header_match:
                    result["VLEN"] = int(header_match.group(1))
                    result["ELEN"] = int(header_match.group(2))

                # Parse each vector register line
                vector_registers = {}
                reg_pattern = re.compile(r'v(\d+)\s*:\s*(?:\[1\]:\s*([0-9xa-fA-F]+))\s*\[0\]:\s*([0-9xa-fA-F]+)')
                for line in lines[1:]:
                    match = reg_pattern.search(line)
                    if match:
                        reg_num = f"v{match.group(1)}"
                        val1 = match.group(2)
                        val0 = match.group(3)
                        vector_registers[reg_num] = [val1, val0]

                result["vector_registers"] = vector_registers
                print(result)
                return result
            elif index == 1:  
                return {"error": "Timeout occurred"}
            else:  
                return {"error": "Simulation ended"}
        except EOF:
            return {"error": "Simulation ended unexpectedly"}
        
        
    async def get_memory(self,addr):
        if not self.spike_process:
            return "Simulator not started"
        
        self.spike_process.sendline(f'mem {addr}')
        try:
            hex_pattern = r'\b0[xX][0-9a-fA-F]+\b'
            index = self.spike_process.expect([hex_pattern, TIMEOUT, EOF])
            if index == 0:  # Matched '(spike)'
                print('regix matched')
                output = self.spike_process.after.decode('utf-8').strip()
                # print(output)
                return (output)
            elif index == 1:  # TIMEOUT
                return "Timeout occurred"
            else:  # EOF
                return "Simulation ended"
        except EOF:
            return "Simulation ended unexpectedly"
        
            
import asyncio
import re

from pexpect import EOF, TIMEOUT, spawn


class Simulator:
    def __init__(self):
        self.spike_process = None

    async def start(self):
        command = '/home/abdulrehman/Desktop/oxygen/tools/spike/bin/spike -d --isa=rv32im /home/abdulrehman/Desktop/oxygen/tools/spike/bin/elf'
        self.spike_process = spawn(command)
        await asyncio.sleep(0.1)
        # Clear initial output
        self.spike_process.expect(['(spike)', TIMEOUT, EOF])

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
                return output
            elif index == 1:  # TIMEOUT
                return "Timeout occurred"
            else:  # EOF
                return "Simulation ended"
        except EOF:
            return "Simulation ended unexpectedly"
def parse_registers(input_str):
    # Use regex to extract register names and values
    pattern = r'(\w+):\s+(0x[0-9a-fA-F]+)'
    matches = re.findall(pattern, input_str)

    # Create a dictionary with register names as keys and values as values
    register_dict = [int(value, 16) for _, value in matches]

    return register_dict
async def main():
    simulator = Simulator()
    await simulator.start()
    
    while True:
        command = input("Enter command (step/reg/quit): ").strip().lower()
        if command == 'step':
            result = await simulator.step()
            # print(result)
            if ('c.unimp' in result):
                print('execution ended')
                break
            result = await simulator.get_registers()
            result = parse_registers(result)
            print(result)
        elif command == 'reg':
            result = await simulator.get_registers()
            print(result)
        elif command == 'quit':
            break
        else:
            print("Unknown command. Use 'step', 'reg', or 'quit'.")

if __name__ == "__main__":
    asyncio.run(main())
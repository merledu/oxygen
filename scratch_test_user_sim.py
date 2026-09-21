import os, sys, asyncio, re, subprocess
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxygen.settings')
import django; django.setup()
import globals
from hex_dump.check import Simulator

async def test():
    elf = '/dev/shm/oxygen_tmp/ucathl1hxsbwfp4l3vupd90qov09x5vn/elf'
    objdump = os.path.join(globals.RISCV32_GNU_TOOLCHAIN, 'riscv32-unknown-elf-objdump')
    res = subprocess.run([objdump, '-M', 'no-aliases', '-d', elf], capture_output=True, text=True)
    decoded = []
    for line in res.stdout.splitlines():
        m = re.match(r'^\s*([0-9a-fA-F]+):\s+([0-9a-fA-F]+)\s+(.*)', line)
        if m:
            decoded.append({'pc': f'0x{int(m.group(1), 16):08x}', 'disasm': m.group(3)})
    print('Decoded instructions count:', len(decoded), flush=True)
    setup_steps = 3
    user_decoded = decoded[setup_steps:]
    end_pc = int(user_decoded[-1]['pc'], 16)
    print('end_pc:', hex(end_pc), flush=True)

    sim = Simulator()
    spike_bin = os.path.join(globals.SPIKE, 'spike')
    spike_cmd = f'{spike_bin} -d --log-commits --isa=rv32imfdcv {elf}'
    await sim.start(spike_cmd, vtype=True, ftype=True, dtype=True, setup_steps=setup_steps, end_pc=end_pc)
    print('After start, pc:', hex(sim.pc), 'registers:', sim.registers[:8], flush=True)
    res_run = await sim.run()
    print('After run, pc:', hex(sim.pc), flush=True)
    print('Registers:', sim.registers[:8], flush=True)
    print('Is alive:', sim.is_alive(), 'is completed:', sim.is_completed, flush=True)

asyncio.run(test())

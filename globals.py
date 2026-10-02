import os, logging


# Paths
HOME = os.environ['HOME']


OXYGEN_ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(OXYGEN_ROOT, 'tools')
RISCV32_GNU_TOOLCHAIN = os.path.join(TOOLS, 'riscv32-gnu-toolchain', 'bin')
RISCV64_GNU_TOOLCHAIN = os.path.join(TOOLS, 'riscv64-gnu-toolchain', 'bin')
SPIKE = os.path.join(TOOLS, 'spike', 'bin')
TMP = '/dev/shm/oxygen_tmp' if (os.path.exists('/dev/shm') and os.access('/dev/shm', os.W_OK)) else os.path.join(OXYGEN_ROOT, 'tmp')
os.makedirs(TMP, exist_ok=True)
TMP_ASM = os.path.join(TMP, 'asm.S')
TMP_DISASM = os.path.join(TMP, 'disasm.S')
TMP_ELF = os.path.join(TMP, 'elf')
LINKER_SCRIPT = os.path.join(OXYGEN_ROOT,"l.ld")


os.environ['PATH'] = SPIKE \
    + os.pathsep + RISCV64_GNU_TOOLCHAIN \
    + os.pathsep + RISCV32_GNU_TOOLCHAIN \
    + os.pathsep + os.environ['PATH']

if 'LD_LIBRARY_PATH' in os.environ:
    # Prevent legacy EDA tool library paths (e.g., Vivado 2018.2 libstdc++) from conflicting with Spike/GCC
    _clean_ld = [p for p in os.environ['LD_LIBRARY_PATH'].split(os.pathsep) if 'vivado' not in p.lower()]
    os.environ['LD_LIBRARY_PATH'] = os.pathsep.join(_clean_ld)


# Global Variables
debug = True
loglevel = logging.DEBUG if debug else logging.INFO
windows = {}
configs = {}
stderr = {}
testlist = []
code = ''
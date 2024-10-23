import os, logging


# Paths
HOME = os.environ['HOME']


OXYGEN_ROOT = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(OXYGEN_ROOT, 'tools')
RISCV32_GNU_TOOLCHAIN = os.path.join(TOOLS, 'riscv32-gnu-toolchain', 'bin')
RISCV64_GNU_TOOLCHAIN = os.path.join(TOOLS, 'riscv64-gnu-toolchain', 'bin')
SPIKE = os.path.join(TOOLS, 'spike', 'bin')
TMP = os.path.join(OXYGEN_ROOT, 'tmp')
TMP_ASM = os.path.join(TMP, 'asm.S')
TMP_DISASM = os.path.join(TMP, 'disasm.S')
TMP_ELF = os.path.join(TMP, 'elf')
LINKER_SCRIPT = os.path.join(RISCV32_GNU_TOOLCHAIN, 'link.ld')


os.environ['PATH'] = SPIKE \
    + os.pathsep + RISCV64_GNU_TOOLCHAIN \
    + os.pathsep + RISCV32_GNU_TOOLCHAIN \
    + os.pathsep + os.environ['PATH']


# Global Variables
debug = True
loglevel = logging.DEBUG if debug else logging.INFO
windows = {}
configs = {}
stderr = {}
testlist = []
code = ''
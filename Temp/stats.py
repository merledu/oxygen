"""
RISC-V instruction statistics counter.
Single-pass O(n) implementation — previously did 7 separate passes over the same lines.
"""

import re

# Pre-compiled: matches the first mnemonic token on a line (ignores labels, comments, blank lines)
_MNEMONIC_RE = re.compile(r'^\s*([a-zA-Z][a-zA-Z0-9_.]*)')

# Instruction classification sets (first-token exact match)
_I_OPS = frozenset([
    'add', 'addi', 'sub', 'lui', 'auipc', 'xor', 'xori', 'or', 'ori', 'and', 'andi',
    'slt', 'slti', 'sltu', 'sltiu', 'beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu',
    'jal', 'jalr', 'lb', 'lh', 'lw', 'lbu', 'lhu', 'sb', 'sh', 'sw',
    'sll', 'slli', 'srl', 'srli', 'sra', 'srai', 'li', 'fence', 'ecall', 'ebreak',
    # RV64I
    'addiw', 'slliw', 'srliw', 'sraiw', 'addw', 'subw', 'sllw', 'srlw', 'sraw',
    'lwu', 'ld', 'sd',
])

_M_OPS = frozenset([
    'mul', 'mulh', 'mulhsu', 'mulhu', 'div', 'divu', 'rem', 'remu',
    # RV64M
    'mulw', 'divw', 'divuw', 'remw', 'remuw',
])

_F_OPS = frozenset([
    'flw', 'fsw', 'fld', 'fsd',
    'fadd.s', 'fsub.s', 'fmul.s', 'fdiv.s', 'fsqrt.s',
    'fadd.d', 'fsub.d', 'fmul.d', 'fdiv.d', 'fsqrt.d',
    'fmadd.s', 'fmsub.s', 'fnmsub.s', 'fnmadd.s',
    'fmadd.d', 'fmsub.d', 'fnmsub.d', 'fnmadd.d',
    'fsgnj.s', 'fsgnjn.s', 'fsgnjx.s', 'fsgnj.d', 'fsgnjn.d', 'fsgnjx.d',
    'fmin.s', 'fmax.s', 'fmin.d', 'fmax.d',
    'feq.s', 'flt.s', 'fle.s', 'feq.d', 'flt.d', 'fle.d',
    'fclass.s', 'fclass.d',
    'fcvt.w.s', 'fcvt.wu.s', 'fcvt.s.w', 'fcvt.s.wu',
    'fcvt.w.d', 'fcvt.wu.d', 'fcvt.d.w', 'fcvt.d.wu',
    'fcvt.l.s', 'fcvt.lu.s', 'fcvt.s.l', 'fcvt.s.lu',
    'fcvt.l.d', 'fcvt.lu.d', 'fcvt.d.l', 'fcvt.d.lu',
    'fcvt.d.s', 'fcvt.s.d',
    'fmv.x.w', 'fmv.w.x', 'fmv.x.d', 'fmv.d.x',
])

_ALU_OPS = frozenset([
    'add', 'addi', 'sub', 'xor', 'xori', 'or', 'ori', 'and', 'andi',
    'sll', 'slli', 'srl', 'srli', 'sra', 'srai', 'slt', 'slti', 'sltu', 'sltiu',
    'lui', 'auipc', 'li',
    'mul', 'mulh', 'mulhsu', 'mulhu', 'div', 'divu', 'rem', 'remu',
    # RV64
    'addiw', 'slliw', 'srliw', 'sraiw', 'addw', 'subw', 'sllw', 'srlw', 'sraw',
    'mulw', 'divw', 'divuw', 'remw', 'remuw',
])

_LOAD_STORE_OPS = frozenset([
    'lb', 'lh', 'lw', 'lbu', 'lhu', 'sb', 'sh', 'sw',
    'flw', 'fsw', 'fld', 'fsd',
    # RV64
    'lwu', 'ld', 'sd',
])

_JUMP_OPS = frozenset([
    'beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu', 'jal', 'jalr', 'j', 'jr', 'ret', 'call', 'tail',
])

_UPPER_OPS = frozenset(['lui', 'auipc'])


def get_instruction_stats(code: str):
    """
    Single O(n) pass over all lines — counts all instruction categories simultaneously.
    Returns: (total, jump, data_transfer, alu, i_ext, m_ext, upper, f_ext, c_ext)
    """
    total = jump = data_transfer = alu = i_ext = m_ext = upper = f_ext = c_ext = 0

    for raw_line in code.splitlines():
        line = raw_line.strip()
        # Skip blank lines, pure comments, and label-only lines
        if not line or line.startswith('#') or (line.endswith(':') and ' ' not in line):
            continue

        m = _MNEMONIC_RE.match(line)
        if not m:
            continue

        mnem = m.group(1).lower()

        # Skip labels that appear inline (e.g. "loop: addi x1, x0, 1")
        if mnem.endswith(':'):
            rest = line[m.end():].strip()
            m2 = _MNEMONIC_RE.match(rest)
            if not m2:
                continue
            mnem = m2.group(1).lower()

        total += 1

        if mnem in _JUMP_OPS:
            jump += 1
        if mnem in _LOAD_STORE_OPS:
            data_transfer += 1
        if mnem in _ALU_OPS:
            alu += 1
        if mnem in _I_OPS:
            i_ext += 1
        if mnem in _M_OPS:
            m_ext += 1
        if mnem in _UPPER_OPS:
            upper += 1
        if mnem in _F_OPS:
            f_ext += 1
        if mnem.startswith('c.') or mnem.startswith('c_'):
            c_ext += 1

    total_cycles = total  # Approximate: 1 cycle per instruction (CPI=1)

    return total, jump, data_transfer, alu, i_ext, m_ext, upper, f_ext, c_ext

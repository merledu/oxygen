import hashlib
import json
import os
import re
import subprocess
import tempfile
import globals
from django.http import JsonResponse
from django.shortcuts import render
from Temp import Datapath_single as DPS
from Temp import interperator as IP

_itype_compilation_cache = {}


def editor(request):
    return render(request, 'index.html')


def testpage(request):
    return render(request, 'index_test.html')


class AssemblyException(Exception):
    def __init__(self, line, msg):
        super().__init__(msg)
        self.line = line
        self.msg = msg


def parse_assembler_error(error_str, offset=0):
    match = re.search(r":(\d+):\s*Error:\s*(.*)", error_str, re.IGNORECASE)
    if match:
        line_num = max(1, int(match.group(1)) - offset)
        return line_num, match.group(2).strip()
    ld_match = re.search(r":(\d+):(?:\([^)]+\))?:\s*(.+)", error_str)
    if ld_match:
        line_num = max(1, int(ld_match.group(1)) - offset)
        return line_num, ld_match.group(2).strip()
    return None, error_str.strip()


def normalize_pc_relative_targets(code):
    """
    Normalizes numeric branch and jump offsets in RISC-V assembly.
    In GNU as, writing `beq x1, x2, 8` treats `8` as absolute symbol 0x8 (triggering
    relocation truncation when linked at 0x80000000). Prepending `.` makes it PC-relative: `.+8`.
    Labels (e.g. `loop`, `.L1`) are preserved unchanged.
    """
    def fix_branch(match):
        op = match.group(1)
        r1 = match.group(2)
        r2 = match.group(3)
        target = match.group(4).strip()
        if re.match(r'^[+-]?(?:0x[0-9a-fA-F]+|\d+)$', target):
            sign = '+' if not target.startswith('-') and not target.startswith('+') else ''
            return f"{op} {r1}, {r2}, .{sign}{target}"
        return match.group(0)

    def fix_jal(match):
        op = match.group(1)
        rest = match.group(2).strip()
        parts = [p.strip() for p in rest.split(',')]
        target = parts[-1]
        if re.match(r'^[+-]?(?:0x[0-9a-fA-F]+|\d+)$', target):
            sign = '+' if not target.startswith('-') and not target.startswith('+') else ''
            parts[-1] = f".{sign}{target}"
            return f"{op} {', '.join(parts)}"
        return match.group(0)

    code = re.sub(r'\b(beq|bne|blt|bge|bltu|bgeu)\s+([a-zA-Z0-9_]+)\s*,\s*([a-zA-Z0-9_]+)\s*,\s*([^#\n\r]+)', fix_branch, code, flags=re.IGNORECASE)
    code = re.sub(r'\b(jal|j)\s+([^#\n\r]+)', fix_jal, code, flags=re.IGNORECASE)
    return code


def compile_and_disassemble(code, mtype='', ctype='', ftype='', dtype='', vtype='', rvtype='rv32'):
    """
    Safely compiles and disassembles RISC-V assembly using an isolated temporary directory.
    Thread-safe, multi-tenant, and never modifies the process working directory.
    """
    code = normalize_pc_relative_targets(code)
    canon_order = ['m', 'a', 'f', 'd', 'c', 'v']
    enabled = set()
    for ext_flag in (mtype, ctype, ftype, dtype, vtype):
        val = str(ext_flag).lower().strip()
        if val in canon_order:
            enabled.add(val)
    if 'd' in enabled:
        enabled.add('f')

    ext_suffix = "".join([x for x in canon_order if x in enabled])
    isa_ext = "i" + ext_suffix

    if rvtype == "rv64":
        toolchain_bin = globals.RISCV64_GNU_TOOLCHAIN
        prefix = "riscv64-unknown-elf"
        march = f"rv64{isa_ext}"
        if 'd' in isa_ext:
            abi = "lp64d"
        elif 'f' in isa_ext:
            abi = "lp64f"
        else:
            abi = "lp64"
    else:
        toolchain_bin = globals.RISCV32_GNU_TOOLCHAIN
        prefix = "riscv32-unknown-elf"
        march = f"rv32{isa_ext}"
        if 'd' in isa_ext:
            abi = "ilp32d"
        elif 'f' in isa_ext:
            abi = "ilp32f"
        else:
            abi = "ilp32"

    gcc_cmd = os.path.join(toolchain_bin, f"{prefix}-gcc")
    objdump_cmd = os.path.join(toolchain_bin, f"{prefix}-objdump")

    has_start = "_start" in code or "main:" in code
    if not has_start:
        prepended = ".globl _start\n_start:\n"
        full_code = prepended + code + "\n"
        line_offset = 2
    else:
        full_code = code + "\n"
        line_offset = 0

    cache_key = hashlib.sha256(f"{code}:{march}:{abi}".encode('utf-8')).hexdigest()
    if cache_key in _itype_compilation_cache:
        cached = _itype_compilation_cache[cache_key]
        return cached['hex'], cached['instructions']

    with tempfile.TemporaryDirectory() as td:
        asm_path = os.path.join(td, "code.S")
        elf_path = os.path.join(td, "code.elf")

        with open(asm_path, "w") as f:
            f.write(full_code)

        gcc_args = [
            gcc_cmd,
            f"-march={march}",
            f"-mabi={abi}",
            "-T", globals.LINKER_SCRIPT,
            "-static",
            "-mcmodel=medany",
            "-fvisibility=hidden",
            "-nostdlib",
            "-nostartfiles",
            "-g",
            "-o", elf_path,
            asm_path,
        ]

        assemble_res = subprocess.run(gcc_args, capture_output=True, text=True)
        if assemble_res.returncode != 0:
            line, msg = parse_assembler_error(assemble_res.stderr, offset=line_offset)
            raise AssemblyException(line, msg or assemble_res.stderr)

        objdump_args = [objdump_cmd, "-M", "no-aliases", "-d", elf_path]
        objdump_res = subprocess.run(objdump_args, capture_output=True, text=True)
        if objdump_res.returncode != 0:
            raise ValueError(f"Disassembly Error: {objdump_res.stderr}")

        decoded_instructions = []
        for line in objdump_res.stdout.splitlines():
            m = re.match(r'^\s*([0-9a-fA-F]+):\s+([0-9a-fA-F]+)\s+(.*)', line)
            if m:
                inst_pc = int(m.group(1), 16)
                inst_hex = m.group(2).strip().lower()
                inst_disasm = m.group(3).strip()
                decoded_instructions.append({
                    'pc': f"0x{inst_pc:08x}",
                    'hex': f"0x{inst_hex}",
                    'disasm': inst_disasm
                })

        hex_lines = [item['hex'] for item in decoded_instructions]
        hex_output = "\n".join(hex_lines)

        if len(_itype_compilation_cache) > 200:
            _itype_compilation_cache.pop(next(iter(_itype_compilation_cache)))
        _itype_compilation_cache[cache_key] = {
            'hex': hex_output,
            'instructions': decoded_instructions
        }

        return hex_output, decoded_instructions


def get_hex_gcc(code, mtype='', ctype='', ftype='', dtype='', vtype='', rvtype='rv32'):
    return compile_and_disassemble(code, mtype, ctype, ftype, dtype, vtype, rvtype)


def assemble_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            mtype = data.get('mtype', '')
            ctype = data.get('ctype', '')
            ftype = data.get('ftype', '')
            dtype = data.get('dtype', '')
            vtype = data.get('vtype', '')
            rvtype = data.get('rvtype', 'rv32')

            try:
                sudo_or_base = IP.checkpsudo(code)
            except Exception:
                sudo_or_base = [line.strip() for line in code.splitlines() if line.strip() and not line.strip().endswith(':')]

            hex_output, decoded_instructions = get_hex_gcc(code, mtype, ctype, ftype, dtype, vtype, rvtype)
            return JsonResponse({
                'hex': hex_output,
                'is_sudo': sudo_or_base,
                'instructions': decoded_instructions,
                'success': True
            })
        except AssemblyException as e:
            return JsonResponse({
                'success': False,
                'error_message': e.msg,
                'error_line': e.line if e.line is not None else 'unknown'
            })
        except ValueError as e:
            err_msg = str(e)
            line, msg = parse_assembler_error(err_msg)
            return JsonResponse({
                'success': False,
                'error_message': msg or err_msg,
                'error_line': line if line is not None else 'unknown'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error_message': str(e),
                'error_line': 'unknown'
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)


def step_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            instruction = data.get('instruction', '')
            pc = data.get('pc', 0)
            memory = data.get('memory', {})
            register = data.get('register', [0] * 32)
            fregister = data.get('f_register', [0.0] * 32)
            vreg = data.get('vreg', [[0] * 16 for _ in range(32)])

            # Create stateless simulator instance per request
            sim = DPS.RISCVSimulatorSingle()
            try:
                sim.pc = int(pc)
            except (ValueError, TypeError):
                sim.pc = 0

            sim.memory = dict(memory) if isinstance(memory, dict) else {}
            sim.registers = list(register) if isinstance(register, list) and len(register) == 32 else [0] * 32
            sim.f_registers = list(fregister) if isinstance(fregister, list) and len(fregister) == 32 else [0.0] * 32
            sim.v_registers = list(vreg) if isinstance(vreg, list) and len(vreg) == 32 else [[0] * 16 for _ in range(32)]

            is_ended = False
            if instruction:
                # Instruction can be e.g. "0x00a00093" or "00a00093"
                clean_hex = instruction.strip().lower()
                if not clean_hex.startswith("0x"):
                    clean_hex = "0x" + clean_hex
                sim.run(clean_hex)
            else:
                is_ended = True

            return JsonResponse({
                'memory': sim.memory,
                'register': sim.registers,
                'pc': sim.pc,
                'f_reg': sim.f_registers,
                'vreg': sim.v_registers,
                'ended': is_ended,
                'message': 'Program execution completed.' if is_ended else '',
                'success': True
            })
        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


def run_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            mtype = data.get('mtype', '')
            ctype = data.get('ctype', '')
            ftype = data.get('ftype', '')
            dtype = data.get('dtype', '')
            vtype = data.get('vtype', '')
            rvtype = data.get('rvtype', 'rv32')

            hex_output, _ = get_hex_gcc(code, mtype, ctype, ftype, dtype, vtype, rvtype)
            try:
                sudo_or_base = IP.checkpsudo(code)
            except Exception:
                sudo_or_base = [line.strip() for line in code.splitlines() if line.strip() and not line.strip().endswith(':')]

            hex_lines = [h.strip() for h in hex_output.splitlines() if h.strip()]

            sim = DPS.RISCVSimulatorSingle()
            # Execute all instructions
            max_cycles = 10000
            cycles = 0
            for h in hex_lines:
                clean_hex = h if h.startswith("0x") else f"0x{h}"
                sim.run(clean_hex)
                cycles += 1
                if cycles >= max_cycles:
                    break

            return JsonResponse({
                'hex': hex_output,
                'is_sudo': sudo_or_base,
                'registers': sim.registers,
                'memory': sim.memory,
                'f_reg': sim.f_registers,
                'vreg': sim.v_registers,
                'pc': sim.pc,
                'ended': True,
                'message': 'Program execution completed.',
                'success': True
            })
        except Exception as e:
            return JsonResponse({'error': str(e), 'success': False}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)


def reset(request):
    if request.method == "POST":
        return JsonResponse({
            'register': [0] * 32,
            'memory': {},
            'pc': 0,
            'fregister': [0.0] * 32,
            'vreg': [[0] * 16 for _ in range(32)],
            'success': True
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)
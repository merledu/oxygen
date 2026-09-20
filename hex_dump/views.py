import asyncio
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import time
from asgiref.sync import sync_to_async
from django.http import JsonResponse
import globals
from Temp import interperator as IP
from .check import Simulator

# High-capacity thread pool executor for 100s of concurrent users
executor = concurrent.futures.ThreadPoolExecutor(max_workers=256)

# Active simulators keyed by session_key
session_simulators = {}
_cleanup_task = None


async def _periodic_cleanup_loop():
    """Background task to regularly prune idle simulators and clean temporary files."""
    while True:
        try:
            await asyncio.sleep(60)
            cleanup_idle_simulators()
        except asyncio.CancelledError:
            break
        except Exception:
            pass


def ensure_background_cleanup():
    """Ensures that the threadpool executor and periodic cleanup task are running."""
    global _cleanup_task
    try:
        loop = asyncio.get_running_loop()
        if not getattr(loop, '_has_oxygen_executor', False):
            loop.set_default_executor(executor)
            loop._has_oxygen_executor = True
        if _cleanup_task is None or _cleanup_task.done():
            _cleanup_task = loop.create_task(_periodic_cleanup_loop())
    except RuntimeError:
        pass


def cleanup_idle_simulators():
    """Terminate and prune simulators idle for more than 5 minutes or terminated, and clean disk."""
    now = time.time()
    to_delete = []
    for sk, sim in list(session_simulators.items()):
        if not sim.is_alive() or (now - sim.last_accessed > 300):
            try:
                sim.terminate()
            except Exception:
                pass
            user_tmp = os.path.join(globals.TMP, sk)
            if os.path.exists(user_tmp):
                try:
                    shutil.rmtree(user_tmp, ignore_errors=True)
                except Exception:
                    pass
            to_delete.append(sk)
    for sk in to_delete:
        session_simulators.pop(sk, None)

    # Purge any orphaned temporary directories older than 1 hour
    try:
        if os.path.exists(globals.TMP):
            for entry in os.listdir(globals.TMP):
                path = os.path.join(globals.TMP, entry)
                if os.path.isdir(path) and entry not in session_simulators:
                    mtime = os.path.getmtime(path)
                    if now - mtime > 3600:
                        shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


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


def sanitize_isa(rvtype, mtype, ctype, ftype, dtype, vtype):
    canon_order = ['m', 'a', 'f', 'd', 'c', 'v']
    enabled = set()
    for ext_flag in (mtype, ctype, ftype, dtype, vtype):
        val = str(ext_flag).lower().strip()
        if val in canon_order:
            enabled.add(val)
    if 'd' in enabled:
        enabled.add('f')

    ext_suffix = "".join([x for x in canon_order if x in enabled])
    valid_rv = "rv64" if str(rvtype).lower() == "rv64" else "rv32"
    isa_str = f"{valid_rv}i{ext_suffix}"
    return isa_str, valid_rv, ext_suffix


async def assemble_code(request):
    ensure_background_cleanup()
    await sync_to_async(request.session.save)()
    session_key = request.session.session_key
    if not session_key:
        await sync_to_async(request.session.save)()
        session_key = request.session.session_key

    cleanup_idle_simulators()

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

            code = normalize_pc_relative_targets(code)

            isa_str, valid_rv, extensions = sanitize_isa(rvtype, mtype, ctype, ftype, dtype, vtype)
            isa_str = f"{valid_rv}i{extensions}"

            # User temp directory isolated per session
            user_tmp = os.path.join(globals.TMP, session_key)
            os.makedirs(user_tmp, exist_ok=True)
            tmp_asm = os.path.join(user_tmp, 'asm.S')
            tmp_elf = os.path.join(user_tmp, 'elf')
            tmp_disasm = os.path.join(user_tmp, 'disasm.S')

            setup_steps = 0
            has_start = "_start" in code or "main:" in code
            if not has_start:
                if 'f' in extensions or 'd' in extensions or 'v' in extensions:
                    # Enable FP (FS=11) and Vector (VS=11) in mstatus: 0x6600
                    full_code = f".globl _start\n_start:\n  lui t0, 0x6\n  addi t0, t0, 1536\n  csrs mstatus, t0\n{code}\n"
                    offset = 5
                    setup_steps = 3
                else:
                    full_code = f".globl _start\n_start:\n{code}\n"
                    offset = 2
            else:
                full_code = code + "\n"
                offset = 0

            with open(tmp_asm, 'w') as f:
                f.write(full_code)

            if valid_rv == "rv64":
                toolchain_bin = globals.RISCV64_GNU_TOOLCHAIN
                prefix = "riscv64-unknown-elf"
                if 'd' in extensions:
                    abi = "lp64d"
                elif 'f' in extensions:
                    abi = "lp64f"
                else:
                    abi = "lp64"
            else:
                toolchain_bin = globals.RISCV32_GNU_TOOLCHAIN
                prefix = "riscv32-unknown-elf"
                if 'd' in extensions:
                    abi = "ilp32d"
                elif 'f' in extensions:
                    abi = "ilp32f"
                else:
                    abi = "ilp32"

            gcc_cmd = os.path.join(toolchain_bin, f"{prefix}-gcc")
            objdump_cmd = os.path.join(toolchain_bin, f"{prefix}-objdump")

            assemble_cmd = [
                gcc_cmd,
                f"-march={isa_str}",
                f"-mabi={abi}",
                "-T", globals.LINKER_SCRIPT,
                "-static",
                "-mcmodel=medany",
                "-fvisibility=hidden",
                "-nostdlib",
                "-nostartfiles",
                "-g",
                "-o", tmp_elf,
                tmp_asm
            ]

            assemble_result = await asyncio.to_thread(subprocess.run, assemble_cmd, capture_output=True, text=True)
            if assemble_result.returncode != 0:
                line, msg = parse_assembler_error(assemble_result.stderr, offset=offset)
                return JsonResponse({
                    'success': False,
                    'error_message': msg or assemble_result.stderr,
                    'error_line': line or 'unknown'
                })

            disassemble_cmd = [objdump_cmd, "-M", "no-aliases", "-d", tmp_elf]
            disassemble_result = await asyncio.to_thread(subprocess.run, disassemble_cmd, capture_output=True, text=True)
            if disassemble_result.returncode != 0:
                return JsonResponse({
                    'success': False,
                    'error_message': disassemble_result.stderr,
                    'error_line': 'unknown'
                })

            decoded_instructions = []
            for line in disassemble_result.stdout.splitlines():
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

            # Slice off setup instructions if present
            if setup_steps > 0 and len(decoded_instructions) >= setup_steps:
                decoded_instructions = decoded_instructions[setup_steps:]
            hex_lines = [item['hex'] for item in decoded_instructions]
            hex_output = "\n".join(hex_lines)

            try:
                sudo_or_base = IP.checkpsudo(code)
            except Exception:
                sudo_or_base = [l.strip() for l in code.splitlines() if l.strip() and not l.strip().endswith(':')]

            # Spawn Spike process
            spike_bin = os.path.join(globals.SPIKE, "spike")
            spike_cmd = f"{spike_bin} -d --isa={isa_str} {tmp_elf}"

            simulator = session_simulators.get(session_key)
            if simulator is None:
                simulator = Simulator()
                session_simulators[session_key] = simulator

            end_pc = int(decoded_instructions[-1]['pc'], 16) if decoded_instructions else None

            await simulator.start(
                spike_cmd,
                vtype=('v' in extensions),
                ftype=('f' in extensions or 'd' in extensions),
                dtype=('d' in extensions),
                setup_steps=setup_steps,
                end_pc=end_pc,
                user_tmp=user_tmp
            )

            return JsonResponse({
                'hex': hex_output,
                'is_sudo': sudo_or_base,
                'instructions': decoded_instructions,
                'success': True
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error_message': str(e), 'error_line': 'unknown'})

    return JsonResponse({'error': 'Invalid request'}, status=400)


async def step_code(request):
    ensure_background_cleanup()
    await sync_to_async(request.session.save)()
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'No active session'}, status=400)

    if request.method == "POST":
        simulator = session_simulators.get(session_key)
        if not simulator or not simulator.is_alive():
            if simulator and simulator.is_completed and not simulator.last_error:
                vreg_array = simulator.v_registers if simulator.vtype else [[0, 0] for _ in range(32)]
                return JsonResponse({
                    'memory': simulator.memory,
                    'register': simulator.registers,
                    'vreg': vreg_array,
                    'vreg_elements': simulator.vreg_elements,
                    'vector_status': simulator.vector_status,
                    'pc': simulator.pc,
                    'f_reg': simulator.f_registers,
                    'd_reg': simulator.d_registers,
                    'f_hex': simulator.f_hex,
                    'ended': True,
                    'message': 'Program execution completed.',
                    'success': True
                })
            err_msg = simulator.last_error if (simulator and simulator.last_error) else 'Simulator session expired or not initialized. Please click Assemble first.'
            return JsonResponse({'error': err_msg, 'success': False, 'ended': True}, status=400)

        # Protect session against concurrent overlapping steps
        async with simulator.lock:
            if not simulator.is_alive():
                if simulator.is_completed and not simulator.last_error:
                    vreg_array = simulator.v_registers if simulator.vtype else [[0, 0] for _ in range(32)]
                    return JsonResponse({
                        'memory': simulator.memory,
                        'register': simulator.registers,
                        'vreg': vreg_array,
                        'vreg_elements': simulator.vreg_elements,
                        'vector_status': simulator.vector_status,
                        'pc': simulator.pc,
                        'f_reg': simulator.f_registers,
                        'd_reg': simulator.d_registers,
                        'f_hex': simulator.f_hex,
                        'ended': True,
                        'message': 'Program execution completed.',
                        'success': True
                    })
                err_msg = simulator.last_error if simulator.last_error else 'Simulator session ended. Please click Assemble.'
                return JsonResponse({'error': err_msg, 'success': False, 'ended': True}, status=400)

            step_res = await simulator.step()
            if step_res in ("Simulation ended", "Program completed") or simulator.is_ended:
                if simulator.last_error:
                    return JsonResponse({'error': simulator.last_error, 'success': False, 'ended': True}, status=400)

            # Format vreg for frontend
            vreg_array = simulator.v_registers if simulator.vtype else [[0, 0] for _ in range(32)]
            is_ended = bool(simulator.is_ended or simulator.is_completed)

            return JsonResponse({
                'memory': simulator.memory,
                'register': simulator.registers,
                'vreg': vreg_array,
                'vreg_elements': simulator.vreg_elements,
                'vector_status': simulator.vector_status,
                'pc': simulator.pc,
                'f_reg': simulator.f_registers,
                'd_reg': simulator.d_registers,
                'f_hex': simulator.f_hex,
                'ended': is_ended,
                'message': 'Program execution completed.' if is_ended else '',
                'success': True
            })

    return JsonResponse({'error': 'Invalid request'}, status=400)


async def run_code(request):
    ensure_background_cleanup()
    await sync_to_async(request.session.save)()
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'No active session'}, status=400)

    if request.method == "POST":
        simulator = session_simulators.get(session_key)
        if not simulator:
            asm_resp = await assemble_code(request)
            simulator = session_simulators.get(session_key)
            if not simulator:
                return asm_resp

        if not simulator.is_alive():
            err_msg = simulator.last_error if simulator.last_error else 'Simulator not running or ended'
            return JsonResponse({'error': err_msg, 'success': False, 'ended': True}, status=400)

        async with simulator.lock:
            await simulator.run()

            vreg_array = simulator.v_registers if simulator.vtype else [[0, 0] for _ in range(32)]

            return JsonResponse({
                'memory': simulator.memory,
                'register': simulator.registers,
                'registers': simulator.registers,
                'vreg': vreg_array,
                'vreg_elements': simulator.vreg_elements,
                'vector_status': simulator.vector_status,
                'pc': simulator.pc,
                'f_reg': simulator.f_registers,
                'd_reg': simulator.d_registers,
                'f_hex': simulator.f_hex,
                'ended': True,
                'message': 'Program execution completed.',
                'success': True
            })

    return JsonResponse({'error': 'Invalid request'}, status=400)


def reset(request):
    if request.method == "POST":
        session_key = request.session.session_key
        if session_key:
            simulator = session_simulators.pop(session_key, None)
            if simulator:
                simulator.terminate()
            user_tmp = os.path.join(globals.TMP, session_key)
            if os.path.exists(user_tmp):
                shutil.rmtree(user_tmp, ignore_errors=True)

        return JsonResponse({
            'register': [0] * 32,
            'memory': {},
            'pc': 0,
            'fregister': [0.0] * 32,
            'd_reg': [0.0] * 32,
            'f_hex': ["0x0000000000000000"] * 32,
            'vreg': [[0, 0] for _ in range(32)],
            'vreg_elements': {
                '8': [[0] * 16 for _ in range(32)],
                '16': [[0] * 8 for _ in range(32)],
                '32': [[0] * 4 for _ in range(32)],
                '64': [[0] * 2 for _ in range(32)],
            },
            'vector_status': {
                'vl': 0,
                'sew': 32,
                'lmul': 'm1',
                'vta': 'ta',
                'vma': 'ma'
            },
            'success': True
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)
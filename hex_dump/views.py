import json
import re
import json
import os
import subprocess
import sys
from asgiref.sync import sync_to_async

import pexpect
from globals import RISCV32_GNU_TOOLCHAIN, RISCV64_GNU_TOOLCHAIN, TMP, TMP_ASM, TMP_DISASM, TMP_ELF, LINKER_SCRIPT, SPIKE
from django.http import JsonResponse
from Temp import Datapath as DP
from Temp import Datapath_single as DPS  
from Temp import interperator as IP
from .check import Simulator

last_reg = None
store_ins=[
    "sw", "sb", "sh"
]


class Wrong_input_Error(Exception):
    pass


execution = DPS.RISCVSimulatorSingle()
session_simulators = {}  #global variable to keep track of the Simulator instance

async def assemble(command,session_key):
    simulator = session_simulators.get(session_key)
    if simulator is None:
        simulator = Simulator()
        session_simulators[session_key] = simulator
        print('spike running')# Create a new instance of the Simulator

    await simulator.start(command)# This will terminate any existing process and start a new one
    print('spike running')
    # return JsonResponse({'status': 'Simulator started'})

async def step(session_key):
    simulator = session_simulators.get(session_key)
    if simulator is None:
        return JsonResponse({'output': "Simulator not started"})

    result = await simulator.step()
    return result

async def get_registers(session_key):
    simulator = session_simulators.get(session_key)
    if simulator is None:
        return JsonResponse({'output': "Simulator not started"})

    result = await simulator.get_registers()
    return result

async def get_memory(addres,session_key):
    simulator = session_simulators.get(session_key)
    if simulator is None:
        return JsonResponse({'output': "Simulator not started"})

    result = await simulator.get_memory(addres)
    return result

def get_user_tmp_paths(session_key):
    user_tmp = os.path.join(TMP, session_key)
    os.makedirs(user_tmp, exist_ok=True)
    return user_tmp
async def assemble_code(request):
    await sync_to_async(request.session.save)()
    session_key = request.session.session_key
    if not session_key:
        await sync_to_async(request.session.save)()
        session_key = request.session.session_key
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        mtype = data.get('mtype', '')
        ctype = data.get('ctype', '')
        ftype = data.get('ftype', '')
        dtype = data.get('dtype', '')
        vtype = data.get('vtype', '')
        rvtype = data.get('rvtype', '')
        
        try:
            # hex_output = IP.main(code)
            tmp = get_user_tmp_paths(session_key)
            tmp_elf = os.path.join(tmp, 'elf')
            tmp_asm = os.path.join(tmp, 'asm.S')
            tmp_disasm = os.path.join(tmp, 'disasm.S')
            
            sudo_or_base  = IP.checkpsudo(code)
            hex_output = get_hex_gcc(code , mtype, ctype, ftype, dtype , vtype, rvtype,tmp_asm , tmp_elf , tmp_disasm)
            command = f'{SPIKE+"/spike"} -d --isa={rvtype}i{mtype}{ctype}{ftype}{dtype}{vtype} {tmp_elf}'
            print(command)
            await assemble(command,session_key)
            return JsonResponse({'hex': hex_output ,
                             'is_sudo' : sudo_or_base,
                             'success': True}, )
        except IP.InstructionError as e:
            return JsonResponse({'success': False, 'error': str(e)})
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)})
        except Wrong_input_Error as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def parse_registers(input_str):
# Use regex to extract register names and values
    pattern = r'(\w+):\s+(0x[0-9a-fA-F]+)'
    matches = re.findall(pattern, input_str)

    # Create a dictionary with register names as keys and values as values
    register_dict = [int(value, 16) for _, value in matches]
    return register_dict


async def step_code(request):
    if request.method == "POST":
        await sync_to_async(request.session.save)()
        session_key = request.session.session_key
        if not session_key:
            await sync_to_async(request.session.save)()
            session_key = request.session.session_key
        print("check")
        data = json.loads(request.body)
        instruction = data.get('instruction', '')
        pc = data.get('pc', '')
        memory = data.get('memory', '')
        register = data.get('register', '')
        Fregister = data.get('f_register', '')
        execution.pc = pc
        if (pc != 0):
            execution.memory = memory
            execution.registers = register
            execution.f_registers = Fregister
        execution.run(instruction)
        ins = await step(session_key)
        print(ins)
        reg = await get_registers(session_key)
        add = extract_values(ins, reg)
        print(hex(add))
        # if (len(ins_split) >= 3): 
        if add >= 2147483648:
            print("hi")
            mem= await get_memory(hex(add),session_key)
            print(f"hi {mem}")
        # print(f"hi {mem}")
        register= parse_registers(reg) #execution.run(instruction)
        print(reg)
        Fregister=execution.f_registers
        memory = execution.memory
        pc = execution.pc
        return JsonResponse({'memory': memory ,
                             'register' : register,
                             'pc': pc,
                             'f_reg': Fregister},)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def reset(request):
    if request.method == "POST":
        request.session.save()
        session_key = request.session.session_key
        if not session_key:
           request.session.save()
           session_key = request.session.session_key
        simulator = session_simulators.get(session_key)
        if not simulator:
            return JsonResponse({'error': 'Simulator not running'}, status=404)
        simulator.terminate()
        execution.memory={}
        execution.registers=[0]*32
        execution.pc=0
        execution.instruction_memory = {}
        execution.f_registers = [0.0] * 32
        return JsonResponse({
                             'register': execution.registers,
                             'memory': execution.memory,
                             'pc':execution.pc,
                             'fregister': execution.f_registers}, )
    return JsonResponse({'error': 'Invalid request'}, status=400)

def extract_values(instruction, register_dump):
    # Extract the register name and immediate value from the instruction
    match = re.search(r'sw\s+(\w+),\s*(\d+)\((\w+)\)', instruction)
    if match:
        immediate_value = int(match.group(2), 10)
        register_name = match.group(3)
    else:
        immediate_value = None
        register_name = None

    # Extract the register value from the register dump
    if register_name:
        register_pattern = rf'{register_name}:\s*(0x[0-9a-fA-F]+)'
        reg_value_match = re.search(register_pattern, register_dump)
        if reg_value_match:
            register_value = int(reg_value_match.group(1), 16)
        else:
            register_value = None
    else:
        register_value = None
    if((register_value == None) or (immediate_value ==None) ):
        address = 0
    else:
        address=register_value+immediate_value
    
    return address

def get_hex_gcc(code , mtype, ctype, ftype, dtype , vtype , rvtype , tmp_asm , tmp_elf , tmp_disasm):
    hex_lines = []
    with open(tmp_asm, 'w') as file:
        file.write(code)
        print("here")
    try:
        disassembly_file = simulate_bash_script(tmp_asm ,tmp_elf , tmp_disasm , mtype, ctype, ftype, dtype , vtype , rvtype)
    except Exception as e:
        raise Wrong_input_Error(str(e))
    
    pc_hex = extract_pc_hex(disassembly_file, tmp_elf)
    for i in pc_hex:
        hex_lines.append(pc_hex[i])
    hex_output = '\n'.join(hex_lines)
    return hex_output


def extract_first_error_line(output):
    error_pattern = re.compile(r"^(.*?Error:.*)$")
    lines = output.splitlines()
    for line in lines:
        if error_pattern.match(line):
            print(line.split(':', 1)[1].strip())
            return line.split(':', 1)[1].strip()
    return None  


def extract_pc_hex(filename , tmp_elf):
    pc_hex_dict = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.split(':')
            if len(parts) > 1 and parts[1].strip(): 
                pc, hex_value = parts[0].strip(), parts[1].split()[0]
                if (pc!=tmp_elf):
                    pc_hex_dict[pc] = hex_value    
    return pc_hex_dict


def simulate_bash_script(file_name ,tmp_elf , tmp_disasm, mtype, ctype, ftype, dtype , vtype , rvtype):
    extensions = mtype + ctype + ftype + dtype + vtype 
    
    if rvtype == "rv32":
        assembletype = 'riscv32'
        abi = 'ilp32'
        if "f" in extensions and "d" in extensions:
            abi = "ilp32d"
        elif "f" in extensions:
            abi = "ilp32f"
    else:
        abi = "lp64"
        assembletype = 'riscv64'
        if "f" in extensions and "d" in extensions:
            abi = "lp64d"
        elif "f" in extensions:
            abi = "lp64f"

    assemble_cmd = [f"{assembletype}-unknown-elf-gcc",f"-march={rvtype}i{extensions}", f"-mabi={abi}", "-T", LINKER_SCRIPT, "-static", "-mcmodel=medany", "-fvisibility=hidden", "-nostdlib", "-nostartfiles", "-g", "-o", tmp_elf, file_name]
    assemble_result = subprocess.run(assemble_cmd, capture_output=True, text=True)
    print(assemble_result.stderr)
    if assemble_result.returncode != 0:
        raise Exception(f"Error in assembly: {assemble_result.stderr}")

    disassemble_cmd = [f"{assembletype}-unknown-elf-objdump","-M","no-aliases", "-d", tmp_elf]
    with open(tmp_disasm, 'w') as disassemble_output:
        disassemble_result = subprocess.run(disassemble_cmd, stdout=disassemble_output, text=True)
    if disassemble_result.returncode != 0:
        raise Exception(f"Error in disassembly: {disassemble_result.stderr}")

    print(f"Disassembly file created: {tmp_disasm}")
    return tmp_disasm
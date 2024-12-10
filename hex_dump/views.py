import json
import re
import json
import os
import subprocess
import sys

import pexpect
from globals import RISCV32_GNU_TOOLCHAIN, RISCV64_GNU_TOOLCHAIN, TMP_ASM, TMP_DISASM, TMP_ELF, LINKER_SCRIPT, SPIKE
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
simulator = None  #global variable to keep track of the Simulator instance

async def assemble(command):
    global simulator
    if simulator is None:
        simulator = Simulator()
        print('spike running')# Create a new instance of the Simulator

    await simulator.start(command)# This will terminate any existing process and start a new one
    print('spike running')
    # return JsonResponse({'status': 'Simulator started'})

async def step():
    global simulator
    if simulator is None:
        return JsonResponse({'output': "Simulator not started"})

    result = await simulator.step()
    return result

async def get_registers():
    global simulator
    if simulator is None:
        return JsonResponse({'output': "Simulator not started"})

    result = await simulator.get_registers()
    return result

async def get_memory(addres):
    global simulator
    if simulator is None:
        return JsonResponse({'output': "Simulator not started"})

    result = await simulator.get_memory(addres)
    return result
async def assemble_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        mtype = data.get('mtype', '')
        ctype = data.get('ctype', '')
        ftype = data.get('ftype', '')
        dtype = data.get('dtype', '')
        
        try:
            # hex_output = IP.main(code)
            sudo_or_base  = IP.checkpsudo(code)
            hex_output = get_hex_gcc(code , mtype, ctype, ftype, dtype)
            command = f'{SPIKE+"/spike"} -d --isa=rv32i{mtype}{ctype}{ftype}{dtype} {TMP_ELF}'
            print(command)
            await assemble(command)
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
        ins = await step()
        print(ins)
        reg = await get_registers()
        ins_split=ins.split()
        add = extract_values(ins, reg)
        print(hex(add))
        # if (len(ins_split) >= 3): 
        if add >= 2147483648:
            print("hi")
            mem= await get_memory(hex(add))
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

def create_ass_file(file_name, content, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    file_path = os.path.join(destination_folder, f"{file_name}.S")
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"File created at {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")

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

def get_hex_gcc(code , mtype, ctype, ftype, dtype):
    hex_lines = []
    with open(TMP_ASM, 'w') as file:
        file.write(code)
        print("here")
    try:
        disassembly_file = simulate_bash_script(TMP_ASM , mtype, ctype, ftype, dtype)
    except Exception as e:
        raise Wrong_input_Error(str(e))
    
    pc_hex = extract_pc_hex(disassembly_file)
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


def extract_pc_hex(filename):
    pc_hex_dict = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.split(':')
            if len(parts) > 1 and parts[1].strip(): 
                pc, hex_value = parts[0].strip(), parts[1].split()[0]
                if (pc!=TMP_ELF):
                    pc_hex_dict[pc] = hex_value    
    return pc_hex_dict


def simulate_bash_script(file_name , mtype, ctype, ftype, dtype):

    assemble_cmd = ["riscv32-unknown-elf-gcc",f"-march=rv32i{mtype}{ctype}{ftype}{dtype}", "-mabi=ilp32", "-T", LINKER_SCRIPT, "-static", "-mcmodel=medany", "-fvisibility=hidden", "-nostdlib", "-nostartfiles", "-g", "-o", TMP_ELF, file_name]
    assemble_result = subprocess.run(assemble_cmd, capture_output=True, text=True)
    print(assemble_result.stderr)
    if assemble_result.returncode != 0:
        raise Exception(f"Error in assembly: {assemble_result.stderr}")

    disassemble_cmd = ["riscv32-unknown-elf-objdump","-M","no-aliases", "-d", TMP_ELF]
    with open(TMP_DISASM, 'w') as disassemble_output:
        disassemble_result = subprocess.run(disassemble_cmd, stdout=disassemble_output, text=True)
    if disassemble_result.returncode != 0:
        raise Exception(f"Error in disassembly: {disassemble_result.stderr}")

    print(f"Disassembly file created: {TMP_DISASM}")
    return TMP_DISASM
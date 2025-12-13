import re
import json
import os
from pathlib import Path
import sys
import time

import pexpect
import globals
from django.http import JsonResponse
from django.shortcuts import render
from Temp import Datapath as DP
from Temp import Datapath_single as DPS  
from Temp import interperator as IP
from hex_dump.views import last_reg
from django.views.decorators.csrf import csrf_exempt
import subprocess
from globals import SPIKE,TMP_ELF

execution = DPS.RISCVSimulatorSingle()
class Wrong_input_Error(Exception):
    pass


def editor(request):
    return render(request,'index.html')


def testpage(request):
    return render(request,'index_test.html')


def create_txt_file(file_name, content, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    file_path = os.path.join(destination_folder, f"{file_name}.txt")
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        print(f"File created at {file_path}")
    except Exception as e:
        print(f"Error writing file: {e}")


def parse_assembler_error(error_str):
    # Example: "Error in assembly: ins.S:2: Error: no such instruction: `vadd.vv v1,v0,v0`"
    # Regex to capture line number and message
    match = re.search(r":(\d+):\s*Error:\s*(.*)", error_str)
    if match:
        return match.group(1), match.group(2)
    return None, error_str

def assemble_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        try:
            # hex_output = IP.main(code)
            sudo_or_base  = IP.checkpsudo(code)
            hex_output = get_hex_gcc(code)
            print('line 53 ', hex_output)
            return JsonResponse({'hex': hex_output ,
                             'is_sudo' : sudo_or_base,
                             'success': True}, )
        except (IP.InstructionError, ValueError, Wrong_input_Error, Exception) as e:
            error_str = str(e)
            line, msg = parse_assembler_error(error_str)
            if line:
                return JsonResponse({'success': False, 'error_message': msg, 'error_line': line})
            else:
                # Fallback for errors without line numbers or parsing failures
                return JsonResponse({'success': False, 'error_message': error_str, 'error_line': 'unknown'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def extract_first_error_line(output):
    error_pattern = re.compile(r"^(.*?Error:.*)$")
    lines = output.splitlines()
    for line in lines:
        if error_pattern.match(line):
            print(line.split(':', 1)[1].strip())
            return line.split(':', 1)[1].strip()
    return None  


def get_hex_gcc(code):
    hex_lines = []
    file_name = "ins"
    destination_folder = globals.RISCV32_GNU_TOOLCHAIN
    create_txt_file(file_name, code, destination_folder)
    file_name = 'ins.txt'
    
    try:
        disassembly_file = simulate_bash_script(file_name)
    except Exception as e:
        raise Wrong_input_Error(str(e))
    
    pc_hex = extract_pc_hex(disassembly_file)
    for i in pc_hex:
        hex_lines.append('0x'+pc_hex[i])
    hex_output = '\n'.join(hex_lines)
    return hex_output
    

def extract_pc_hex(filename):
    pc_hex_dict = {}
    with open(filename, 'r') as file:
        for line in file:
            parts = line.split(':')
            if len(parts) > 1 and parts[1].strip(): 
                pc, hex_value = parts[0].strip(), parts[1].split()[0]
                if (pc!='ins'):
                    pc_hex_dict[pc] = hex_value    
    return pc_hex_dict


def step_code(request):
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
            # execution.v_registers = Vregister # Need to accept vreg from frontend if passed
        
        register=execution.run(instruction)
        Fregister=execution.f_registers
        memory = execution.memory
        pc = execution.pc
        v_registers = execution.v_registers
        print(pc)
        return JsonResponse({'memory': memory ,
                             'register' : register,
                             'pc': pc,
                             'f_reg': Fregister,
                             'vreg': v_registers},)
    return JsonResponse({'error': 'Invalid request'}, status=400)


def run_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        hex_output = get_hex_gcc(code)
        sudo_or_base  = IP.checkpsudo(code)
        registers = last_reg
        execution2 = DP.RISCVSimulator()
        registers = execution2.run(hex_output)
        f_registers = execution2.f_registers
        v_registers = execution2.v_registers
        memory = execution2.memory
        return JsonResponse({'hex': hex_output ,
                             'is_sudo': sudo_or_base,
                             'registers': registers,
                             'memory': memory,
                             'f_reg': f_registers,
                             'vreg': v_registers}, )
    return JsonResponse({'error': 'Invalid request'}, status=400)


def reset(request):
    if request.method == "POST":
        execution.memory={}
        execution.registers=[0]*32
        execution.pc=0
        execution.instruction_memory = {}
        execution.f_registers = [0.0] * 32 
        execution.v_registers = [[0]*16 for _ in range(32)]
        return JsonResponse({
                             'register': execution.registers,
                             'memory': execution.memory,
                             'pc':execution.pc,
                             'fregister': execution.f_registers,
                             'vreg': execution.v_registers}, )
    return JsonResponse({'error': 'Invalid request'}, status=400)


def simulate_bash_script(file_name):
    # Extract the filename without the extension
    filename = os.path.splitext(file_name)[0]

    # Change directory
    os.chdir(globals.RISCV32_GNU_TOOLCHAIN)
    
    # Convert the .txt file to .S
    new_file_name = f"{filename}.S"
    os.rename(file_name, new_file_name)

    # Assemble the .S file to produce an object file using RISC-V assembler
    assemble_cmd = ["./riscv32-unknown-elf-as", "-o", filename, new_file_name]
    assemble_result = subprocess.run(assemble_cmd, capture_output=True, text=True)
    if assemble_result.returncode != 0:
        raise Exception(f"Error in assembly: {assemble_result.stderr}")

    # Disassemble the object file to produce a .S disassembly file
    disassembly_file = f"{filename}_disassembly.S"
    disassemble_cmd = ["./riscv32-unknown-elf-objdump", "-d", filename]
    with open(disassembly_file, 'w') as disassemble_output:
        disassemble_result = subprocess.run(disassemble_cmd, stdout=disassemble_output, text=True)
    if disassemble_result.returncode != 0:
        raise Exception(f"Error in disassembly: {disassemble_result.stderr}")

    print(f"Disassembly file created: {disassembly_file}")
    return disassembly_file
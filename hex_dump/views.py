import json
import re
import json
import os
import subprocess
from globals import RISCV32_GNU_TOOLCHAIN, RISCV64_GNU_TOOLCHAIN, TMP_ASM, TMP_DISASM, TMP_ELF
from django.http import JsonResponse
from Temp import Datapath as DP
from Temp import Datapath_single as DPS  
from Temp import interperator as IP



class Wrong_input_Error(Exception):
    pass


execution = DPS.RISCVSimulatorSingle()


def assemble_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        code = data.get('code', '')
        try:
            # hex_output = IP.main(code)
            sudo_or_base  = IP.checkpsudo(code)
            get_hex_gcc(code)
            hex_output = get_hex_gcc(code)
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


def get_hex_gcc(code):
    hex_lines = []
    with open(TMP_ASM, 'w') as file:
        file.write(code)
        print("here")
    try:
        disassembly_file = simulate_bash_script(TMP_ASM)
    except Exception as e:
        raise Wrong_input_Error(str(e))
    
    pc_hex = extract_pc_hex(disassembly_file)
    for i in pc_hex:
        hex_lines.append('0x'+pc_hex[i])
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


def simulate_bash_script(file_name):

    assemble_cmd = ["riscv32-unknown-elf-gcc","-march=rv32im", "-mabi=ilp32", "-T", "/home/saad/Desktop/oxygen/tools/riscv32-gnu-toolchain/bin/link.ld", "-static", "-mcmodel=medany", "-fvisibility=hidden", "-nostdlib", "-nostartfiles", "-g", "-o", TMP_ELF, file_name]
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
import json
import re
import json
import os
from django.http import JsonResponse
from Temp import Datapath as DP
from Temp import Datapath_single as DPS  
from Temp import interperator as IP
import subprocess


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


def get_hex_gcc(code):
    hex_lines = []
    file_name = "ins"
    destination_folder = "Itype/tools/riscv_32/bin/"
    create_txt_file(file_name, code, destination_folder)
    file_name = 'ins.txt'
    result = subprocess.run(["Itype/tools/riscv_32/bin/bash.sh",'ins.txt'], capture_output=True, text=True)
    if ('Error' in result.stderr):
        raise Wrong_input_Error(extract_first_error_line(result.stderr))
    pc_hex = extract_pc_hex('Itype/tools/riscv_32/bin/ins_disassembly.S')
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
                if (pc!='ins'):
                    pc_hex_dict[pc] = hex_value    
    return pc_hex_dict
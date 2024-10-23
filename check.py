# import json
# import shlex
# import subprocess
# import sys
# import pexpect
# import time
# import re

# from globals import SPIKE,TMP_ELF
# # Define the command
# cmd = f"./spike -d --isa=rv32im {TMP_ELF}"
# subprocess.call('cd tools/spike/bin', shell=True) 
# pattern = r"warning: tohost and fromhost symbols not in ELF; can't communicate with target\s*\(spike\)"
# stop_pattern = r"core\s+0:\s+0x80000002\s+\(0x00000000\)\s+c\.unimp\s+core\s+0:\s+exception\s+trap_illegal_instruction,\s+epc\s+0x80000002\s+core\s+0:\s+tval\s+0x00000000"
# x = pexpect.spawn(cmd ,encoding='utf-8')
# x.logfile_read=sys.stdout #Start subprocess.
# x.logfile_read = open ('mylogfilename.txt', 'w')
# x.expect(pattern)
# while True:
#     x.sendline("")
#     x.expect('(spike)')
#     x.sendline('reg 0')
#     x.expect('zero: 0x00000000')
    
#     # if re.search(stop_pattern, x.before):
#     if ('c.unimp' in x.before):
#             break
# x.logfile_read.close()

# with open('mylogfilename.txt', 'r+') as f:
#     str=''
#     a = f.readlines()
#     k = 0
#     start = False
#     for i in a:
#         if('c.unimp' in i):
#             break
#         if ('core   0: 0x8' in i):
#             start = True
#             str+=i
#         if('zero: 0x00000000' in i and start == True):
#             x = ('{'+i+a[k+1]+a[k+2]+a[k+3]+a[k+4]+a[k+5]+a[k+6]+a[k+7]+'}' + '\n')
#             str+=x
#         k+=1
#     f.write(str)

# file_path = 'mylogfilename.txt'  # Replace with your actual file name

# # Initialize the list to store register values
# register_values = []

# # Regular expression pattern to match hex values
# pattern = re.compile(r'0x[0-9a-fA-F]+')

# # Open the file and read its contents
# with open(file_path, 'r') as file:
#     for line in file:
#         # Find all hex values in the line
#         matches = pattern.findall(line)
#         # Add them to the list of register values
#         register_values.extend(matches)

# # Print or use the register values as needed
# last_reg = register_values[-32:-1]
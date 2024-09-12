import json
import shlex
import subprocess
import sys
import pexpect
import time
import re

from globals import SPIKE,TMP_ELF
# Define the command
cmd = f"./spike -d --isa=rv32im {TMP_ELF}"
subprocess.call('cd tools/spike/bin', shell=True) 
pattern = r"warning: tohost and fromhost symbols not in ELF; can't communicate with target\s*\(spike\)"
stop_pattern = r"core\s+0:\s+0x80000002\s+\(0x00000000\)\s+c\.unimp\s+core\s+0:\s+exception\s+trap_illegal_instruction,\s+epc\s+0x80000002\s+core\s+0:\s+tval\s+0x00000000"
x = pexpect.spawn(cmd ,encoding='utf-8')
x.logfile_read=sys.stdout #Start subprocess.
x.logfile_read = open ('mylogfilename.txt', 'w')
x.expect(pattern)
while True:
    x.sendline("")
    x.expect('(spike)')
    
    x.sendline('reg 0')
    x.expect('zero: 0x00000000')
    
    # if re.search(stop_pattern, x.before):
    if ('c.unimp' in x.before):
            break
    time.sleep(0.1)
x.logfile_read.close()

with open('mylogfilename.txt', 'r') as f:
    with open('clean.txt', 'w') as c:
        a = f.readlines()
        k = 0
        start = False
        for i in a:
            if('c.unimp' in i):
                break
            if ('core   0: 0x8' in i):
                start = True
                c.write(i)
            if('zero: 0x00000000' in i and start == True):
                x = ('{'+i+a[k+1]+a[k+2]+a[k+3]+a[k+4]+a[k+5]+a[k+6]+a[k+7]+'}' + '\n')
                c.write(x)
                
            k+=1


file_path = 'clean.txt'  # Replace with your actual file name

# Initialize the list to store register values
register_values = []

# Regular expression pattern to match hex values
pattern = re.compile(r'0x[0-9a-fA-F]+')

# Open the file and read its contents
with open(file_path, 'r') as file:
    for line in file:
        # Find all hex values in the line
        matches = pattern.findall(line)
        # Add them to the list of register values
        register_values.extend(matches)

# Print or use the register values as needed
last_reg = register_values[-32:-1]

        

# with open('output.txt', 'w') as f:
#     with open('x.log', 'r') as l:
#         f.write(l.readlines())


# Start subprocess
# x = pexpect.spawn(cmd)

# # Expect the warning pattern
# x.expect(pattern)

# # Collect the output
# output = []

# # Execute commands and capture output
# for i in range(0, 5):
#     x.sendline("")
#     output.append(x.before.decode('utf-8'))
#     x.expect('(spike)')
#     output.append(x.before.decode('utf-8'))
#     x.sendline('reg 0')
#     x.expect('zero: 0x00000000')
#     output.append(x.before.decode('utf-8'))
#     time.sleep(1)

# # Filter and format the output
# formatted_output = []

# # Extract the relevant lines
# for line in output:
#     if "core   0:" in line:
#         formatted_output.append(line.strip())
#         print(line)

# # Add the corresponding command
# formatted_output.append("core   0: 0x00001000 (0x00000297) auipc   t0, 0x0")

# # Write to a text file with binary encoding
# with open('output.txt', 'w') as f:
#     for line in formatted_output:
#         f.write(line + '\n')

# print("Data written to output.txt in binary encoding.")
# with open("output.txt", "w") as file:
#     x.expect(pattern)
    
#     for i in range(0, 5):
#         x.sendline("")
#         output_before = x.before
#         file.write(output_before + '\n')  # Write the output before the prompt
        
#         x.expect('(spike)')
#         output_before = x.before
#         file.write(output_before + '\n')  # Write the output before the prompt
        
#         x.sendline('reg 0')
#         x.expect('zero: 0x00000000')
#         reg_output = x.before
#         file.write(reg_output + '\n')  # Write the register output
        
#         # Write the specific command and register values
#         if "core   0: 0x00001000" in reg_output:
#             # Find the relevant command line
#             command_output = reg_output.split("core   0: 0x00001000 (")[1].split(")")[0].strip()
#             file.write(f"Command: {command_output}\n")
            
#             # Find the register values
#             start_index = reg_output.find("ra: ")
#             end_index = reg_output.find("t6: ") + len("t6: 0x00000000") + 1
#             register_values = reg_output[start_index:end_index].strip()
#             file.write(f"Register Values:\n{register_values}\n")
        
#         time.sleep(1)

# output = ''
# result = subprocess.run([cmd],shell=True ,capture_output=True, text=True)
# for line in iter(result.stdout.readline, ""):
#         print (line)
#         output += line
# print(result.stdout)

# process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE)
# output = process.stdout.readline()
# print ("printing: " + output.strip())
# while True:
#     output = process.stdout.readline()
#     if output == '' and process.poll() is not None:
#         break
#     if output:
#         print ("printing: " + output.strip())
# rc = process.poll()
# Start the subprocess with pexpect
# child = pexpect.spawn(cmd, encoding='utf-8')

# Define a timeout for waiting
# prompt_timeout = 10
# i = 0
# with open ('spike.txt','w') as file:
#     try:
#         while True:
#             # Wait for the prompt indicating the process is ready for input
#             index = child.expect([r'core\s+\d+:\s+[0x\w]+\s+\(0x[0-9a-f]+\)\s+c\.unimp',
#                                 '(spike)', 
#                                 pexpect.EOF, 
#                                 pexpect.TIMEOUT], 
#                                 timeout=prompt_timeout)
            
#             if index == 0:
#                 # Specific output encountered, stop the execution
#                 print("Stopping execution due to 'c.unimp' output")
#                 break
            
#             elif index == 1:
#                 # Print the output before sending the Enter key
#                 # print("Output:\n", child.before)
#                 if('warning:' in child.before):
#                     child.sendline('')
#                     pass
               
#                 else:
#                     file.write(child.before+'\n'+'end')                    
#                     child.sendline('')
            
#             elif index == 2:
#                 print("Output:\n", child.before)
#                 if('warning:' in child.before):
#                     child.sendline('')
#                     pass
#                 else:
#                     line =  child.before.split('\r')
                   
#                     file.write(line[1])
#                     child.sendline('')
#                     print("Sent Enter key")
#                 # End of file, the process finished
            
#             elif index == 3:
#                 # Handle timeout if necessary
#                 print("Timeout occurred")
#                 break
        
#         # Optional: Add 
#             time.sleep(1)

#     except pexpect.exceptions.EOF:
#         print("Unexpected EOF")
#     except pexpect.exceptions.TIMEOUT:
#         print("Timeout waiting for prompt")
#     finally:
#         child.close()   
#!/bin/bash

# Check if a file is provided
if [ $# -eq 0 ]; then
    echo "No file provided. Usage: ./script.sh <file.txt>"
    exit 1
fi

# Extract the filename without the extension
filename=$(basename "$1" .txt)

cd Itype/riscv_32/bin
# Convert the .txt file to .S using gedit
mv "$1" "${filename}.S"

# Assemble the .S file to produce an object file using RISC-V assembler
riscv32-unknown-elf-as -o "${filename}" "${filename}.S"

# Disassemble the object file to produce a .S disassembly file
riscv32-unknown-elf-objdump -d "${filename}" > "${filename}_disassembly.S"

# Return the disassembly file
echo "Disassembly file created: ${filename}_disassembly.S"
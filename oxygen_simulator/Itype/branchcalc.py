def replace_labels_with_immediates(instructions):
    # Split the instructions into a list of lines
    lines = instructions.split('\n')
    print(lines)
    # First pass: Identify labels and their addresses
    labels = {}
    address = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            label = line.split(':')[0].strip()
            labels[label] = address
            print(label)
        else:
            print(address , " " , line)
            address += 4
            print(labels)
            
            

    # Second pass: Calculate immediates and replace labels
    result = []
    address = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ':' in line:
            label = line.split(':')[0].strip()
            line = line.split(':')[1].strip()
            if not line:
                continue
        if line[0].lower()=='b':
            parts = line.split(',')
            label = parts[-1].strip()
            if label in labels:
                immediate = labels[label] - address
                new_line = f"{parts[0]},{parts[1]},{immediate}"
                result.append(new_line)
        elif line[0].lower()=='j':
            parts = line.split(' ')
            label = parts[-1].strip()
            if (label in labels):
                immediate = labels[label]-address
                new_line = f"{parts[0]} {immediate}"
                result.append(new_line)
                
            else:
                result.append(line)
        else:
            result.append(line)
        address += 4
    
    return '\n'.join(result)

# Example usage:
instructions = """
li x1,1
li x2,5
jump:
blt x1,x2,label
addi x1,x1,1
jalr x1,x1,12
label:
nop
"""

print(replace_labels_with_immediates(instructions))
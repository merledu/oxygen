import re

# Define the file path
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
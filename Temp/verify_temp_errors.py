import sys
import os

sys.path.append('/home/abdulrehman/Desktop/oxygen/Temp')
import interperator
import Datapath

def test_temp_errors():
    input_file = '/home/abdulrehman/Desktop/oxygen/Temp/test_temp_errors.asm'
    with open(input_file, 'r') as f:
        content = f.read()
    
    print("Input Assembly:")
    print(content)
    print("-" * 20)
    
    print("Running Interpreter (Expect Errors):")
    hex_output = interperator.main(content)
    print("Hex Output:")
    print(hex_output)
    print("-" * 20)
    
    print("Running Simulator (Expect Runtime Errors if any hex generated):")
    sim = Datapath.RISCVSimulator()
    sim.run(hex_output)

if __name__ == "__main__":
    test_temp_errors()

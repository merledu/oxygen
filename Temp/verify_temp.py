import sys
import os

# Add the directory containing Temp files to the python path
sys.path.append('/home/abdulrehman/Desktop/oxygen/Temp')

import interperator
import Datapath

def test_temp_imfcd():
    input_file = '/home/abdulrehman/Desktop/oxygen/Temp/test_temp_imfcd.asm'
    with open(input_file, 'r') as f:
        content = f.read()
    
    print("Input Assembly:")
    print(content)
    print("-" * 20)
    
    try:
        print("Running Interpreter...")
        hex_output = interperator.main(content)
        print("Hex Output:")
        print(hex_output)
        print("-" * 20)
        
        print("Running Simulator...")
        sim = Datapath.RISCVSimulator()
        # Initialize some registers for testing
        sim.registers[2] = 10 # x2
        sim.registers[3] = 20 # x3
        sim.f_registers[2] = 1.5 # f2
        sim.f_registers[3] = 2.5 # f3
        
        sim.run(hex_output)
        
        print("Register Dump:")
        sim.dump_registers()
        print("F Register Dump (partial):")
        for i in range(5):
             print(f"f{i}: {sim.f_registers[i]}")
             
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_temp_imfcd()

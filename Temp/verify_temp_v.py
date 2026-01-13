import sys
import os

sys.path.append('/home/abdulrehman/Desktop/oxygen/Temp')
import interperator
import Datapath

def test_temp_v():
    input_file = '/home/abdulrehman/Desktop/oxygen/Temp/test_temp_v.asm'
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
        
        # Setup registers and memory
        sim.registers[1] = 0x100 # x1 = address 0x100
        sim.registers[2] = 10    # x2 = 10
        sim.registers[3] = 20    # x3 = 20
        
        # Initialize memory at 0x100
        for i in range(16):
            sim.memory[0x100 + i] = i # 0, 1, 2, ... 15
            
        sim.run(hex_output)
        
        print("Register Dump:")
        sim.dump_registers()
        print("V Register Dump (partial):")
        for i in range(5):
             print(f"v{i}: {sim.v_registers[i]}")
             
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_temp_v()

import sys
import os

sys.path.append('/home/abdulrehman/Desktop/oxygen/Temp')
import interperator
import Datapath_single

def test_single():
    print("Testing Datapath_single.py with IMFCDV instructions...")
    
    # Define test assembly
    assembly_code = """
    addi x1, x0, 10
    mul x2, x1, x1
    fcvt.s.w f1, x1
    fadd.s f2, f1, f1
    c.addi x1, 1
    vadd.vv v1, v0, v0
    """
    # Note: vadd.vv v1, v0, v0 might be 0+0=0 if v0 is 0.
    # Let's try to load something into V registers first?
    # vle8.v requires memory.
    # Let's use vadd.vi v1, v0, 5 (if supported) -> v1 = v0 + 5
    # interperator.py has vadd.vi
    
    assembly_code = """
    addi x1, x0, 10
    mul x2, x1, x1
    fcvt.s.w f1, x1
    fadd.s f2, f1, f1
    c.addi x1, 1
    vadd.vi v1, v0, 5
    """
    
    print("Assembly:")
    print(assembly_code)
    
    try:
        # Generate Hex
        hex_output = interperator.main(assembly_code)
        print("\nHex Output:")
        print(hex_output)
        
        hex_lines = hex_output.strip().split('\n')
        
        # Initialize Simulator
        sim = Datapath_single.RISCVSimulatorSingle()
        
        # Run instructions
        print("\nExecuting...")
        for hex_inst in hex_lines:
            print(f"Executing: {hex_inst}")
            sim.run(hex_inst)
            
        # Check Results
        print("\nResults:")
        print(f"x1 (should be 11): {sim.registers[1]}")
        print(f"x2 (should be 100): {sim.registers[2]}")
        print(f"f1 (should be 10.0): {sim.f_registers[1]}")
        print(f"f2 (should be 20.0): {sim.f_registers[2]}")
        print(f"v1[0] (should be 5): {sim.v_registers[1][0]}")
        
        # Assertions
        assert sim.registers[1] == 11, "x1 incorrect"
        assert sim.registers[2] == 100, "x2 incorrect"
        assert sim.f_registers[1] == 10.0, "f1 incorrect"
        assert sim.f_registers[2] == 20.0, "f2 incorrect"
        assert sim.v_registers[1][0] == 5, "v1[0] incorrect"
        
        print("\nSUCCESS: All checks passed!")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single()

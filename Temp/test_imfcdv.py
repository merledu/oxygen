import sys
import os
import math

# Add current directory to path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Datapath import RISCVSimulator
from interperator import main as assemble

def test_imfcdv():
    print("Starting IMFCDV Verification...")
    
    # Assembly code covering various extensions
    assembly_code = """
    # I Extension
    addi x1, x0, 10
    fence
    fence.i
    
    # M Extension
    addi x2, x0, 5
    mul x3, x1, x2      # x3 = 50
    
    # F Extension
    # Load float values (simulated via integer moves for now as we don't have data section loader)
    # Actually we can use fcvt
    fcvt.s.w f1, x1     # f1 = 10.0
    fcvt.s.w f2, x2     # f2 = 5.0
    fadd.s f3, f1, f2   # f3 = 15.0
    fsqrt.s f4, f1      # f4 = sqrt(10.0) ~= 3.162
    
    # D Extension
    fcvt.d.w f5, x1     # f5 = 10.0 (double)
    fcvt.d.w f6, x2     # f6 = 5.0 (double)
    fmul.d f7, f5, f6   # f7 = 50.0 (double)
    
    # C Extension
    c.li x4, 7          # x4 = 7
    c.add x4, x2        # x4 = 7 + 5 = 12
    c.mv x5, x4         # x5 = 12
    
    # V Extension
    # Initialize vector registers (manually via loop in simulator or just assume 0)
    # We will use vadd.vi to set some values
    # vadd.vi vd, vs2, imm. vs2=0 (v0) which is 0.
    vadd.vi v1, v0, 2   # v1 = [2, 2, ...]
    vadd.vi v2, v0, 3   # v2 = [3, 3, ...]
    vadd.vv v3, v1, v2  # v3 = [5, 5, ...]
    vmul.vv v4, v1, v2  # v4 = [6, 6, ...]
    
    # System
    # ecall
    """
    
    try:
        # Assemble
        print("Assembling...")
        hex_code = assemble(assembly_code)
        if "Error" in hex_code:
            print(f"Assembly Failed:\n{hex_code}")
            return

        # Simulate
        print("Simulating...")
        sim = RISCVSimulator()
        sim.run(hex_code)
        
        # Verify Results
        print("Verifying...")
        
        # I/M Check
        assert sim.registers[3] == 50, f"MUL failed: x3={sim.registers[3]}"
        
        # F Check
        assert sim.f_registers[3] == 15.0, f"FADD.S failed: f3={sim.f_registers[3]}"
        assert abs(sim.f_registers[4] - math.sqrt(10.0)) < 0.0001, f"FSQRT.S failed: f4={sim.f_registers[4]}"
        
        # D Check
        assert sim.f_registers[7] == 50.0, f"FMUL.D failed: f7={sim.f_registers[7]}"
        
        # C Check
        assert sim.registers[4] == 12, f"C.ADD failed: x4={sim.registers[4]}"
        assert sim.registers[5] == 12, f"C.MV failed: x5={sim.registers[5]}"
        
        # V Check
        # v3 should be all 5s
        # v4 should be all 6s
        for i in range(16):
            assert sim.v_registers[3][i] == 5, f"VADD.VV failed at index {i}: {sim.v_registers[3][i]}"
            assert sim.v_registers[4][i] == 6, f"VMUL.VV failed at index {i}: {sim.v_registers[4][i]}"
            
        print("All tests passed!")
        
    except Exception as e:
        print(f"Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imfcdv()

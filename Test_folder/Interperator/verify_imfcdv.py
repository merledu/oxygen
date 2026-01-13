import sys
import os

# Add the directory containing interperator.py to the python path
sys.path.append('/home/abdulrehman/Desktop/oxygen/Test_folder/Interperator')

import interperator

def test_imfcdv():
    input_file = '/home/abdulrehman/Desktop/oxygen/Test_folder/Interperator/test_imfcdv.asm'
    with open(input_file, 'r') as f:
        content = f.read()
    
    print("Input Assembly:")
    print(content)
    print("-" * 20)
    
    try:
        hex_output = interperator.main(content)
        print("Hex Output:")
        print(hex_output)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imfcdv()

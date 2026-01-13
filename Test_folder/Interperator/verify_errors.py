import sys
sys.path.append('/home/abdulrehman/Desktop/oxygen/Test_folder/Interperator')
import interperator

def test_errors():
    input_file = '/home/abdulrehman/Desktop/oxygen/Test_folder/Interperator/test_errors.asm'
    with open(input_file, 'r') as f:
        content = f.read()
    
    print("Input Assembly:")
    print(content)
    print("-" * 20)
    
    output = interperator.main(content)
    print("Output:")
    print(output)

if __name__ == "__main__":
    test_errors()

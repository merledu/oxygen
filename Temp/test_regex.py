import re

def parse_assembler_error(error_str):
    # Example: "Error in assembly: ins.S:2: Error: no such instruction: `vadd.vv v1,v0,v0`"
    # Regex to capture line number and message
    match = re.search(r":(\d+):\s*Error:\s*(.*)", error_str)
    if match:
        return match.group(1), match.group(2)
    return None, error_str

def test_parsing():
    errors = [
        ("Error in assembly: ins.S:2: Error: no such instruction: `vadd.vv v1,v0,v0`", "2", "no such instruction: `vadd.vv v1,v0,v0`"),
        ("Error in assembly: ins.S:10: Error: illegal operands `addi x1, x2`", "10", "illegal operands `addi x1, x2`"),
        ("Some other error", None, "Some other error")
    ]
    
    for err, expected_line, expected_msg in errors:
        line, msg = parse_assembler_error(err)
        print(f"Input: {err}")
        print(f"Parsed: Line={line}, Msg={msg}")
        assert line == expected_line
        assert msg == expected_msg
        print("PASS")

if __name__ == "__main__":
    test_parsing()

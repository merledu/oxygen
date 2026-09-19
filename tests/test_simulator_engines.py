import concurrent.futures
import json
import unittest
import requests

BASE = 'http://127.0.0.1:8000/oxygen'


class TestOxygenEngines(unittest.TestCase):

    def setUp(self):
        self.session = requests.Session()

    def tearDown(self):
        try:
            self.session.post(f'{BASE}/reset')
            self.session.post(f'{BASE}/gen-hex/reset')
        except Exception:
            pass

    # =========================================================================
    # 1. Custom Simulator Tests
    # =========================================================================

    def test_01_custom_assemble(self):
        """Test custom assemble endpoint with standard RISC-V instructions."""
        code = "addi x1, x0, 15\naddi x2, x1, 25\n"
        resp = self.session.post(f'{BASE}/assemble-code', json={'code': code})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'), f"Assemble failed: {data}")
        hexes = data.get('hex', '').strip().splitlines()
        self.assertEqual(len(hexes), 2)
        self.assertTrue(hexes[0].startswith('0x'))

    def test_02_custom_step_and_registers(self):
        """Test stepping through custom interpreter instructions and register updates."""
        # 1. addi x1, x0, 10
        step1 = self.session.post(f'{BASE}/step', json={
            'instruction': '0x00a00093',
            'pc': 0,
            'register': [0] * 32,
            'memory': {},
            'f_register': [0.0] * 32,
            'vreg': [[0] * 16 for _ in range(32)]
        })
        self.assertEqual(step1.status_code, 200)
        d1 = step1.json()
        self.assertEqual(d1['register'][1], 10, f"x1 expected 10, got {d1['register'][1]}")
        self.assertEqual(d1['pc'], 4)

        # 2. addi x2, x1, 20 (0x01408113)
        step2 = self.session.post(f'{BASE}/step', json={
            'instruction': '0x01408113',
            'pc': d1['pc'],
            'register': d1['register'],
            'memory': d1['memory'],
            'f_register': d1['f_reg'],
            'vreg': d1['vreg']
        })
        self.assertEqual(step2.status_code, 200)
        d2 = step2.json()
        self.assertEqual(d2['register'][2], 30, f"x2 expected 30, got {d2['register'][2]}")
        self.assertEqual(d2['pc'], 8)

    def test_03_custom_jalr(self):
        """Verify JALR (opcode 0x67) executes and sets PC correctly without hanging."""
        # Setup: x1 = 16, then jalr x2, 4(x1) -> sets x2 = pc+4, pc = 20
        # jalr x2, 4(x1): rd=2, rs1=1, imm=4 -> 0x00408167
        regs = [0] * 32
        regs[1] = 16
        resp = self.session.post(f'{BASE}/step', json={
            'instruction': '0x00408167',
            'pc': 0,
            'register': regs,
            'memory': {},
            'f_register': [0.0] * 32,
            'vreg': [[0] * 16 for _ in range(32)]
        })
        self.assertEqual(resp.status_code, 200)
        d = resp.json()
        self.assertEqual(d['register'][2], 4, f"Return address in x2 expected 4, got {d['register'][2]}")
        self.assertEqual(d['pc'], 20, f"Target PC expected 20, got {d['pc']}")

    def test_04_custom_memory_store_and_load(self):
        """Verify store and load instructions in custom engine."""
        # 1. Store word: sw x1, 8(x0) with x1 = 99 -> 0x00102423
        regs = [0] * 32
        regs[1] = 99
        s_resp = self.session.post(f'{BASE}/step', json={
            'instruction': '0x00102423',
            'pc': 0,
            'register': regs,
            'memory': {},
            'f_register': [0.0] * 32,
            'vreg': [[0] * 16 for _ in range(32)]
        })
        self.assertEqual(s_resp.status_code, 200)
        d_mem = s_resp.json()
        self.assertIn('8', d_mem['memory'])
        self.assertEqual(d_mem['memory']['8'], 99)

        # 2. Load word: lw x2, 8(x0) -> 0x00802103
        l_resp = self.session.post(f'{BASE}/step', json={
            'instruction': '0x00802103',
            'pc': 4,
            'register': d_mem['register'],
            'memory': d_mem['memory'],
            'f_register': d_mem['f_reg'],
            'vreg': d_mem['vreg']
        })
        self.assertEqual(l_resp.status_code, 200)
        d_load = l_resp.json()
        self.assertEqual(d_load['register'][2], 99, f"x2 expected 99 from lw, got {d_load['register'][2]}")

    def test_05_custom_run_code(self):
        """Verify batch run_code endpoint on custom engine."""
        code = "addi x1, x0, 7\naddi x2, x0, 8\nmul x3, x1, x2\n"
        resp = self.session.post(f'{BASE}/run-code', json={'code': code, 'mtype': 'm'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data['registers'][1], 7)
        self.assertEqual(data['registers'][2], 8)
        self.assertEqual(data['registers'][3], 56, f"Expected 7*8=56, got {data['registers'][3]}")

    # =========================================================================
    # 2. Spike Simulator Tests
    # =========================================================================

    def test_06_spike_assemble_and_step(self):
        """Test Spike assemble, step, and genuine register updates."""
        code = "addi x1, x0, 42\naddi x2, x1, 8\n"
        asm_resp = self.session.post(f'{BASE}/gen-hex/assemble-code', json={
            'code': code,
            'mtype': '', 'ctype': '', 'ftype': '', 'dtype': '', 'vtype': '', 'rvtype': 'rv32'
        })
        self.assertEqual(asm_resp.status_code, 200)
        data = asm_resp.json()
        self.assertTrue(data.get('success'), f"Spike assemble failed: {data}")

        # Step 1: addi x1, x0, 42
        step1 = self.session.post(f'{BASE}/gen-hex/step', json={})
        self.assertEqual(step1.status_code, 200)
        d1 = step1.json()
        self.assertTrue(d1.get('success'))
        self.assertEqual(d1['register'][1], 42, f"Spike x1 expected 42, got {d1['register'][1]}")
        self.assertEqual(d1['pc'], 0x80000000)

        # Step 2: addi x2, x1, 8
        step2 = self.session.post(f'{BASE}/gen-hex/step', json={})
        self.assertEqual(step2.status_code, 200)
        d2 = step2.json()
        self.assertTrue(d2.get('success'))
        self.assertEqual(d2['register'][2], 50, f"Spike x2 expected 50, got {d2['register'][2]}")

    def test_07_spike_memory_store(self):
        """Test Spike memory store and memory dictionary reflection."""
        code = "lui x1, 0x80001\naddi x2, x0, 77\nsw x2, 4(x1)\n"
        asm_resp = self.session.post(f'{BASE}/gen-hex/assemble-code', json={
            'code': code,
            'mtype': '', 'ctype': '', 'ftype': '', 'dtype': '', 'vtype': '', 'rvtype': 'rv32'
        })
        self.assertTrue(asm_resp.json().get('success'))

        # Step through the 3 instructions
        s1 = self.session.post(f'{BASE}/gen-hex/step', json={})
        s2 = self.session.post(f'{BASE}/gen-hex/step', json={})
        s3 = self.session.post(f'{BASE}/gen-hex/step', json={})
        d3 = s3.json()
        self.assertTrue(d3.get('success'))
        # Address 0x80001004 should be populated with 0x0000004d (77)
        self.assertIn('0x80001004', d3['memory'], f"Expected 0x80001004 in memory, got {d3['memory']}")
        self.assertEqual(int(d3['memory']['0x80001004'], 16), 77)

    def test_08_spike_run_code(self):
        """Test batch run-code execution on Spike engine."""
        code = "addi x1, x0, 100\naddi x2, x1, 50\n"
        resp = self.session.post(f'{BASE}/gen-hex/run-code', json={
            'code': code,
            'mtype': '', 'ctype': '', 'ftype': '', 'dtype': '', 'vtype': '', 'rvtype': 'rv32'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'), f"Spike run failed: {data}")
        self.assertEqual(data['registers'][1], 100)
        self.assertEqual(data['registers'][2], 150)

    # =========================================================================
    # 3. Concurrency & Isolation Tests
    # =========================================================================

    def test_09_parallel_user_isolation(self):
        """Verify parallel users do not collide or overwrite each other's code/state."""
        def run_user(user_id):
            s = requests.Session()
            val = user_id * 10
            code = f"addi x1, x0, {val}\naddi x2, x1, 5\n"
            # Assemble custom
            r1 = s.post(f'{BASE}/assemble-code', json={'code': code})
            if not r1.json().get('success'):
                return False, f"User {user_id} assemble failed: {r1.text}"
            # Run custom
            r2 = s.post(f'{BASE}/run-code', json={'code': code})
            d = r2.json()
            if d.get('registers', [0, 0])[1] != val or d.get('registers', [0, 0, 0])[2] != val + 5:
                return False, f"User {user_id} got wrong regs: {d.get('registers')}"
            return True, "OK"

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_user, i) for i in range(1, 9)]
            for f in concurrent.futures.as_completed(futures):
                success, msg = f.result()
                self.assertTrue(success, msg)

    # =========================================================================
    # 4. Error Handling
    # =========================================================================

    def test_10_assembly_syntax_error(self):
        """Verify invalid assembly code returns error with line number."""
        bad_code = "addi x1, x0, 10\nnot_an_instruction x2, x1\n"
        resp = self.session.post(f'{BASE}/assemble-code', json={'code': bad_code})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data.get('success'))
        self.assertEqual(int(data.get('error_line')), 2)
        self.assertIn('not_an_instruction', data.get('error_message', ''))

    def test_11_custom_float_and_compressed(self):
        """Verify F and C extension operations in custom engine."""
        code = "addi x1, x0, 10\nfcvt.s.w f1, x1\nfadd.s f2, f1, f1\nc.addi x1, 5\n"
        resp = self.session.post(f'{BASE}/run-code', json={'code': code, 'ftype': 'f', 'ctype': 'c'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data['registers'][1], 15, f"Expected 15 after c.addi, got {data['registers'][1]}")
        self.assertEqual(data['f_reg'][1], 10.0, f"Expected f1=10.0, got {data['f_reg'][1]}")
        self.assertEqual(data['f_reg'][2], 20.0, f"Expected f2=20.0, got {data['f_reg'][2]}")

    def test_12_spike_float(self):
        """Verify F extension operations in Spike engine."""
        code = "addi x1, x0, 10\nfcvt.s.w f1, x1\nfadd.s f2, f1, f1\n"
        asm = self.session.post(f'{BASE}/gen-hex/assemble-code', json={'code': code, 'ftype': 'f'})
        self.assertTrue(asm.json().get('success'))
        self.session.post(f'{BASE}/gen-hex/step', json={})
        s2 = self.session.post(f'{BASE}/gen-hex/step', json={})
        self.assertEqual(s2.json().get('f_reg')[1], 10.0)
        s3 = self.session.post(f'{BASE}/gen-hex/step', json={})
        self.assertEqual(s3.json().get('f_reg')[2], 20.0)

    def test_13_spike_vector(self):
        """Verify V extension operations in Spike engine."""
        code = "vsetvli t0, x0, e32, m1, ta, ma\nvmv.v.i v1, 7\n"
        asm = self.session.post(f'{BASE}/gen-hex/assemble-code', json={'code': code, 'vtype': 'v'})
        self.assertTrue(asm.json().get('success'))
        self.session.post(f'{BASE}/gen-hex/step', json={})
        s2 = self.session.post(f'{BASE}/gen-hex/step', json={})
        vreg = s2.json().get('vreg')
        self.assertIsNotNone(vreg)
        self.assertGreater(vreg[1][0], 0, f"Expected non-zero vector element, got {vreg[1]}")

    def test_14_spike_double_precision(self):
        """Verify D extension operations, 64-bit double registers, and hex in Spike."""
        code = "addi x1, x0, 25\nfcvt.d.w ft1, x1\nfadd.d ft2, ft1, ft1\n"
        asm = self.session.post(f'{BASE}/gen-hex/assemble-code', json={'code': code, 'dtype': 'd'})
        self.assertTrue(asm.json().get('success'))
        self.session.post(f'{BASE}/gen-hex/step', json={})
        s2 = self.session.post(f'{BASE}/gen-hex/step', json={})
        d2 = s2.json()
        self.assertEqual(d2['d_reg'][1], 25.0, f"Expected d_reg[1]=25.0, got {d2['d_reg'][1]}")
        s3 = self.session.post(f'{BASE}/gen-hex/step', json={})
        d3 = s3.json()
        self.assertEqual(d3['d_reg'][2], 50.0, f"Expected d_reg[2]=50.0, got {d3['d_reg'][2]}")
        self.assertIn('4049000000000000', d3['f_hex'][2].lower())

    def test_15_spike_double_store(self):
        """Verify 8-byte fsd store into memory in Spike."""
        code = "lui x1, 0x80001\naddi x2, x0, 25\nfcvt.d.w ft1, x2\nfsd ft1, 8(x1)\n"
        asm = self.session.post(f'{BASE}/gen-hex/assemble-code', json={'code': code, 'dtype': 'd'})
        self.assertTrue(asm.json().get('success'))
        for _ in range(4):
            last_resp = self.session.post(f'{BASE}/gen-hex/step', json={})
        d = last_resp.json()
        self.assertIn('0x80001008', d['memory'])

    def test_16_spike_vector_csr_and_slicing(self):
        """Verify vector CSR (sew, lmul, vl) tracking and element slicing."""
        code = "vsetvli t0, x0, e16, m1, ta, ma\nvmv.v.i v1, 9\n"
        asm = self.session.post(f'{BASE}/gen-hex/assemble-code', json={'code': code, 'vtype': 'v'})
        self.assertTrue(asm.json().get('success'))
        s1 = self.session.post(f'{BASE}/gen-hex/step', json={})
        d1 = s1.json()
        self.assertEqual(d1['vector_status']['sew'], 16)
        self.assertEqual(d1['vector_status']['lmul'], 'm1')
        s2 = self.session.post(f'{BASE}/gen-hex/step', json={})
        d2 = s2.json()
        # Check that 16-bit element slicing has 9 in elements
        e16_elements = d2['vreg_elements']['16'][1]
        self.assertIn(9, e16_elements)

    def test_17_spike_byte_halfword_stores(self):
        """Verify 1-byte (sb) and 2-byte (sh) memory writes in Spike."""
        code = "lui x1, 0x80001\naddi x2, x0, 0x5a\nsb x2, 1(x1)\naddi x3, x0, 0x123\nsh x3, 4(x1)\n"
        asm = self.session.post(f'{BASE}/gen-hex/assemble-code', json={'code': code})
        self.assertTrue(asm.json().get('success'))
        for _ in range(5):
            last_resp = self.session.post(f'{BASE}/gen-hex/step', json={})
        mem = last_resp.json()['memory']
        self.assertIn('0x80001001', mem)
        self.assertIn('0x80001004', mem)

    def test_18_numeric_branch_and_jump_offsets(self):
        """Verify numeric branch and jump offsets (e.g. beq x1, x1, 8 / jal x29, 8)."""
        code = "addi x1, x0, 10\nbeq x1, x1, 8\nnop\nnop\njal x29, 8\nnop\nnop\n"
        # Spike
        asm_spike = self.session.post(f'{BASE}/gen-hex/assemble-code', json={'code': code})
        self.assertTrue(asm_spike.json().get('success'))
        # Custom
        asm_custom = self.session.post(f'{BASE}/assemble-code', json={'code': code})
        self.assertTrue(asm_custom.json().get('success'))


if __name__ == '__main__':
    unittest.main()


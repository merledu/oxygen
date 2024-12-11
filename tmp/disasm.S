
/home/saad/Desktop/oxygen/tmp/elf:     file format elf32-littleriscv


Disassembly of section .text:

80000000 <loop-0x20>:
80000000:	00000293          	addi	t0,zero,0
80000004:	00100313          	addi	t1,zero,1
80000008:	800002b7          	lui	t0,0x80000
8000000c:	0062a023          	sw	t1,0(t0) # 80000000 <loop-0x20>
80000010:	00100313          	addi	t1,zero,1
80000014:	0062a223          	sw	t1,4(t0)
80000018:	00200393          	addi	t2,zero,2
8000001c:	00002e03          	lw	t3,0(zero) # 0 <loop-0x80000020>

80000020 <loop>:
80000020:	03c38063          	beq	t2,t3,80000040 <end>
80000024:	ffc2ae83          	lw	t4,-4(t0)
80000028:	ff82af03          	lw	t5,-8(t0)
8000002c:	01ee8fb3          	add	t6,t4,t5
80000030:	01f2a023          	sw	t6,0(t0)
80000034:	00428293          	addi	t0,t0,4
80000038:	00138393          	addi	t2,t2,1
8000003c:	fe5ff06f          	jal	zero,80000020 <loop>

80000040 <end>:
80000040:	00a00893          	addi	a7,zero,10

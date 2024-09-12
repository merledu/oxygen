
/home/saad/Desktop/oxygen/tmp/elf:     file format elf32-littleriscv


Disassembly of section .text:

80000000 <lael-0x8>:
80000000:	00100093          	addi	ra,zero,1
80000004:	00500113          	addi	sp,zero,5

80000008 <lael>:
80000008:	00108093          	addi	ra,ra,1
8000000c:	00000193          	addi	gp,zero,0
80000010:	fe209ce3          	bne	ra,sp,80000008 <lael>
80000014:	0080006f          	jal	zero,8000001c <_end>
80000018:	00100193          	addi	gp,zero,1

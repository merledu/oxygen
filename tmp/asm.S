li t0, 0
li t1, 1
li t0,0x80000000
sw t1, 0(t0)
li t1, 1
sw t1, 4(t0)
li t2, 2
lw t3, 0(x0)
loop:
beq t2, t3, end
lw t4, -4(t0)
lw t5, -8(t0)
add t6, t4, t5
sw t6, 0(t0)
addi t0, t0, 4
addi t2, t2, 1
j loop
end:
li a7, 10
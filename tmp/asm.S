li x1,1
li x2,5
lael:
addi x1,x1,1
li x3,0
bne x1,x2,lael
j end
li x3,1
end:
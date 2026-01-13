add x1, x2, x3
vle8.v v1, (x1)
vadd.vv v2, v1, v1
vadd.vx v3, v1, x2
vadd.vi v4, v1, 5
vse8.v v2, (x1)

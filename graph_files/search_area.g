# The area is a square with walls surrounding it

world = {} # the world frame

floor = {
    X: [0 0 0],
    shape: box,
    size: [10, 10, .1],
    color: [0 .166 .214],
    contact: true
}

marker(floor) {
    shape: marker,
    size: [.25],
    Q: [0 0 5]
}
wall_one(floor)  {
    Q: [4.87, 0, .5],
    shape: box,
    size: [.25,10,1],
    color: [.8 .8 .8],
    contact: true
} 
wall_two(floor)  {
    Q: "t(0 4.87 .5) d(90 0 0 1)",
    shape: box,
    size: [.25,10,1],
    color: [.8 .8 .8],
    contact: true
} 
wall_three(floor)  {
    Q: [-4.87, 0, .5],
    shape: box,
    size: [.25,10,1],
    color: [.8 .8 .8],
    contact: true
} 
wall_four(floor)  {
    Q: "t(0 -4.87 .5) d(90 0 0 1)",
    shape: box,
    size: [.25,10,1],
    color: [.8 .8 .8],
    contact: true
} 

# 0.9 x 0.9 m table with 3 x 3 cells of 0.3 m: a Panda reaches ~0.85 m, so every cell can be reached from
# one side of the table (with 2 x 2 m tables the middle and back cells could not). A 0.12 x 0.24 m character fits in a cell.
table_left(floor) {
    Q: "t(2.2 2.4 .2)",
    shape: box,
    size: [.9 .9 .2],
    color: [.8 .8 .8],
    contact: true
}
area_1_L(table_left) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t(-0.30  0.30 0.101)" }
area_2_L(table_left) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t( 0.00  0.30 0.101)" }
area_3_L(table_left) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t( 0.30  0.30 0.101)" }
area_4_L(table_left) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t(-0.30  0.00 0.101)" }
area_5_L(table_left) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t( 0.00  0.00 0.101)" }
area_6_L(table_left) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t( 0.30  0.00 0.101)" }
area_7_L(table_left) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t(-0.30 -0.30 0.101)" }
area_8_L(table_left) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t( 0.00 -0.30 0.101)" }
area_9_L(table_left) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t( 0.30 -0.30 0.101)" }


# 0.9 x 0.9 m table with 3 x 3 cells of 0.3 m: a Panda reaches ~0.85 m, so every cell can be reached from
# one side of the table (with 2 x 2 m tables the middle and back cells could not). A 0.12 x 0.24 m character fits in a cell.
table_right(floor) {
    Q: "t(2.2 -2.4 .2)",
    shape: box,
    size: [.9 .9 .2],
    color: [.8 .8 .8],
    contact: true
}
area_1_R(table_right) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t(-0.30  0.30 0.101)" }
area_2_R(table_right) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t( 0.00  0.30 0.101)" }
area_3_R(table_right) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t( 0.30  0.30 0.101)" }
area_4_R(table_right) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t(-0.30  0.00 0.101)" }
area_5_R(table_right) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t( 0.00  0.00 0.101)" }
area_6_R(table_right) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t( 0.30  0.00 0.101)" }
area_7_R(table_right) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t(-0.30 -0.30 0.101)" }
area_8_R(table_right) { shape: box, color: [.78 0 0], size: [.296 .296 .002], Q: "t( 0.00 -0.30 0.101)" }
area_9_R(table_right) { shape: box, color: [.2 .2 .8], size: [.296 .296 .002], Q: "t( 0.30 -0.30 0.101)" }



base_origin_1 (floor) { Q: "t(0.8 1.0 .15)" }
mobile_base_1 (base_origin_1) {
    joint: transXYPhi, limits: [-5 -5 -4 5 5 4],
    shape: box, size: [.5 .5 .2], color: [.2 .2 .2], contact: true
}
Prefix: "p1_"
# panda.g, its .yml and meshes/ sit next to this file (no machine-specific paths)
Include: <panda.g>
Prefix: False
Edit p1_panda_base (mobile_base_1) { Q: "t(0 0 .1)" }

base_origin_2 (floor) { Q: "t(0.8 -1.0 .15)" }
mobile_base_2 (base_origin_2) {
    joint: transXYPhi, limits: [-5 -5 -4 5 5 4],
    shape: box, size: [.5 .5 .2], color: [.3 .3 .3], contact: true
}
Prefix: "p2_"
# panda.g, its .yml and meshes/ sit next to this file (no machine-specific paths)
Include: <panda.g>
Prefix: False
Edit p2_panda_base (mobile_base_2) { Q: "t(0 0 .1)" }
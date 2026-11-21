# 36 characters (A-Z yellow, 0-9 green), parent frames char_<C> laid out on a grid at z = 0.
# Black discs on the top face = glyph bottom.  Black base layer = underside.
# Re-place a character by setting the X of char_<C>.

# digit '0'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_0: { X: "t(-1.0000 1.0000 0.0000)" }
char_0_s0(char_0): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_0_b0(char_0): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_0_s1(char_0): { Q: "t(0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_0_b1(char_0): { Q: "t(0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_0_s2(char_0): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_0_b2(char_0): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_0_s3(char_0): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_0_b3(char_0): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_0_s4(char_0): { Q: "t(0.0000 0.0000 0.0230) d(63.43 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0111, contact: 1 }
char_0_b4(char_0): { Q: "t(0.0000 0.0000 0.0030) d(63.43 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0020, contact: 1 }
char_0_hole0(char_0): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_0_hole1(char_0): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_0_bottom(char_0): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_0_grasp(char_0): { Q: "t(-0.0000 -0.1200 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '1'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_1: { X: "t(-0.7900 1.0000 0.0000)" }
char_1_s0(char_1): { Q: "t(0.0000 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_1_b0(char_1): { Q: "t(0.0000 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_1_s1(char_1): { Q: "t(-0.0300 0.0900 0.0230) d(-135.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0041, contact: 1 }
char_1_b1(char_1): { Q: "t(-0.0300 0.0900 0.0030) d(-135.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0007, contact: 1 }
char_1_hole0(char_1): { Q: "t(0.0000 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_1_bottom(char_1): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_1_grasp(char_1): { Q: "t(-0.0002 0.0261 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '2'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_2: { X: "t(-0.5800 1.0000 0.0000)" }
char_2_s0(char_2): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_2_b0(char_2): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_2_s1(char_2): { Q: "t(0.0600 0.0600 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_2_b1(char_2): { Q: "t(0.0600 0.0600 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_2_s2(char_2): { Q: "t(0.0000 0.0000 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_2_b2(char_2): { Q: "t(0.0000 0.0000 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_2_s3(char_2): { Q: "t(-0.0600 -0.0600 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_2_b3(char_2): { Q: "t(-0.0600 -0.0600 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_2_s4(char_2): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_2_b4(char_2): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_2_hole0(char_2): { Q: "t(-0.0499 -0.1050 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_2_hole1(char_2): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_2_bottom(char_2): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_2_grasp(char_2): { Q: "t(0.0000 0.0000 0.0200) d(-90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '3'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_3: { X: "t(-0.3700 1.0000 0.0000)" }
char_3_s0(char_3): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_3_b0(char_3): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_3_s1(char_3): { Q: "t(0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_3_b1(char_3): { Q: "t(0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_3_s2(char_3): { Q: "t(0.0000 -0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_3_b2(char_3): { Q: "t(0.0000 -0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_3_s3(char_3): { Q: "t(0.0180 0.0000 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1065 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0041, contact: 1 }
char_3_b3(char_3): { Q: "t(0.0180 0.0000 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1065 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0007, contact: 1 }
char_3_hole0(char_3): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_3_hole1(char_3): { Q: "t(0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_3_bottom(char_3): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_3_grasp(char_3): { Q: "t(0.0256 0.0000 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '4'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_4: { X: "t(-0.1600 1.0000 0.0000)" }
char_4_s0(char_4): { Q: "t(-0.0600 0.0600 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_4_b0(char_4): { Q: "t(-0.0600 0.0600 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_4_s1(char_4): { Q: "t(0.0000 0.0000 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_4_b1(char_4): { Q: "t(0.0000 0.0000 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_4_s2(char_4): { Q: "t(0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_4_b2(char_4): { Q: "t(0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_4_hole0(char_4): { Q: "t(0.0600 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_4_bottom(char_4): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_4_grasp(char_4): { Q: "t(0.0132 0.0001 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '5'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_5: { X: "t(0.0500 1.0000 0.0000)" }
char_5_s0(char_5): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_5_b0(char_5): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_5_s1(char_5): { Q: "t(-0.0600 0.0600 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_5_b1(char_5): { Q: "t(-0.0600 0.0600 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_5_s2(char_5): { Q: "t(0.0000 0.0000 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_5_b2(char_5): { Q: "t(0.0000 0.0000 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_5_s3(char_5): { Q: "t(0.0600 -0.0600 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_5_b3(char_5): { Q: "t(0.0600 -0.0600 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_5_s4(char_5): { Q: "t(0.0000 -0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_5_b4(char_5): { Q: "t(0.0000 -0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_5_hole0(char_5): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_5_hole1(char_5): { Q: "t(0.0499 -0.1050 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_5_bottom(char_5): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_5_grasp(char_5): { Q: "t(0.0000 0.0000 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '6'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_6: { X: "t(0.2600 1.0000 0.0000)" }
char_6_s0(char_6): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_6_b0(char_6): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_6_s1(char_6): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_6_b1(char_6): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_6_s2(char_6): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_6_b2(char_6): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_6_s3(char_6): { Q: "t(0.0600 -0.0600 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_6_b3(char_6): { Q: "t(0.0600 -0.0600 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_6_s4(char_6): { Q: "t(0.0000 0.0000 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_6_b4(char_6): { Q: "t(0.0000 0.0000 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_6_hole0(char_6): { Q: "t(-0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_6_hole1(char_6): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_6_bottom(char_6): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_6_grasp(char_6): { Q: "t(-0.0086 0.0002 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '7'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_7: { X: "t(0.4700 1.0000 0.0000)" }
char_7_s0(char_7): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_7_b0(char_7): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_7_s1(char_7): { Q: "t(0.0180 0.0000 0.0230) d(-109.29 0 0 1)", shape: ssBox, size: [0.2768 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0106, contact: 1 }
char_7_b1(char_7): { Q: "t(0.0180 0.0000 0.0030) d(-109.29 0 0 1)", shape: ssBox, size: [0.2768 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0019, contact: 1 }
char_7_hole0(char_7): { Q: "t(-0.0219 -0.1140 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_7_bottom(char_7): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_7_grasp(char_7): { Q: "t(0.0307 0.0357 0.0200) d(165.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '8'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_8: { X: "t(0.6800 1.0000 0.0000)" }
char_8_s0(char_8): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_8_b0(char_8): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_8_s1(char_8): { Q: "t(0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_8_b1(char_8): { Q: "t(0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_8_s2(char_8): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_8_b2(char_8): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_8_s3(char_8): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_8_b3(char_8): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_8_s4(char_8): { Q: "t(0.0000 0.0000 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_8_b4(char_8): { Q: "t(0.0000 0.0000 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_8_hole0(char_8): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_8_hole1(char_8): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_8_bottom(char_8): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_8_grasp(char_8): { Q: "t(0.0000 0.0000 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# digit '9'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_9: { X: "t(-1.0000 0.6800 0.0000)" }
char_9_s0(char_9): { Q: "t(0.0000 0.0000 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_9_b0(char_9): { Q: "t(0.0000 0.0000 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_9_s1(char_9): { Q: "t(-0.0600 0.0600 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_9_b1(char_9): { Q: "t(-0.0600 0.0600 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_9_s2(char_9): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_9_b2(char_9): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_9_s3(char_9): { Q: "t(0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0100, contact: 1 }
char_9_b3(char_9): { Q: "t(0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_9_s4(char_9): { Q: "t(0.0000 -0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [0 0.7 0.25], mass: 0.0055, contact: 1 }
char_9_b4(char_9): { Q: "t(0.0000 -0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_9_hole0(char_9): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_9_hole1(char_9): { Q: "t(0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_9_bottom(char_9): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_9_grasp(char_9): { Q: "t(0.0086 -0.0002 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'A'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_A: { X: "t(-0.7900 0.6800 0.0000)" }
char_A_s0(char_A): { Q: "t(-0.0300 0.0000 0.0230) d(75.96 0 0 1)", shape: ssBox, size: [0.2699 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0103, contact: 1 }
char_A_b0(char_A): { Q: "t(-0.0300 0.0000 0.0030) d(75.96 0 0 1)", shape: ssBox, size: [0.2699 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_A_s1(char_A): { Q: "t(0.0300 0.0000 0.0230) d(-75.96 0 0 1)", shape: ssBox, size: [0.2699 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0103, contact: 1 }
char_A_b1(char_A): { Q: "t(0.0300 0.0000 0.0030) d(-75.96 0 0 1)", shape: ssBox, size: [0.2699 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_A_s2(char_A): { Q: "t(0.0000 -0.0600 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0043, contact: 1 }
char_A_b2(char_A): { Q: "t(0.0000 -0.0600 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0008, contact: 1 }
char_A_hole0(char_A): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_A_hole1(char_A): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_A_bottom(char_A): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_A_grasp(char_A): { Q: "t(0.0317 -0.0070 0.0200) d(15.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'B'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_B: { X: "t(-0.5800 0.6800 0.0000)" }
char_B_s0(char_B): { Q: "t(-0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_B_b0(char_B): { Q: "t(-0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_B_s1(char_B): { Q: "t(-0.0150 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0043, contact: 1 }
char_B_b1(char_B): { Q: "t(-0.0150 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0008, contact: 1 }
char_B_s2(char_B): { Q: "t(0.0450 0.0900 0.0230) d(-63.43 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0034, contact: 1 }
char_B_b2(char_B): { Q: "t(0.0450 0.0900 0.0030) d(-63.43 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_B_s3(char_B): { Q: "t(0.0450 0.0300 0.0230) d(-116.57 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0034, contact: 1 }
char_B_b3(char_B): { Q: "t(0.0450 0.0300 0.0030) d(-116.57 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_B_s4(char_B): { Q: "t(-0.0150 0.0000 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0043, contact: 1 }
char_B_b4(char_B): { Q: "t(-0.0150 0.0000 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0008, contact: 1 }
char_B_s5(char_B): { Q: "t(0.0450 -0.0300 0.0230) d(-63.43 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0034, contact: 1 }
char_B_b5(char_B): { Q: "t(0.0450 -0.0300 0.0030) d(-63.43 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_B_s6(char_B): { Q: "t(0.0450 -0.0900 0.0230) d(-116.57 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0034, contact: 1 }
char_B_b6(char_B): { Q: "t(0.0450 -0.0900 0.0030) d(-116.57 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_B_s7(char_B): { Q: "t(-0.0150 -0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0043, contact: 1 }
char_B_b7(char_B): { Q: "t(-0.0150 -0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0008, contact: 1 }
char_B_hole0(char_B): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_B_hole1(char_B): { Q: "t(0.0274 -0.1050 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_B_bottom(char_B): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_B_grasp(char_B): { Q: "t(-0.0049 0.0000 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'C'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_C: { X: "t(-0.3700 0.6800 0.0000)" }
char_C_s0(char_C): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_C_b0(char_C): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_C_s1(char_C): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_C_b1(char_C): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_C_s2(char_C): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_C_b2(char_C): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_C_hole0(char_C): { Q: "t(-0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_C_hole1(char_C): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_C_bottom(char_C): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_C_grasp(char_C): { Q: "t(-0.0598 0.0000 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'D'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_D: { X: "t(-0.1600 0.6800 0.0000)" }
char_D_s0(char_D): { Q: "t(-0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_D_b0(char_D): { Q: "t(-0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_D_s1(char_D): { Q: "t(-0.0300 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.0825 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0032, contact: 1 }
char_D_b1(char_D): { Q: "t(-0.0300 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.0825 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_D_s2(char_D): { Q: "t(0.0300 0.0900 0.0230) d(-45.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0041, contact: 1 }
char_D_b2(char_D): { Q: "t(0.0300 0.0900 0.0030) d(-45.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0007, contact: 1 }
char_D_s3(char_D): { Q: "t(0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_D_b3(char_D): { Q: "t(0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_D_s4(char_D): { Q: "t(0.0300 -0.0900 0.0230) d(-135.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0041, contact: 1 }
char_D_b4(char_D): { Q: "t(0.0300 -0.0900 0.0030) d(-135.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0007, contact: 1 }
char_D_s5(char_D): { Q: "t(-0.0300 -0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.0825 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0032, contact: 1 }
char_D_b5(char_D): { Q: "t(-0.0300 -0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.0825 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_D_hole0(char_D): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_D_hole1(char_D): { Q: "t(0.0049 -0.1050 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_D_bottom(char_D): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_D_grasp(char_D): { Q: "t(-0.0598 0.0000 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'E'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_E: { X: "t(0.0500 0.6800 0.0000)" }
char_E_s0(char_E): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_E_b0(char_E): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_E_s1(char_E): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_E_b1(char_E): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_E_s2(char_E): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_E_b2(char_E): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_E_s3(char_E): { Q: "t(-0.0150 0.0000 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0043, contact: 1 }
char_E_b3(char_E): { Q: "t(-0.0150 0.0000 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0008, contact: 1 }
char_E_hole0(char_E): { Q: "t(-0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_E_hole1(char_E): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_E_bottom(char_E): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_E_grasp(char_E): { Q: "t(-0.0249 0.0000 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'F'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_F: { X: "t(0.2600 0.6800 0.0000)" }
char_F_s0(char_F): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_F_b0(char_F): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_F_s1(char_F): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_F_b1(char_F): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_F_s2(char_F): { Q: "t(-0.0150 0.0000 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0043, contact: 1 }
char_F_b2(char_F): { Q: "t(-0.0150 0.0000 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1125 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0008, contact: 1 }
char_F_hole0(char_F): { Q: "t(-0.0600 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_F_bottom(char_F): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_F_grasp(char_F): { Q: "t(-0.0601 0.0307 0.0200) d(5.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'G'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_G: { X: "t(0.4700 0.6800 0.0000)" }
char_G_s0(char_G): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_G_b0(char_G): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_G_s1(char_G): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_G_b1(char_G): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_G_s2(char_G): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_G_b2(char_G): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_G_s3(char_G): { Q: "t(0.0600 -0.0720 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.1185 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0045, contact: 1 }
char_G_b3(char_G): { Q: "t(0.0600 -0.0720 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.1185 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0008, contact: 1 }
char_G_s4(char_G): { Q: "t(0.0330 -0.0240 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.0765 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0029, contact: 1 }
char_G_b4(char_G): { Q: "t(0.0330 -0.0240 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.0765 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0005, contact: 1 }
char_G_hole0(char_G): { Q: "t(-0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_G_hole1(char_G): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_G_bottom(char_G): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_G_grasp(char_G): { Q: "t(-0.0602 -0.0140 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'H'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_H: { X: "t(0.6800 0.6800 0.0000)" }
char_H_s0(char_H): { Q: "t(-0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_H_b0(char_H): { Q: "t(-0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_H_s1(char_H): { Q: "t(0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_H_b1(char_H): { Q: "t(0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_H_s2(char_H): { Q: "t(0.0000 0.0000 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_H_b2(char_H): { Q: "t(0.0000 0.0000 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_H_hole0(char_H): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_H_hole1(char_H): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_H_bottom(char_H): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_H_grasp(char_H): { Q: "t(0.0000 0.0000 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'I'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_I: { X: "t(-1.0000 0.3600 0.0000)" }
char_I_s0(char_I): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_I_b0(char_I): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_I_s1(char_I): { Q: "t(0.0000 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_I_b1(char_I): { Q: "t(0.0000 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_I_s2(char_I): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_I_b2(char_I): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_I_hole0(char_I): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_I_hole1(char_I): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_I_bottom(char_I): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_I_grasp(char_I): { Q: "t(0.0000 0.0000 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'J'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_J: { X: "t(-0.7900 0.3600 0.0000)" }
char_J_s0(char_J): { Q: "t(0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_J_b0(char_J): { Q: "t(0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_J_s1(char_J): { Q: "t(0.0000 -0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_J_b1(char_J): { Q: "t(0.0000 -0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_J_s2(char_J): { Q: "t(-0.0600 -0.0900 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.0825 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0032, contact: 1 }
char_J_b2(char_J): { Q: "t(-0.0600 -0.0900 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.0825 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_J_hole0(char_J): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_J_hole1(char_J): { Q: "t(0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_J_bottom(char_J): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_J_grasp(char_J): { Q: "t(0.0600 -0.0536 0.0200) d(175.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'K'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_K: { X: "t(-0.5800 0.3600 0.0000)" }
char_K_s0(char_K): { Q: "t(-0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_K_b0(char_K): { Q: "t(-0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_K_s1(char_K): { Q: "t(0.0000 0.0600 0.0230) d(45.00 0 0 1)", shape: ssBox, size: [0.1922 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0074, contact: 1 }
char_K_b1(char_K): { Q: "t(0.0000 0.0600 0.0030) d(45.00 0 0 1)", shape: ssBox, size: [0.1922 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0013, contact: 1 }
char_K_s2(char_K): { Q: "t(0.0180 -0.0420 0.0230) d(-61.70 0 0 1)", shape: ssBox, size: [0.1997 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0076, contact: 1 }
char_K_b2(char_K): { Q: "t(0.0180 -0.0420 0.0030) d(-61.70 0 0 1)", shape: ssBox, size: [0.1997 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0013, contact: 1 }
char_K_hole0(char_K): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_K_hole1(char_K): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_K_bottom(char_K): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_K_grasp(char_K): { Q: "t(0.0009 -0.0099 0.0200) d(30.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'L'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_L: { X: "t(-0.3700 0.3600 0.0000)" }
char_L_s0(char_L): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_L_b0(char_L): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_L_s1(char_L): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_L_b1(char_L): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_L_hole0(char_L): { Q: "t(-0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_L_hole1(char_L): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_L_bottom(char_L): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_L_grasp(char_L): { Q: "t(-0.0599 -0.0422 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'M'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_M: { X: "t(-0.1600 0.3600 0.0000)" }
char_M_s0(char_M): { Q: "t(-0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_M_b0(char_M): { Q: "t(-0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_M_s1(char_M): { Q: "t(-0.0300 0.0750 0.0230) d(-56.31 0 0 1)", shape: ssBox, size: [0.1307 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0050, contact: 1 }
char_M_b1(char_M): { Q: "t(-0.0300 0.0750 0.0030) d(-56.31 0 0 1)", shape: ssBox, size: [0.1307 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0009, contact: 1 }
char_M_s2(char_M): { Q: "t(0.0300 0.0750 0.0230) d(56.31 0 0 1)", shape: ssBox, size: [0.1307 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0050, contact: 1 }
char_M_b2(char_M): { Q: "t(0.0300 0.0750 0.0030) d(56.31 0 0 1)", shape: ssBox, size: [0.1307 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0009, contact: 1 }
char_M_s3(char_M): { Q: "t(0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_M_b3(char_M): { Q: "t(0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_M_hole0(char_M): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_M_hole1(char_M): { Q: "t(0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_M_bottom(char_M): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_M_grasp(char_M): { Q: "t(-0.0600 0.0049 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'N'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_N: { X: "t(0.0500 0.3600 0.0000)" }
char_N_s0(char_N): { Q: "t(-0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_N_b0(char_N): { Q: "t(-0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_N_s1(char_N): { Q: "t(0.0000 0.0000 0.0230) d(-63.43 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0111, contact: 1 }
char_N_b1(char_N): { Q: "t(0.0000 0.0000 0.0030) d(-63.43 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0020, contact: 1 }
char_N_s2(char_N): { Q: "t(0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_N_b2(char_N): { Q: "t(0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_N_hole0(char_N): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_N_hole1(char_N): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_N_bottom(char_N): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_N_grasp(char_N): { Q: "t(-0.0600 -0.0203 0.0200) d(5.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'O'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_O: { X: "t(0.2600 0.3600 0.0000)" }
char_O_s0(char_O): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_O_b0(char_O): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_O_s1(char_O): { Q: "t(0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_O_b1(char_O): { Q: "t(0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_O_s2(char_O): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_O_b2(char_O): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_O_s3(char_O): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_O_b3(char_O): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_O_hole0(char_O): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_O_hole1(char_O): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_O_bottom(char_O): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_O_grasp(char_O): { Q: "t(0.0600 0.0000 0.0200) d(180.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'P'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_P: { X: "t(0.4700 0.3600 0.0000)" }
char_P_s0(char_P): { Q: "t(-0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_P_b0(char_P): { Q: "t(-0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_P_s1(char_P): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_P_b1(char_P): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_P_s2(char_P): { Q: "t(0.0600 0.0600 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_P_b2(char_P): { Q: "t(0.0600 0.0600 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_P_s3(char_P): { Q: "t(0.0000 0.0000 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_P_b3(char_P): { Q: "t(0.0000 0.0000 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_P_hole0(char_P): { Q: "t(-0.0600 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_P_bottom(char_P): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_P_grasp(char_P): { Q: "t(-0.0104 0.0002 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'Q'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_Q: { X: "t(0.6800 0.3600 0.0000)" }
char_Q_s0(char_Q): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_Q_b0(char_Q): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_Q_s1(char_Q): { Q: "t(0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_Q_b1(char_Q): { Q: "t(0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_Q_s2(char_Q): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_Q_b2(char_Q): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_Q_s3(char_Q): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_Q_b3(char_Q): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_Q_s4(char_Q): { Q: "t(0.0420 -0.1020 0.0230) d(-45.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0041, contact: 1 }
char_Q_b4(char_Q): { Q: "t(0.0420 -0.1020 0.0030) d(-45.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0007, contact: 1 }
char_Q_hole0(char_Q): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_Q_hole1(char_Q): { Q: "t(0.0619 -0.1320 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_Q_bottom(char_Q): { Q: "t(0 -0.1320 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_Q_grasp(char_Q): { Q: "t(0.0599 -0.0119 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'R'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_R: { X: "t(-1.0000 0.0400 0.0000)" }
char_R_s0(char_R): { Q: "t(-0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_R_b0(char_R): { Q: "t(-0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_R_s1(char_R): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_R_b1(char_R): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_R_s2(char_R): { Q: "t(0.0600 0.0600 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_R_b2(char_R): { Q: "t(0.0600 0.0600 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_R_s3(char_R): { Q: "t(0.0000 0.0000 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_R_b3(char_R): { Q: "t(0.0000 0.0000 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_R_s4(char_R): { Q: "t(0.0000 -0.0600 0.0230) d(-45.00 0 0 1)", shape: ssBox, size: [0.1922 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0074, contact: 1 }
char_R_b4(char_R): { Q: "t(0.0000 -0.0600 0.0030) d(-45.00 0 0 1)", shape: ssBox, size: [0.1922 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0013, contact: 1 }
char_R_hole0(char_R): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_R_hole1(char_R): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_R_bottom(char_R): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_R_grasp(char_R): { Q: "t(-0.0082 0.1200 0.0200) d(90.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'S'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_S: { X: "t(-0.7900 0.0400 0.0000)" }
char_S_s0(char_S): { Q: "t(0.0000 0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_S_b0(char_S): { Q: "t(0.0000 0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_S_s1(char_S): { Q: "t(-0.0600 0.0840 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.0945 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0036, contact: 1 }
char_S_b1(char_S): { Q: "t(-0.0600 0.0840 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.0945 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_S_s2(char_S): { Q: "t(0.0000 -0.0000 0.0230) d(-38.66 0 0 1)", shape: ssBox, size: [0.1762 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0067, contact: 1 }
char_S_b2(char_S): { Q: "t(0.0000 -0.0000 0.0030) d(-38.66 0 0 1)", shape: ssBox, size: [0.1762 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0012, contact: 1 }
char_S_s3(char_S): { Q: "t(0.0600 -0.0840 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.0945 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0036, contact: 1 }
char_S_b3(char_S): { Q: "t(0.0600 -0.0840 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.0945 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_S_s4(char_S): { Q: "t(0.0000 -0.1200 0.0230) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_S_b4(char_S): { Q: "t(0.0000 -0.1200 0.0030) d(180.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_S_hole0(char_S): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_S_hole1(char_S): { Q: "t(0.0499 -0.1056 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_S_bottom(char_S): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_S_grasp(char_S): { Q: "t(0.0000 -0.0000 0.0200) d(51.34 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'T'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_T: { X: "t(-0.5800 0.0400 0.0000)" }
char_T_s0(char_T): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_T_b0(char_T): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_T_s1(char_T): { Q: "t(0.0000 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_T_b1(char_T): { Q: "t(0.0000 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_T_hole0(char_T): { Q: "t(0.0000 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_T_bottom(char_T): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_T_grasp(char_T): { Q: "t(0.0000 0.0422 0.0200) d(5.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'U'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_U: { X: "t(-0.3700 0.0400 0.0000)" }
char_U_s0(char_U): { Q: "t(-0.0600 0.0000 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_U_b0(char_U): { Q: "t(-0.0600 0.0000 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_U_s1(char_U): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_U_b1(char_U): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_U_s2(char_U): { Q: "t(0.0600 0.0000 0.0230) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0100, contact: 1 }
char_U_b2(char_U): { Q: "t(0.0600 0.0000 0.0030) d(90.00 0 0 1)", shape: ssBox, size: [0.2625 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_U_hole0(char_U): { Q: "t(-0.0499 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_U_hole1(char_U): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_U_bottom(char_U): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_U_grasp(char_U): { Q: "t(-0.0600 -0.0256 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'V'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_V: { X: "t(-0.1600 0.0400 0.0000)" }
char_V_s0(char_V): { Q: "t(-0.0300 0.0000 0.0230) d(-75.96 0 0 1)", shape: ssBox, size: [0.2699 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0103, contact: 1 }
char_V_b0(char_V): { Q: "t(-0.0300 0.0000 0.0030) d(-75.96 0 0 1)", shape: ssBox, size: [0.2699 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_V_s1(char_V): { Q: "t(0.0300 0.0000 0.0230) d(75.96 0 0 1)", shape: ssBox, size: [0.2699 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0103, contact: 1 }
char_V_b1(char_V): { Q: "t(0.0300 0.0000 0.0030) d(75.96 0 0 1)", shape: ssBox, size: [0.2699 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_V_hole0(char_V): { Q: "t(0.0000 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_V_bottom(char_V): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_V_grasp(char_V): { Q: "t(0.0314 0.0071 0.0200) d(165.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'W'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_W: { X: "t(0.0500 0.0400 0.0000)" }
char_W_s0(char_W): { Q: "t(-0.0450 0.0000 0.0230) d(-82.87 0 0 1)", shape: ssBox, size: [0.2644 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0101, contact: 1 }
char_W_b0(char_W): { Q: "t(-0.0450 0.0000 0.0030) d(-82.87 0 0 1)", shape: ssBox, size: [0.2644 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_W_s1(char_W): { Q: "t(-0.0150 -0.0900 0.0230) d(63.43 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0034, contact: 1 }
char_W_b1(char_W): { Q: "t(-0.0150 -0.0900 0.0030) d(63.43 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_W_s2(char_W): { Q: "t(0.0150 -0.0900 0.0230) d(-63.43 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0034, contact: 1 }
char_W_b2(char_W): { Q: "t(0.0150 -0.0900 0.0030) d(-63.43 0 0 1)", shape: ssBox, size: [0.0896 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0006, contact: 1 }
char_W_s3(char_W): { Q: "t(0.0450 0.0000 0.0230) d(82.87 0 0 1)", shape: ssBox, size: [0.2644 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0101, contact: 1 }
char_W_b3(char_W): { Q: "t(0.0450 0.0000 0.0030) d(82.87 0 0 1)", shape: ssBox, size: [0.2644 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0018, contact: 1 }
char_W_hole0(char_W): { Q: "t(-0.0214 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_W_hole1(char_W): { Q: "t(0.0214 -0.1080 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_W_bottom(char_W): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_W_grasp(char_W): { Q: "t(0.0418 -0.0276 0.0200) d(170.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'X'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_X: { X: "t(0.2600 0.0400 0.0000)" }
char_X_s0(char_X): { Q: "t(0.0000 0.0000 0.0230) d(63.43 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0111, contact: 1 }
char_X_b0(char_X): { Q: "t(0.0000 0.0000 0.0030) d(63.43 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0020, contact: 1 }
char_X_s1(char_X): { Q: "t(0.0000 0.0000 0.0230) d(-63.43 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0111, contact: 1 }
char_X_b1(char_X): { Q: "t(0.0000 0.0000 0.0030) d(-63.43 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0020, contact: 1 }
char_X_s2(char_X): { Q: "t(0.0000 0.0000 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.0465 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0018, contact: 1 }
char_X_b2(char_X): { Q: "t(0.0000 0.0000 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.0465 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0003, contact: 1 }
char_X_hole0(char_X): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_X_hole1(char_X): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_X_bottom(char_X): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_X_grasp(char_X): { Q: "t(0.0000 0.0000 0.0200) d(0.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'Y'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_Y: { X: "t(0.4700 0.0400 0.0000)" }
char_Y_s0(char_Y): { Q: "t(-0.0300 0.0900 0.0230) d(-45.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0041, contact: 1 }
char_Y_b0(char_Y): { Q: "t(-0.0300 0.0900 0.0030) d(-45.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0007, contact: 1 }
char_Y_s1(char_Y): { Q: "t(0.0300 0.0900 0.0230) d(45.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0041, contact: 1 }
char_Y_b1(char_Y): { Q: "t(0.0300 0.0900 0.0030) d(45.00 0 0 1)", shape: ssBox, size: [0.1074 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0007, contact: 1 }
char_Y_s2(char_Y): { Q: "t(0.0000 -0.0300 0.0230) d(-90.00 0 0 1)", shape: ssBox, size: [0.2025 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0077, contact: 1 }
char_Y_b2(char_Y): { Q: "t(0.0000 -0.0300 0.0030) d(-90.00 0 0 1)", shape: ssBox, size: [0.2025 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0014, contact: 1 }
char_Y_hole0(char_Y): { Q: "t(0.0000 -0.1065 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_Y_bottom(char_Y): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_Y_grasp(char_Y): { Q: "t(0.0000 0.0318 0.0200) d(5.00 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

# letter 'Z'  (0.120 x 0.240 m, strokes 0.0225 wide, 0.04 thick)
char_Z: { X: "t(0.6800 0.0400 0.0000)" }
char_Z_s0(char_Z): { Q: "t(0.0000 0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_Z_b0(char_Z): { Q: "t(0.0000 0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_Z_s1(char_Z): { Q: "t(0.0000 0.0000 0.0230) d(-116.57 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0111, contact: 1 }
char_Z_b1(char_Z): { Q: "t(0.0000 0.0000 0.0030) d(-116.57 0 0 1)", shape: ssBox, size: [0.2908 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0020, contact: 1 }
char_Z_s2(char_Z): { Q: "t(0.0000 -0.1200 0.0230) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0340 0.004], color: [1 0.85 0], mass: 0.0055, contact: 1 }
char_Z_b2(char_Z): { Q: "t(0.0000 -0.1200 0.0030) d(0.00 0 0 1)", shape: ssBox, size: [0.1425 0.0225 0.0060 0.0029], color: [0.05 0.05 0.05], mass: 0.0010, contact: 1 }
char_Z_hole0(char_Z): { Q: "t(-0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_Z_hole1(char_Z): { Q: "t(0.0499 -0.1200 0.0405)", shape: cylinder, size: [.001 0.0067], color: [0 0 0], contact: 0 }  # glyph-bottom mark
char_Z_bottom(char_Z): { Q: "t(0 -0.1200 0.0200)", shape: marker, size: [.03] }  # glyph bottom; +y points to the glyph top
char_Z_grasp(char_Z): { Q: "t(0.0000 0.0000 0.0200) d(-26.57 0 0 1)", shape: marker, size: [.02] }  # x = closing direction, z = up

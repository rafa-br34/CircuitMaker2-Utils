module NOT(A, Y);
input A;
output Y = ~A;
endmodule

module REG(CLK, IS, OS);
input CLK, IS;
output reg OS;
always @(posedge CLK)
	OS <= IS;
endmodule

module NOR_2(A, B, Y);
input A, B;
output Y = ~(A | B);
endmodule

module NOR_3(A, B, C, Y);
input A, B, C;
output Y = ~(A | B | C);
endmodule

module NOR_4(A, B, C, D, Y);
input A, B, C, D;
output Y = ~(A | B | C | D);
endmodule

module NOR_5(A, B, C, D, E, Y);
input A, B, C, D, E;
output Y = ~(A | B | C | D | E);
endmodule

module NOR_6(A, B, C, D, E, F, Y);
input A, B, C, D, E, F;
output Y = ~(A | B | C | D | E | F);
endmodule


module OR_2(A, B, Y);
input A, B;
output Y = A | B;
endmodule

module OR_3(A, B, C, Y);
input A, B, C;
output Y = A | B | C;
endmodule

module OR_4(A, B, C, D, Y);
input A, B, C, D;
output Y = A | B | C | D;
endmodule

module OR_5(A, B, C, D, E, Y);
input A, B, C, D, E;
output Y = A | B | C | D | E;
endmodule

module OR_6(A, B, C, D, E, F, Y);
input A, B, C, D, E, F;
output Y = A | B | C | D | E | F;
endmodule


module AND_2(A, B, Y);
input A, B;
output Y = A & B;
endmodule

module AND_3(A, B, C, Y);
input A, B, C;
output Y = A & B & C;
endmodule

module AND_4(A, B, C, D, Y);
input A, B, C, D;
output Y = A & B & C & D;
endmodule

module AND_5(A, B, C, D, E, Y);
input A, B, C, D, E;
output Y = A & B & C & D & E;
endmodule

module AND_6(A, B, C, D, E, F, Y);
input A, B, C, D, E, F;
output Y = A & B & C & D & E & F;
endmodule


module XOR_2(A, B, Y);
input A, B;
output Y = A ^ B;
endmodule

module XOR_3(A, B, C, Y);
input A, B, C;
output Y = A ^ B ^ C;
endmodule

module XOR_4(A, B, C, D, Y);
input A, B, C, D;
output Y = A ^ B ^ C ^ D;
endmodule

module XOR_5(A, B, C, D, E, Y);
input A, B, C, D, E;
output Y = A ^ B ^ C ^ D ^ E;
endmodule

module XOR_6(A, B, C, D, E, F, Y);
input A, B, C, D, E, F;
output Y = A ^ B ^ C ^ D ^ E ^ F;
endmodule


module NAND_2(A, B, Y);
input A, B;
output Y = ~(A & B);
endmodule

module NAND_3(A, B, C, Y);
input A, B, C;
output Y = ~(A & B & C);
endmodule

module NAND_4(A, B, C, D, Y);
input A, B, C, D;
output Y = ~(A & B & C & D);
endmodule

module NAND_5(A, B, C, D, E, Y);
input A, B, C, D, E;
output Y = ~(A & B & C & D & E);
endmodule

module NAND_6(A, B, C, D, E, F, Y);
input A, B, C, D, E, F;
output Y = ~(A & B & C & D & E & F);
endmodule


module XNOR_2(A, B, Y);
input A, B;
output Y = ~(A ^ B);
endmodule

module XNOR_3(A, B, C, Y);
input A, B, C;
output Y = ~(A ^ B ^ C);
endmodule

module XNOR_4(A, B, C, D, Y);
input A, B, C, D;
output Y = ~(A ^ B ^ C ^ D);
endmodule

module XNOR_5(A, B, C, D, E, Y);
input A, B, C, D, E;
output Y = ~(A ^ B ^ C ^ D ^ E);
endmodule

module XNOR_6(A, B, C, D, E, F, Y);
input A, B, C, D, E, F;
output Y = ~(A ^ B ^ C ^ D ^ E ^ F);
endmodule
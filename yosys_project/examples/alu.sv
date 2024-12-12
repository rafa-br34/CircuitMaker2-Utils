parameter BITS = 8;

typedef enum { OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_MOD, OP_SHR, OP_SHL } OperationType;

module alu(input wire [BITS-1:0] a, b, input wire [2:0] operation, output wire [BITS-1:0] result);
	always_comb begin
		case (operation)
			OP_ADD: result = a + b;
			OP_SUB: result = a - b;
			OP_MUL: result = a * b;
			OP_DIV: result = a / b;
			OP_MOD: result = a % b;

			OP_SHR: result = a >> b;
			OP_SHL: result = a << b;

			default: result = 0;
		endcase
	end
endmodule

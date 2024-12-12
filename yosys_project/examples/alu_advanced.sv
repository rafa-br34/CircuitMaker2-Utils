parameter BITS = 16;

typedef enum { OP_ADD, OP_SUB, OP_MUL, OP_AND, OP_OR, OP_XOR, OP_SHF, OP_ROT } OperationType;

module alu(input wire [BITS-1:0] a, b, input wire [2:0] operation, output wire [BITS-1:0] result, output reg signed [BITS-1:0] excess, output wire zero, parity, negative, carry, overflow);
	wire [BITS * 2 - 1:0] extended_result = 0;
	
	const integer full_mask = (1 << BITS) - 1;
	const integer is_negative = b >> (BITS - 1);
	const integer negative_value = (full_mask - b + 1);
	
	const integer clamped_neg = negative_value >= BITS ? BITS : negative_value;
	const integer clamped_pos = b >= BITS ? BITS : b;

	const integer rot_left = negative_value % BITS;
	const integer rot_right = b % BITS;

	always_comb begin
		overflow = 0;
		excess = 0;
		carry = 0;

		case (operation)
			OP_ADD: {carry, result} = a + b;
			OP_SUB: {carry, result} = a - b;

			OP_MUL: begin
				extended_result = a * b;
				result = extended_result[BITS - 1:0];
				excess = extended_result[BITS * 2 - 1:BITS];
			end

			OP_AND: result = a & b;
			OP_OR:  result = a | b;
			OP_XOR: result = a ^ b;

			OP_SHF: begin
				if (is_negative) begin
					excess = a << (BITS - clamped_neg);
					result = a >> clamped_neg;
					carry = excess > 0;
				end else begin
					excess = a >> (BITS - clamped_pos);
					result = a << clamped_pos;
					carry = excess > 0;
				end
			end

			OP_ROT: begin
				if (is_negative) begin
					result = (a << rot_left) | (a >> (BITS - rot_left));
				end else begin
					result = (a >> rot_right) | (a << (BITS - rot_right));
				end
			end
		endcase

		if (operation == OP_ADD || operation == OP_SUB) begin
			excess = carry ? 1 : 0;
			overflow = (a[BITS - 1] ^ result[BITS - 1]);
		end

		negative = result >> (BITS - 1);
		parity = result & 1;
		zero = (result == 0);
	end
endmodule

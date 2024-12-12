module xorshift32(input wire[31:0] state, output wire[31:0] result);
	always_comb begin
		result = state;
		result ^= result << 13;
		result ^= result >> 17;
		result ^= result << 5;
	end
endmodule

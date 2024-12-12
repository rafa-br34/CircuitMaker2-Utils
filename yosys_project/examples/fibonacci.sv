parameter SIZE = 32;

module fibonacci(input wire clock, reset, output wire[SIZE-1:0] state);
	logic[SIZE-1:0] a = 0;
	logic[SIZE-1:0] b = 0;

	always @(posedge clock or posedge reset) begin
		if (reset) begin
			a <= 1;
			b <= 0;
		end else begin
			a <= b + a;
			b <= a;
		end
	end

	always @(posedge clock) begin
		state <= a;
	end
endmodule
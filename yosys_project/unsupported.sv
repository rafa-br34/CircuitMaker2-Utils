
// Self triggering, unsupported because of BLIFParser.py
module self_triggering(inout reg clock);
	always @(posedge clock) begin
		clock <= ~clock; // blocking assignment should inhibit this behaviour
	end
endmodule

module sequential_logic(input wire clock, output reg result_sync, result_async);
	initial begin
		result_sync = 0;
		result_async = 0;
	end

	always @(posedge clock) begin
		for (int i = 0; i < 128; i++) begin
			result_sync = !result_sync;
			result_async <= !result_async;
		end
	end
endmodule
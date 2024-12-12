module golcell(input wire [7:0] neighbors, input wire clk, output logic state);
	wire [2:0] live_neighbors = 0;

	always @(posedge clk) begin
		for (integer idx = 0; idx < 8; idx++) begin
			live_neighbors += neighbors[idx];
		end

		if (state && (live_neighbors < 2 || live_neighbors > 3))
			state <= 0;
		else if (!state && live_neighbors == 3)
			state <= 1;
	end
endmodule
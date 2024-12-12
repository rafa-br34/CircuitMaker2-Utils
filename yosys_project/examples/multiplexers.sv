parameter BUS_SIZE = 12 + 8;
parameter IDX_SIZE = 4;
parameter IDX_COUNT = 4;

module multiplexer(input wire[BUS_SIZE * IDX_COUNT - 1:0] input_bus, input wire[IDX_SIZE-1:0] index, output wire[BUS_SIZE - 1:0] output_bus);
	always_comb begin
		output_bus = 0;

		for (int i = 0; i < IDX_COUNT; i++) begin
			if (index == i)
				output_bus = input_bus[i * BUS_SIZE:(i + 1) * BUS_SIZE];
		end
	end
endmodule

module demultiplexer(input wire[BUS_SIZE-1:0] input_bus, input wire[IDX_SIZE-1:0] index, output wire[IDX_COUNT * BUS_SIZE - 1:0] output_bus);
	always_comb begin
		output_bus = 0;

		for (int i = 0; i < IDX_COUNT; i++) begin
			if (index == i)
				output_bus[i * BUS_SIZE:(i + 1) * BUS_SIZE] = input_bus;
		end
	end
endmodule
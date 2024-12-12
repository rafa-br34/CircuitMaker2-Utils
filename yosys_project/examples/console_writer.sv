module console_writer(input wire clock, write, clear, input wire[7:0] character, output logic[7:0] location, output wire write_flag, clear_flag);
	logic [4:0] index = 0;
	logic [2:0] line = 0;
	
	always @(posedge clock) begin
		clear_flag = clear;
		write_flag = write;

		if (write) begin
			case (character)
				10: line <= line + 1;
				13: index <= 0;

				default: index <= index + 1;
			endcase
		end else if (clear) begin
			line <= 0;
			index <= 0;
		end

		if (index >= 31) begin
			index <= 0;
			line <= line + 1;
		end

		location = (line << 5) | index;
	end
endmodule
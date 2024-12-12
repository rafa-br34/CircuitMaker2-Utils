parameter BANDWIDTH = 1;
parameter WORD_SIZE = 2;
parameter BUFFER_OUT = 2;
parameter BUFFER_IN = 2;

parameter BUF_BITS_OUT = WORD_SIZE * BUFFER_OUT;
parameter BUF_BITS_IN = WORD_SIZE * BUFFER_IN;

parameter BUF_BITS_OUT_LOG2 = $clog2(BUF_BITS_OUT + 1);
parameter BUF_BITS_IN_LOG2 = $clog2(BUF_BITS_IN + 1);

module transceiver(
	input wire clock, reset,
	input wire adv_recv, adv_send,
	output reg recv_buff_ready, send_buff_ready,
	output wire[WORD_SIZE - 1:0] recv, input wire[WORD_SIZE - 1:0] send,
	input wire[BANDWIDTH - 1:0] rx, output wire[BANDWIDTH - 1:0] tx,

	output wire[BUF_BITS_OUT_LOG2 - 1:0] dbg0
);
	logic[BUF_BITS_OUT_LOG2 - 1:0] buffer_out_idx = 0;
	logic[BUF_BITS_OUT - 1:0] buffer_out = 0;
	
	logic[BUF_BITS_IN_LOG2 - 1:0] buffer_in_idx = 0;
	logic[BUF_BITS_IN - 1:0] buffer_in = 0;

	const int bit_mask = (1 << BANDWIDTH) - 1;
	int offset = 0;
	int mask = 0;


	wire[BUF_BITS_OUT_LOG2 - 1:0] buffer_out_free;
	assign buffer_out_free = BUF_BITS_OUT - buffer_out_idx;
	assign dbg0 = buffer_out_free;

	// Transmit (TX)
	always @(posedge clock) begin
		if (adv_send && buffer_out_free > WORD_SIZE) begin
			buffer_out[buffer_out_idx + WORD_SIZE:buffer_out_idx] = send;
			buffer_out_idx += WORD_SIZE;
		end
		
		if (buffer_out_free > WORD_SIZE)
			send_buff_ready <= 1;
		else
			send_buff_ready <= 0;

		// Send bits
		if (buffer_out_idx) begin
			offset = buffer_out_idx - WORD_SIZE;
			mask = bit_mask << offset;
			
			tx <= (buffer_out >> buffer_out_idx) & bit_mask;//(buffer_out & mask) >> offset;
			buffer_out_idx -= BANDWIDTH;
		end else
			tx <= 0;
	end
	/*
	// Receive (RX)
	always @(posedge clock) begin
		if (adv_recv && buffer_in_idx) begin
			recv <= buffer_in[buffer_in_idx + WORD_SIZE:buffer_in_idx];
			buffer_in_idx -= WORD_SIZE;
		end

		if (0)
			recv_buff_ready <= 1;
		else
			recv_buff_ready <= 0;

		/
		// Receive bits
		if (buffer_in_bit + 1 == WORD_SIZE) begin
			buffer_in_idx <= buffer_in_idx + 1;
			buffer_in_bit <= 0;
		end
		
		offset = BANDWIDTH * buffer_in_idx * WORD_SIZE + buffer_in_bit;
		buffer_in[offset:offset + BANDWIDTH] <= rx;
		/
	end
	*/
endmodule
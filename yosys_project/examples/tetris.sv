parameter SCREEN_X = 10;
parameter SCREEN_Y = 20;
parameter CYCLES_PER_TICK = 2;

typedef bit[63:0] uint64;

module tetris(
	input wire clock, reset,
	output logic[SCREEN_X * SCREEN_Y - 1:0] screen,
	input wire flag_left, flag_right, flag_rotate, flag_place,
	//input wire[7:0] rng
	output wire[2:0] dbg0
);
	logic[$clog2(CYCLES_PER_TICK) - 1:0] current_cycle = 0;
	logic[$clog2(SCREEN_Y + 4) - 1:0] current_pos_y = 0;
	logic[$clog2(SCREEN_X + 2) - 1:0] current_pos_x;
	logic[SCREEN_X * SCREEN_Y - 1:0] board = 0;
	logic[2:0] current_tetromino = 0;
	logic[1:0] current_rotation = 0;

	const bit[SCREEN_X - 1:0] row_mask = (1 << SCREEN_X) - 1;
	const bit[64 * 7 - 1:0] tetrominoes = {
		64'h0F00222200F04444, // I
		64'h8E0064400E2044C0, // J
		64'h2E0044600E80C440, // L
		64'h6C00462006C08C40, // S
		64'hC60026400C604C80, // Z
		64'h4E0046400E404C40, // T
		64'hCC00CC00CC00CC00  // O
	};

	bit clear_enable = 0;
	int tetromino = 0;

	assign dbg0 = current_tetromino;
	
	always @(posedge clock) begin
		if (reset) begin
			board <= 0;
			offset_x <= 0;
			offset_y <= 0;
			current_cycle <= 0;
			current_pos_x <= 0;
			current_pos_y <= 0;
			current_rotation <= 0;
			current_tetromino <= 0;
		end else begin
			// Compute key presses
			if (flag_left)
				current_pos_x = current_pos_x < (SCREEN_X - 1) ? current_pos_x + 1 : current_pos_x;
			
			if (flag_right)
				current_pos_x = current_pos_x > 0 ? current_pos_x - 1 : current_pos_x;

			if (flag_rotate)
				current_rotation++;

			if (flag_place) begin
				current_tetromino = current_tetromino >= 6 ? 0 : current_tetromino + 1;
				current_pos_x = SCREEN_X / 2;
			end

			tetromino = tetrominoes[current_tetromino * 64 + current_rotation * 16 +: 16];
			
			// Draw tetromino
			for (int y = 0; y < 4; y++) begin
				for (int x = 0; x < 4; x++) begin
					board[(y + current_pos_y) * SCREEN_X + (x + current_pos_x)] = tetromino[y * 4 + x];
					board[(y + current_pos_y) * SCREEN_X + (x + current_pos_x)] <= 0;
				end
			end
			
			// Remove full rows
			if (clear_enable || 0)
				for (int y = SCREEN_Y - 1; y > 0; y--)
					if (board[(y + 1) * SCREEN_X - 1:y * SCREEN_X] == row_mask)
						board[(y + 1) * SCREEN_X - 1:y * SCREEN_X] = 0;
			
			/*
			for (int y = SCREEN_Y - 2; (y + 1) > 0; y--) begin
				for (int x = 0; x < SCREEN_X; x++) begin
					if (board[y * SCREEN_X + x] && !board[(y + 1) * SCREEN_X + x]) begin
						board[y * SCREEN_X + x] = 0;
						board[(y + 1) * SCREEN_X + x] = 1;
					end
				end
			end

			//board[current_pos_x] = 1;
			//*/
		end

		// Unconditionally update the screen at the end
		screen <= board;
	end
endmodule
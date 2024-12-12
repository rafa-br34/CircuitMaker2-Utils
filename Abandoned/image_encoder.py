import argparse
import pathlib
import base64
import numpy as np
import zlib

from tqdm import tqdm
from PIL import Image


c_screen_size = (128, 128)

def parse_arguments():
	parser = argparse.ArgumentParser(description="Utility to convert CM2 logic circuits into a graph")

	parser.add_argument(
		"--input", "-i",
		help="The file to use",
		required=True, type=str
	)

	return parser.parse_args()

class Memory:
	def __init__(self, word_size=16):
		self.content = []
		self.word_mask = (1 << word_size) - 1
		self.word_size = word_size

	def push_word(self, word):
		self.content.append(int(word))# & self.word_mask)

	def encode_hex(self):
		return ''.join([format(num, f"0{self.word_size // 4}x") for num in self.content])
	
	def encode_b64(self):
		return base64.b64encode(zlib.compressobj().compress(b''.join([int.to_bytes(val, self.word_size // 8) for val in self.content])))
		

def main():
	arguments = parse_arguments()

	img = Image.open(arguments.input)

	frame_count = getattr(img, "n_frames", 1)
	frame_array = np.ndarray((frame_count, *c_screen_size, 3), np.uint8)

	print(f"Loading {frame_count} frames...")
	for i in range(frame_count):
		img.seek(i)

		resized = img.convert("RGB").resize(c_screen_size)
		
		frame_array[i, :, :, :] = np.array(resized) / 255 * 64

	operations = []
	screen = np.ndarray((*c_screen_size, 3), np.uint8)

	print("Optimizing frames...")
	for frame in tqdm(frame_array):
		for (x, y) in np.argwhere(np.any(frame - screen, axis=-1)):
			operations.append((x, y, *frame[x, y]))

		screen = frame

	mem_xyr2 = Memory()
	mem_r4gb = Memory()

	print(f"Operation count: {len(operations)}")
	for (x, y, r, g, b) in operations:
		xyr2 = (r & 0b000011) | (y << 2) | (x << 8)
		r4gb = b | (g << 6) | ((r & 0b111100) << 10)
		#print(x, y, r, g, b)
		#print(bin(xyr2), bin(r4gb))
		mem_xyr2.push_word(xyr2)
		mem_r4gb.push_word(r4gb)

	print("Writing files...")
	pathlib.Path("mem_xyr2.hex.b64.txt").write_text(mem_xyr2.encode_hex())
	pathlib.Path("mem_r4gb.hex.b64.txt").write_text(mem_r4gb.encode_hex())


if __name__ == "__main__":
	main()
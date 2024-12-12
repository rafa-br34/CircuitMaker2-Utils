import schemdraw
import pyperclip
import logging
import random
import numpy as np
import enum
import math
import time

from simanneal import Annealer
from PIL import Image

import CircuitMaker as CM
import CircuitMakerAbstraction as CMA
import NetListReducer as NLR
import LogicMinifier as LM

logging.basicConfig(format="[%(levelname)s]<%(name)s> %(message)s", level=logging.DEBUG)


class memory_types(enum.Enum):
	readonly_flipflop = 0
	readonly_hardwired = 1
	readwrite_advanced = 2


def generate_memory(creation, bandwidth, bit_count, initial_data, technology=memory_types.readonly_flipflop):
	assert bit_count % bandwidth == 0, "bit_count must be divisible by the bandwidth"
	assert bandwidth <= bit_count, "bit_count must be higher or equal to the bandwidth"

	rowcount = int(bit_count / bandwidth)
	mem_outputs = []
	mem_inputs = []
	mem_rows = []
	mem_rw = []

	# memory outputs
	for o in range(bandwidth):
		mem_outputs.append(creation.add_component(CM.Component(CM.ComponentTypes.GATE_OR, position=[-2, 0, o])))

	# memory row index
	for r in range(rowcount):
		mem_rows.append(creation.add_component(CM.Component(CM.ComponentTypes.GATE_OR, position=[r, 0, -2])))

	for r in range(rowcount):
		for b in range(bandwidth):
			bit = (initial_data[r * bandwidth + b])

			match (technology):
				case memory_types.readonly_flipflop:
					cell_position = np.array([r, 0, b])

					cell = creation.add_component(CM.Component(
						CM.ComponentTypes.FLIPFLOP,
						CM.StateTypes(bit),
						cell_position + [0, 1, 0],
						augments=(bit and (2, 0) or ())
					))

					creation.add_component(CM.Component(
						CM.ComponentTypes.GATE_AND,
						CM.StateTypes.OFF,
						cell_position,
						[cell, mem_rows[r]],
						[mem_outputs[b]]
					))

				case memory_types.readonly_hardwired:
					bit and mem_rows[r].outputs.append(mem_outputs[b])

	return (mem_rows, mem_outputs)

def generate_demultiplexer(creation, index_size=4):
	input_select_list = []
	block_list = []
	original = []
	negated = []
	
	for y in range(index_size):
		original.append(input := creation.add_component(CM.Component(CM.ComponentTypes.GATE_OR, position=[0, y, -3])))
		block_list.append(input); input_select_list.append(input)

		negated.append(negated_input := creation.add_component(CM.Component(CM.ComponentTypes.GATE_NOR, position=[0, y, -2], inputs=[input])))
		block_list.append(negated_input)

	output_list = []
	input_list = []
	for state in range(2 ** index_size):
		and_gate = creation.add_component(CM.Component(CM.ComponentTypes.GATE_AND, position=np.array([0, state, -1])))
		
		for b in range(index_size):
			if (state >> b) & 1:
				negated[b].outputs.append(and_gate)
			else:
				original[b].outputs.append(and_gate)
		
		block_list.append(and_gate)
		input_list.append(and_gate)
		output_list.append(and_gate)


	return (input_select_list, input_list, output_list, block_list)

def generate_half_adder(creation, width=8):
	input_a = []
	input_b = []
	carry_output = []
	sum_output = []


def generate_display(creation, size=[5,7], inputs=None, display_lookup=None, pixel_procedure=None):
	def _default_pixel_proc(save, x, y, mx, my):
		return save.add_component(CM.Component(
			CM.ComponentTypes.GATE_XOR,
			CM.StateTypes.OFF,
			[x, y]
		))
	pixel_procedure = pixel_procedure or _default_pixel_proc

	if display_lookup:
		input_count = math.log2(len(display_lookup))
		input_count = input_count - math.floor(input_count) > 0 and math.floor(input_count + 1) or math.floor(input_count)

	if inputs:
		if display_lookup:
			assert len(inputs) != input_count, f"expected {input_count} inputs for lookup table with {len(display_lookup)} objects, got {len(inputs)}"
		else:
			assert len(inputs) != size[0] * size[1], f"expected {size[0] * size[1]} inputs, got {len(inputs)}"

	if display_lookup:
		[select, data, outputs, blocks] = generate_demultiplexer(creation, input_count)

	for x in range(size[0]):
		for y in range(size[1]):
			pixel = pixel_procedure(creation, x, y, size[0], size[1])

			if display_lookup:
				idx = size[0] * (size[1] - 1 - y) + x
				for i, table in enumerate(display_lookup):
					if table[idx]:
						pixel.inputs += [outputs[-(i + 1)]]
	
	blocks.sort(key=lambda block: block.type.value)
	pos = np.array([0, 0, -1])
	for block in blocks:
		block.position = pos.copy()
		
		pos[0] += 1

		if pos[0] >= size[0]:
			pos[0] = 0
			pos[1] += 1
		
		if pos[1] >= size[1]:
			pos[1] = 0
			pos[2] -= 1

	return (select, data)


	
def generate_image(save, image, offset=np.array([0,0,0]), pixel_procedure=None):
	def _default_pixel_proc(save, x, y, z, r, g, b, a):
		if a <= 0: return
		return save.add_component(CM.Component(
			CM.ComponentTypes.TILE,
			CM.StateTypes.OFF,
			np.array([x, y, z]),
			augments=(r, g, b)
		))
	pixel_procedure = pixel_procedure or _default_pixel_proc
	
	image_object = Image.open(image).convert("RGBA")
	[width, height] = image_object.size
	image_pixels = image_object.load()

	for y in range(height):
		for x in range(width):
			pixel_procedure(save, 0, y + offset[1], x + offset[0], *image_pixels[x, (height - 1) - y])



def generate_notes(save, start_node, end_note, type=CM.WaveTypes.SINE):
	def freq(n):
		return 440 * (2 ** ((n-49) / 12 ))
	
	for n in range(end_note - start_node):
		save.add_component(CM.Component(
			CM.ComponentTypes.SOUND,
			CM.StateTypes.OFF,
			np.array([0, (n % 12) in [2, 4, 7, 9, 11] and 1 or 0, n]),
			augments=(freq(n), type)
		))

def get_creation_io(creation):
	inputs = []
	outputs = []

	for component in creation.components:
		(len(component.inputs) == 0 and len(component.outputs) > 0) and inputs.append(component)
		(len(component.outputs) == 0 and len(component.inputs) > 0) and outputs.append(component)

	return (inputs, outputs)

def optimize_creation_size(creation):
	cube_size = len(creation.components) ** (1.0 / 3)
	cube_size - int(cube_size) > 0 and (cube_size := int(cube_size) + 1)

	assert cube_size != 0, "Cube size must be higher than 0"
	"""
	class block_sort_annealing(Annealer):
		def move(self):
			a = random.randint(0, len(self.state) - 1)
			b = random.randint(0, len(self.state) - 1)
			self.state[a], self.state[b] = self.state[b], self.state[a]
		
		def energy(self):
			e = 0
			for i in self.state:
				i
	#"""

	"""
	offsets = [
		np.array([-1, 0, 0]), np.array([1, 0, 0]), # X
		np.array([0, -1, 0]), np.array([0, 1, 0]), # Y
		np.array([0, 0, -1]), np.array([0, 0, 1]), # Z
	]

	offsets = [
		# Top Layer
		np.array([-1, 1, -1]), np.array([-1, 1, 0]), np.array([-1, 1, 1]),
		np.array([0, 1, -1]), np.array([0, 1, 0]), np.array([0, 1, 1]),
		np.array([1, 1, -1]), np.array([1, 1, 0]), np.array([1, 1, 1]),

		# Middle Layer
		np.array([-1, 0, -1]), np.array([-1, 0, 0]), np.array([-1, 0, 1]),
		np.array([0, 0, -1]), np.array([0, 0, 0]), np.array([0, 0, 1]),
		np.array([1, 0, -1]), np.array([1, 0, 0]), np.array([1, 0, 1]),

		# Bottom Layer
		np.array([-1, -1, -1]), np.array([-1, -1, 0]), np.array([-1, -1, 1]),
		np.array([0, -1, -1]), np.array([0, -1, 0]), np.array([0, -1, 1]),
		np.array([1, -1, -1]), np.array([1, -1, 0]), np.array([1, -1, 1]),
	]

	todo = creation.components.copy()
	
	available_positions = []
	used_positions = {}

	def update_available(position):
		for offset in offsets:
			center = tuple(offset + position)

			if (center in used_positions) or (center in available_positions):
				continue

			available_positions.append(center)

	def get_score_for_block(block, position):
		assert (position in available_positions) or (tuple(position) in used_positions), "Theoretically impossible state reached"
		
		score = 0

		# Theoretical offsets
		for offset in offsets:
			center = tuple(position + offset)

			if center not in used_positions: # Is it a block?
				score -= 25
				continue
			
			neighbor = used_positions[center]
			if neighbor.type == block.type:
				score += 10
			else:
				score += 5

			#straight = np.linalg.norm(neighbor.position - block.position)
			#straight = int(straight) - straight == 0
			
			#for i, o in zip(neighbor.inputs, neighbor.outputs):
			#	if straight and (o in block.outputs or i in block.inputs):
			#		score += 25

		return score

	[inputs, outputs] = get_creation_io(creation)
	for obj in inputs + outputs:
		todo.remove(obj)

	update_available(np.array([0, 0, 0]))
	while len(todo):
		block = todo.pop()
		best_score = -np.inf

		for position in available_positions:
			score = get_score_for_block(block, position)
			if score > best_score:
				best_score = score
				block.position = np.array(position)
				available_positions.remove(position)

		used_positions[tuple(block.position)] = block
		update_available(block.position)
	#"""

font = {
	"start_char": 0x20,
	"char_count": 0x7F,
	"size": [5, 7],
	"data": [
0x00, 0x00, 0x00, 0x00, 0x00,
0x00, 0x00, 0x5F, 0x00, 0x00,
0x00, 0x07, 0x00, 0x07, 0x00,
0x14, 0x7F, 0x14, 0x7F, 0x14,
0x24, 0x2A, 0x7F, 0x2A, 0x12,
0x23, 0x13, 0x08, 0x64, 0x62,
0x36, 0x49, 0x55, 0x22, 0x50,
0x00, 0x05, 0x03, 0x00, 0x00,
0x00, 0x1C, 0x22, 0x41, 0x00,
0x00, 0x41, 0x22, 0x1C, 0x00,
0x08, 0x2A, 0x1C, 0x2A, 0x08,
0x08, 0x08, 0x3E, 0x08, 0x08,
0x00, 0x50, 0x30, 0x00, 0x00,
0x08, 0x08, 0x08, 0x08, 0x08,
0x00, 0x60, 0x60, 0x00, 0x00,
0x20, 0x10, 0x08, 0x04, 0x02,
0x3E, 0x51, 0x49, 0x45, 0x3E,
0x00, 0x42, 0x7F, 0x40, 0x00,
0x42, 0x61, 0x51, 0x49, 0x46,
0x21, 0x41, 0x45, 0x4B, 0x31,
0x18, 0x14, 0x12, 0x7F, 0x10,
0x27, 0x45, 0x45, 0x45, 0x39,
0x3C, 0x4A, 0x49, 0x49, 0x30,
0x01, 0x71, 0x09, 0x05, 0x03,
0x36, 0x49, 0x49, 0x49, 0x36,
0x06, 0x49, 0x49, 0x29, 0x1E,
0x00, 0x36, 0x36, 0x00, 0x00,
0x00, 0x56, 0x36, 0x00, 0x00,
0x00, 0x08, 0x14, 0x22, 0x41,
0x14, 0x14, 0x14, 0x14, 0x14,
0x41, 0x22, 0x14, 0x08, 0x00,
0x02, 0x01, 0x51, 0x09, 0x06,
0x32, 0x49, 0x79, 0x41, 0x3E,
0x7E, 0x11, 0x11, 0x11, 0x7E,
0x7F, 0x49, 0x49, 0x49, 0x36,
0x3E, 0x41, 0x41, 0x41, 0x22,
0x7F, 0x41, 0x41, 0x22, 0x1C,
0x7F, 0x49, 0x49, 0x49, 0x41,
0x7F, 0x09, 0x09, 0x01, 0x01,
0x3E, 0x41, 0x41, 0x51, 0x32,
0x7F, 0x08, 0x08, 0x08, 0x7F,
0x00, 0x41, 0x7F, 0x41, 0x00,
0x20, 0x40, 0x41, 0x3F, 0x01,
0x7F, 0x08, 0x14, 0x22, 0x41,
0x7F, 0x40, 0x40, 0x40, 0x40,
0x7F, 0x02, 0x04, 0x02, 0x7F,
0x7F, 0x04, 0x08, 0x10, 0x7F,
0x3E, 0x41, 0x41, 0x41, 0x3E,
0x7F, 0x09, 0x09, 0x09, 0x06,
0x3E, 0x41, 0x51, 0x21, 0x5E,
0x7F, 0x09, 0x19, 0x29, 0x46,
0x46, 0x49, 0x49, 0x49, 0x31,
0x01, 0x01, 0x7F, 0x01, 0x01,
0x3F, 0x40, 0x40, 0x40, 0x3F,
0x1F, 0x20, 0x40, 0x20, 0x1F,
0x7F, 0x20, 0x18, 0x20, 0x7F,
0x63, 0x14, 0x08, 0x14, 0x63,
0x03, 0x04, 0x78, 0x04, 0x03,
0x61, 0x51, 0x49, 0x45, 0x43,
0x00, 0x00, 0x7F, 0x41, 0x41,
0x02, 0x04, 0x08, 0x10, 0x20,
0x41, 0x41, 0x7F, 0x00, 0x00,
0x04, 0x02, 0x01, 0x02, 0x04,
0x40, 0x40, 0x40, 0x40, 0x40,
0x00, 0x01, 0x02, 0x04, 0x00,
0x20, 0x54, 0x54, 0x54, 0x78,
0x7F, 0x48, 0x44, 0x44, 0x38,
0x38, 0x44, 0x44, 0x44, 0x20,
0x38, 0x44, 0x44, 0x48, 0x7F,
0x38, 0x54, 0x54, 0x54, 0x18,
0x08, 0x7E, 0x09, 0x01, 0x02,
0x08, 0x14, 0x54, 0x54, 0x3C,
0x7F, 0x08, 0x04, 0x04, 0x78,
0x00, 0x44, 0x7D, 0x40, 0x00,
0x20, 0x40, 0x44, 0x3D, 0x00,
0x00, 0x7F, 0x10, 0x28, 0x44,
0x00, 0x41, 0x7F, 0x40, 0x00,
0x7C, 0x04, 0x18, 0x04, 0x78,
0x7C, 0x08, 0x04, 0x04, 0x78,
0x38, 0x44, 0x44, 0x44, 0x38,
0x7C, 0x14, 0x14, 0x14, 0x08,
0x08, 0x14, 0x14, 0x18, 0x7C,
0x7C, 0x08, 0x04, 0x04, 0x08,
0x48, 0x54, 0x54, 0x54, 0x20,
0x04, 0x3F, 0x44, 0x40, 0x20,
0x3C, 0x40, 0x40, 0x20, 0x7C,
0x1C, 0x20, 0x40, 0x20, 0x1C,
0x3C, 0x40, 0x30, 0x40, 0x3C,
0x44, 0x28, 0x10, 0x28, 0x44,
0x0C, 0x50, 0x50, 0x50, 0x3C,
0x44, 0x64, 0x54, 0x4C, 0x44,
0x00, 0x08, 0x36, 0x41, 0x00,
0x00, 0x00, 0x7F, 0x00, 0x00,
0x00, 0x41, 0x36, 0x08, 0x00,
0x08, 0x08, 0x2A, 0x1C, 0x08,
0x08, 0x1C, 0x2A, 0x08, 0x08 
	]
}
"""
5,0,2,0,6,0+0;1,0,1,0,-7,;1,0,1,0,-3,;2,0,-1,0,-3,;2,0,1,0,4,;5,1,1,0,-5,2+0;6,0,1,0,-9,;1,0,0,0,0,;3,1,0,0,-3,;0,1,1,0,3,;5,0,0,0,6,0+0;5,0,-5,0,0,0+0?5,10;5,3;1,5;4,3;5,8;4,2;2,7;11,8;6,2;4,8;3,6;10,2;6,9;8,9;9,3;12,4??
"""



def main():
	#NLR.run("8051.edf")
	#a = LM.minterm(0b1011, 0b0100, size=4)
	#b = LM.minterm(0b0100, 0b1011, size=4)
	#print(a,'*',b,'=',a.combine(b))
	#terms = [1, 5, 6, 8, 9]; dnc = []
	#terms = [0, 1, 2, 5, 6, 7]; dnc = []
	#terms = [3, 4, 6, 7]; dnc = []
	#terms = [4, 8, 10, 12, 11, 15]; dnc = [9, 14]
	#print(*[str(term) for term in LM.reduce_terms_qmc(terms, dnc)])
	"""
	a = LM.minterm(0b1110, 0b0000)
	b = LM.minterm(0b1100, 0b0000)

	print(a,'+',b,end=' = ')
	a.combine(b)
	print(a)
	"""
	creation = CM.Creation()
	#creation.deserialize("5,0,2,0,6,0+0;1,0,1,0,-7,;1,0,1,0,-3,;2,0,-1,0,-3,;2,0,1,0,4,;5,1,1,0,-5,2+0;6,0,1,0,-9,;1,0,0,0,0,;3,1,0,0,-3,;0,1,1,0,3,;5,0,0,0,6,0+0;5,0,-5,0,0,0+0?5,10;5,3;1,5;4,3;5,8;4,2;2,7;11,8;6,2;4,8;3,6;10,2;6,9;8,9;9,3;12,4??")
	#creation.deserialize(creation)
	#generate_image(creation, "test1.png")
	#"3,0,-2,0,0,;13,0,2,1,3,67;13,0,0,1,3,66;13,0,-2,1,3,;6,0,1,0,-5,;13,0,-1,1,-5,48;6,0,-1,0,-5,;2,0,1,0,-3,;13,0,1,1,-5,79;1,0,0,0,0,;1,0,2,0,0,;5,0,-2,0,3,0+0;3,0,-1,0,-3,;5,0,0,0,3,0+0;5,0,2,0,3,0+0?11,8;15,10;15,13;10,8;1,13;12,11;14,11;13,7;1,10;12,1;14,1;8,5??"
	# creation.deserialize("6,0,0,0,2,0+160+160;6,0,0,2,-1,0+160+160;6,0,0,2,-2,0+160+160;6,0,0,3,0,0+160+160;6,0,0,2,0,0+160+160;6,0,0,1,-1,0+160+160;6,0,0,1,-2,0+160+160;6,0,0,1,0,0+160+160;6,0,0,3,-1,0+160+160;6,0,0,4,0,0+160+160;6,0,0,5,-1,0+160+160;6,0,0,5,-2,0+160+160;6,0,0,3,-2,0+160+160;6,0,0,5,0,0+160+160;6,0,0,4,-1,0+160+160;6,0,0,4,-2,0+160+160;6,0,0,6,0,0+160+160;6,0,0,0,-2,0+160+160;6,0,0,0,0,0+160+160;6,0,0,4,2,0+160+160;6,0,0,5,2,0+160+160;6,0,0,6,2,0+160+160;6,0,0,3,2,0+160+160;6,0,0,1,2,0+160+160;6,0,0,2,2,0+160+160;6,0,0,0,-1,0+160+160;6,0,0,6,1,0+160+160;6,0,0,6,-2,0+160+160;6,0,0,1,1,0+160+160;6,0,0,0,1,0+160+160;6,0,0,5,1,0+160+160;6,0,0,2,1,0+160+160;6,0,0,4,1,0+160+160;6,0,0,3,1,0+160+160;6,0,0,6,-1,???")

	"""
	creation = CMA.creation()
	memory = creation.add_child(CMA.memory())
	memory.io.select[0].output
	"""

	#"""

	#print(lookup)

	def pixel_proc(save, x, y, mx, my):
		inversed = save.add_component(CM.Component(
			CM.ComponentTypes.LED,
			CM.StateTypes.OFF,
			[x, y, 0],
			augments=[0, 140, 160, 100, 100, 0]
		))
		return inversed
	
	[select, enable] = generate_display(creation, size, display_lookup=lookup, pixel_procedure=pixel_proc)

	last = None
	for y, sel in enumerate(select):
		last = creation.add_component(CM.Component(CM.ComponentTypes.FLIPFLOP, position=[6, y, 0], inputs = last and [last] or [], outputs=[sel]))
	#"""

	"""
	[select, data, output, _block_list] = generate_demultiplexer(creation, 16)

	for y, sel in enumerate(select):
		creation.add_component(CM.component(CM.component_types.flipflop, position=[0, y, 4], outputs=[sel]))
	
	for y, dat in enumerate(data):
		creation.add_component(CM.component(CM.component_types.flipflop, position=[1, y, 4], outputs=[dat]))
	
	for y, out in enumerate(output):
		creation.add_component(CM.component(CM.component_types.led, position=[2, y, 4], inputs=[out]))
	#"""
	
	
	"""
	random.seed(5)
	bits = 16 * 16
	[rows, outputs] = generate_memory(save, 8, bits, [round(random.randint(0, 0) / 1000) for _ in range(bits)], technology=memory_types.readonly_flipflop)
	
	last = None
	for r in rows:
		r.inputs = [last] if last else []
		last = r
	#"""

	"""
	#print(save.bridge_connections())
	a = CMA.structure(creation.components, position=np.array([0,0,0]))
	print(a.get_bounding_box())
	a.rotation += [0,0,90]
	a.update()
	print(a.get_bounding_box())
	#"""
	#a = save.add_component(CM.component(CM.block_type.gate_and))
	#b = save.add_component(CM.component(CM.block_type.gate_and))
	#a.outputs = [b]
	#b.inputs = [a]
	
	#optimize_creation_size(creation)
	"""
	todo = creation.components.copy()
	
	[inputs, outputs] = get_creation_io(creation)
	for obj in inputs + outputs:
		todo.remove(obj)
	todo.sort(key=lambda block: block.type.value)
	
	for y, block in enumerate(todo):
		block.position = [0,y,0]
	
	#for comp in creation.components:
	#	comp.position = np.round(np.array(comp.position))
	#"""

	pyperclip.copy(creation.serialize(optimize_blocks=False, round_positions=True))

if __name__ == "__main__":
	main()
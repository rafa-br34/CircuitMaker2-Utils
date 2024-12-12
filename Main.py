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
		
		if a <= 0:
			return
		
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

memory = CMA.memory_properties

def main():
	"""
	creation = CM.creation()

	#| memory.output_rw_lock
	bank = CMA.memory_bank(memory.editable | memory.read_write, data=list(np.random.randint(0,2,1*32)), bandwidth=1, row_count=32)
	bank.build()

	bank.instances.rotation = [90, 0, 0]
	creation.add_components(bank.instances.get())
	"""
	creation = CM.Creation()

	for i in range(1000):
		a = CM.Component(position=[0,i,0])
		b = CM.Component(position=[1,i,0])
		b.inputs = [a]
		a.inputs = [b]
		
		creation.add_components([a, b])

	pyperclip.copy(creation.serialize(optimize_blocks=False, round_positions=False))

if __name__ == "__main__":
	main()
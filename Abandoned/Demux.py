import pyperclip
import numpy as np
import math

from CircuitMaker import Component, Creation, ComponentTypes

size_y = 8

def generate_demultiplexer(creation, index_size=4):
	input_select_list = []
	block_list = []
	original = []
	negated = []
	
	for y in range(index_size):
		input_node = creation.add_component(Component(ComponentTypes.GATE_OR, position=[0, y, -3]))
		negated_input = creation.add_component(Component(ComponentTypes.GATE_NOR, position=[0, y, -2], inputs=[input_node]))

		original.append(input_node)
		block_list.append(input_node)
		input_select_list.append(input_node)

		negated.append(negated_input)
		block_list.append(negated_input)

	state_count = 2 ** index_size

	output_list = []
	input_list = []
	for state in range(state_count):
		and_gate = creation.add_component(Component(ComponentTypes.GATE_AND, position=np.array([math.floor(state / size_y), state % size_y, -1])))
		
		for b in range(index_size):
			if (state >> b) & 1:
				negated[b].outputs.append(and_gate)
			else:
				original[b].outputs.append(and_gate)
		
		block_list.append(and_gate)
		input_list.append(and_gate)
		output_list.append(and_gate)


	return (input_select_list, input_list, output_list, block_list)


def main():
	creation = Creation()

	generate_demultiplexer(creation, index_size=4)

	pyperclip.copy(creation.serialize(optimize_blocks=False, round_positions=True))

if __name__ == "__main__":
	main()
import CircuitMaker as CM
import numpy as np
import enum
import math


def unpack_class(instance):
	return list(filter(None, [instance.__getattribute__(n) for n in dir(instance)]))

class orientation(enum.Enum):
	up = [0, 1, 0]
	down = [0, -1, 0]
	left = [1, 0, 0]
	right = [-1, 0, 0]
	front = [0, 0, 1]
	back = [0, 0, -1]

class instance:
	children = []

	def __init__(self, children=[]):
		self.children = children or []

	def remove_child(self, child):
		self.children.remove(child)
		return child

	def remove_children(self, children):
		return [self.remove_child(child) for child in children]

	def add_child(self, child):
		self.children.append(child)
		return child

	def add_children(self, children):
		return [self.add_child(child) for child in children]

	def clear(self):
		self.children.clear()

	def clone(self):
		return instance([child.clone() for child in self.children])

class structure(instance):
	position = np.array([0, 0, 0])
	rotation = np.array([0, 0, 0])

	def __init__(self, children=[], position=np.array([0, 0, 0]), rotation=np.array([0, 0, 0])):
		super().__init__(children)
		self.position = position
		self.rotation = rotation

	def clone(self):
		return structure([child.clone() for child in self.children], self.position.copy(), self.rotation.copy())

	def get_position_matrix(self):
		points = []

		for child in self.children:
			points += isinstance(child, CM.Component) and [child.position] or [*child.get_position_matrix()]
		
		return np.array(points)

	def get_bounding_box(self):
		points = self.get_position_matrix()
		return [points.min(axis=0), points.max(axis=0)]
	

	def update_position(self):
		[bounds_min, _bounds_max] = self.get_bounding_box()

		for child in self.children:
			child.position = (np.array(child.position) - bounds_min) + self.position
	
	def update_rotation(self, cube_size=1):
		correction = cube_size * np.sqrt(3) / 3
		angle_x = np.radians(self.rotation[0])
		angle_y = np.radians(self.rotation[1])
		angle_z = np.radians(self.rotation[2])

		matrix_x = np.array([
			[1, 0, 0],
			[0, np.cos(angle_x), -np.sin(angle_x)],
			[0, np.sin(angle_x), np.cos(angle_x)]
		])
		matrix_y = np.array([
			[np.cos(angle_y), 0, np.sin(angle_y)],
			[0, 1, 0],
			[-np.sin(angle_y), 0, np.cos(angle_y)]
		])
		matrix_z = np.array([
			[np.cos(angle_z), -np.sin(angle_z), 0],
			[np.sin(angle_z), np.cos(angle_z), 0],
			[0, 0, 1]
		])

		rotation_matrix = np.dot(matrix_x, np.dot(matrix_y, matrix_z))
		
		correct_x = correction * np.sin(angle_x)
		correct_y = correction * np.sin(angle_y)
		correct_z = correction * np.sin(angle_z)

		corrective_shift = np.array([
			0 + correct_y + correct_z,
			correct_x + 0 + correct_z,
			correct_x + correct_y + 0
		]) + 1

		for child in self.children:
			child.position = np.dot((child.position - self.position) * corrective_shift, rotation_matrix) + self.position
	
	def update(self):
		self.update_position()
		self.update_rotation()

	def build(self):
		self.update()

		blocks = []
		for child in self.children:
			blocks += isinstance(child, CM.Component) and [child] or child.build()

		return blocks


class io_type(enum.Enum):
	input = 0
	output = 1
	bidirectional = 2

class io_block(structure):
	mode = io_type.input

	def __init__(self, items=[], mode=io_type.input):
		super().__init__(items)
		self.mode = mode


class bus_label_mode(enum.Enum):
	none = 0
	y_plus = 1
	y_minus = 2
	x_plus = 3
	x_minus = 4
	horizontal = 2

class bus(structure):
	_last_inputs = []
	_last_outputs = []
	_last_blocks = []

	inputs = []
	outputs = []

	orientation_mode = orientation.left
	block_type = CM.ComponentTypes.GATE_OR
	labels = []
	labels_mode = bus_label_mode.none
	width = 8

	def __init__(self, inputs=[], outputs=[], width=8, orientation_mode=orientation.left, block_type=CM.ComponentTypes.NODE, labels=[], labels_mode=bus_label_mode.none):
		self.inputs = inputs or []
		self.outputs = outputs or []
		self.width = width
		self.orientation_mode = orientation_mode
		self.block_type = block_type
		self.labels = labels or []
		self.labels_mode = labels_mode


	def _connect_to(self, table, value, index):
		if index is None:
			for t in table:
				t.append(value)
		elif isinstance(index, int):
			table[index].append(value)
		elif isinstance(index, list):
			for i in index:
				table[i].append(value)

	def connect_input(self, input, index=None):
		self._connect_to(self.inputs, input, index)
		
	def connect_output(self, output, index=None):
		self._connect_to(self.outputs, output, index)

	def _clear_last(self):
		for bus_block in self._last_blocks:
			# Remove the inputs and outputs from the blocks created by this bus
			for output_block in bus_block.outputs:
				if bus_block in output_block.inputs:
					output_block.outputs.remove(bus_block)
				bus_block.outputs.clear()
				
			for input_block in bus_block.inputs:
				if bus_block in input_block.outputs:
					input_block.outputs.remove(bus_block)
				bus_block.inputs.clear()
		self._last_blocks.clear()
		self.clear()

		# If this bus made a direct connection, then remove it
		for output_block in self._last_outputs:
			for input in output_block.inputs:
				if input in self.outputs:
					output_block.inputs.remove(input)
			output_block.outputs.clear()
		self._last_outputs.clear()
		
		for input_block in self._last_inputs:
			for output in input_block.outputs:
				if output in self.inputs:
					input_block.outputs.remove(output)
			input_block.outputs.clear()
		self._last_inputs.clear()
		

	def build(self):
		self._clear_last()

		self._last_outputs = self.outputs.copy()
		self._last_inputs = self.inputs.copy()

		for idx, [output_list, input_list] in enumerate(zip(self.outputs, self.inputs, strict=True)):
			self._last_blocks.append(child := self.add_child(CM.Component(
				self.block_type,
				position=np.array([idx] * 3) * self.orientation_mode
			)))

			for output, input in zip(output_list, input_list):
				child.outputs += [output]
				child.inputs += [input]
		
		return super().build()


class memory_types(enum.Enum):
	readonly_flipflop = 0
	readonly_hardwired = 1
	readwrite_advanced = 2

class memory:
	class _memory_instances:
		cells = []
		inputs = None
		outputs = None
		row_select = None

	memory_type = memory_types.readonly_flipflop
	bit_count = 8
	bandwidth = 8
	instances = _memory_instances()
	data = None

	def __init__(self, memory_type=memory_types.readonly_hardwired, bit_count=8, bandwidth=8, data=None):
		self.memory_type = memory_type
		self.bit_count = bit_count
		self.bandwidth = bandwidth
		self.data = data

	def _verify(self):
		assert self.bit_count % self.bandwidth == 0, "bit_count must be divisible by the bandwidth"
		assert self.bandwidth <= self.bit_count, "bit_count must be higher or equal to the bandwidth"
		assert (not self.data) or (len(self.data) >= self.bit_count), "data must have at least the same length as bit_count when defined"

	def build(self):
		self._verify()

		row_count = int(self.bit_count / (bandwidth := self.bandwidth))

		instances = self.instances

		mem_outputs = instances.outputs = bus(width=bandwidth)
		mem_rows = instances.row_select = bus(width=row_count)
		mem_bank = instances.memory_bank = structure()

		# memory outputs
		for o in range(bandwidth):
			mem_outputs.add_component(CM.Component(CM.ComponentTypes.NODE, position=[-2, 0, o]))

		# memory row index
		for r in range(row_count):
			mem_rows.add_component(CM.Component(CM.ComponentTypes.NODE, position=[r, 0, -2]))

		for r in range(row_count):
			for b in range(bandwidth):
				bit = (self.data and self.data[r * bandwidth + b] or 0)

				match (self.memory_type):
					case memory_types.readonly_flipflop:
						cell_position = np.array([r, 0, b])

						cell = mem_bank.add_component(CM.Component(
							CM.ComponentTypes.FLIPFLOP,
							CM.StateTypes(bit),
							cell_position + [0, 1, 0],
							augments=(bit and (2, 0) or ())
						))

						mem_bank.add_component(CM.Component(
							CM.ComponentTypes.GATE_AND,
							CM.StateTypes.OFF,
							cell_position,
							[cell, mem_rows[r]],
							[mem_outputs[b]]
						))

					case memory_types.readonly_hardwired:
						bit and mem_rows[r].outputs.append(mem_outputs[b])
		
		return unpack_class(instances)
	

def add_structure_to_save(save, structure):
	assert "build" in dir(structure), f"{structure} composite structure has no build method"

	for component in structure.build():
		if isinstance(component, CM.Component):
			save.add_component(component)
		elif component:
			add_structure_to_save(save, component)

class creation(CM.Creation):

	def serialize(self, **kwargs):
		save = CM.Creation()

		for item in self.components:
			if isinstance(item, CM.Component):
				save.add_component(item)
			else:
				add_structure_to_save(save, item)
		
		return save.serialize(**kwargs)



import CircuitMaker as CM
import numpy as np

import enum

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

		correct_x = (np.sin(2 * angle_x) + 1) * ((np.sqrt(2) - 1) / 2) + 1
		correct_y = (np.sin(2 * angle_y) + 1) * ((np.sqrt(2) - 1) / 2) + 1
		correct_z = (np.sin(2 * angle_z) + 1) * ((np.sqrt(2) - 1) / 2) + 1

		corrective_shift = np.array([
			0 + correct_y + correct_z,
			correct_x,# + 0 + correct_z,
			correct_x,# + correct_y + 0
		])
		print(corrective_shift)

		for child in self.children:
			child.position = np.dot((child.position - self.position) * corrective_shift, rotation_matrix) + self.position
	
	def update(self):
		self.update_position()
		self.update_rotation()

	def get(self):
		self.update()
		return self.children


class memory_properties(enum.IntEnum):
	read_write = 1 << 0 # Allow for memory that can be both read and written
	editable = 1 << 1 # Allow for manual editing

	output_rw_lock = 1 << 2, # Locks output when the cell is being written

class memory_bank:
	class _io:
		inputs = []
		outputs = []
		row_select = []
		read_write = []

	instances = structure()
	cells = []
	io = _io()

	properties = memory_properties.editable
	bandwidth = 8
	row_count = 8
	data = []
	
	def __init__(self, properties=memory_properties.editable, bandwidth=8, row_count=8, data=None):
		self.properties = properties
		self.bandwidth = bandwidth
		self.row_count = row_count
		self.data = data

	def _verify(self):
		assert (not self.properties & memory_properties.output_rw_lock) or (self.properties & memory_properties.read_write), "Cannot use memory_properties.output_rw_lock without memory_properties.read_write"
		assert (not self.data) or (len(self.data) >= self.row_count * self.bandwidth), "Data must have at least the same length as row_count * bandwidth when defined"

	def _clear(self):
		self.cells.clear()
		self.instances.clear()
		self.io.inputs.clear()
		self.io.outputs.clear()
		self.io.row_select.clear()
		self.io.read_write.clear()
	
	def build(self):
		self._verify()
		self._clear()
		
		row_count = self.row_count
		bandwidth = self.bandwidth

		instances = self.instances
		cells = self.cells

		io = self.io
		inputs = io.inputs = []
		outputs = io.outputs = []
		row_select = io.row_select = []
		read_write = io.read_write = []


		# memory outputs
		for o in range(bandwidth):
			outputs.append(CM.Component(CM.ComponentTypes.NODE, position=[-1, -1, o]))
		instances.add_children(outputs)

		# memory row index
		for r in range(row_count):
			row_select.append(CM.Component(CM.ComponentTypes.NODE, position=[r, -1, -1]))
		instances.add_children(row_select)

		if self.properties & memory_properties.read_write:
			for rw in range(bandwidth):
				read_write.append(CM.Component(CM.ComponentTypes.NODE, position=[row_count + 0, -3, rw]))
			instances.add_children(read_write)

			for i in range(bandwidth):
				inputs.append(CM.Component(CM.ComponentTypes.NODE, position=[row_count + 0, -2, i]))
			instances.add_children(inputs)

		for r in range(row_count):
			for b in range(bandwidth):
				bit = (self.data and self.data[r * bandwidth + b] or 0)
				cell_position = np.array([r, 0, b])

				if self.properties == 0:
					bit and row_select[r].outputs.append(outputs[b])
				else:
					cell = []

					state_carrier = CM.Component(
						CM.ComponentTypes.FLIPFLOP,
						CM.StateTypes(bit),
						cell_position,
						augments=(bit and (2, 0) or ())
					)
					cell.append(state_carrier)

					output_gate = CM.Component(
						CM.ComponentTypes.GATE_AND,
						CM.StateTypes.OFF,
						cell_position - [0, 1, 0],
						[state_carrier, row_select[r]],
						[outputs[b]]
					)
					cell.append(output_gate)

					if self.properties & memory_properties.read_write:
						feedback_gate = CM.Component(
							CM.ComponentTypes.GATE_XOR,
							CM.StateTypes.OFF,
							cell_position - [0, 2, 0],
							[state_carrier, inputs[b]]
						)
						cell.append(feedback_gate)

						write_gate = CM.Component(
							CM.ComponentTypes.GATE_AND,
							CM.StateTypes.OFF,
							cell_position - [0, 3, 0],
							[feedback_gate, row_select[r], read_write[b]],
							[state_carrier]
						)
						cell.append(write_gate)

						if self.properties & memory_properties.output_rw_lock:
							rw_lock_gate = CM.Component(
								CM.ComponentTypes.GATE_NOR,
								CM.StateTypes.OFF,
								cell_position - [0, 4, 0],
								[read_write[b]],
								[output_gate]
							)
							cell.append(rw_lock_gate)
					
					instances.add_children(cell)
					cells.append(cell)
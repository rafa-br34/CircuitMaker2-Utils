import pathlib
import numpy as np
import enum


class ComponentTypes(enum.Enum):
	GATE_NOR           = 0
	GATE_AND           = 1
	GATE_OR            = 2
	GATE_XOR           = 3
	BUTTON             = 4
	FLIPFLOP           = 5
	LED                = 6
	SOUND              = 7
	CONDUCTOR          = 8
	CUSTOM_IO          = 9
	GATE_NAND          = 10
	GATE_XNOR          = 11
	RANDOM             = 12
	TEXT               = 13
	TILE               = 14
	NODE               = 15
	DELAY              = 16
	ANTENNA            = 17
	IMPROVED_CONDUCTOR = 18
	LED_MIXER          = 19

class WaveTypes(enum.Enum):
	SINE     = 0
	SQUARE   = 1
	TRIANGLE = 2
	SAWTOOTH = 3

class AntennaTypes(enum.Enum):
	LOCAL = 0
	GLOBAL = 1

class StateTypes(enum.Enum):
	OFF = 0
	ON  = 1

class MaterialTypes(enum.Enum):
	STUD = 1
	SMOOTH_PLASTIC = 2
	MARBLE = 3
	NEON = 4
	GLASS_TRANSPARENT = 5
	GLASS_OPAQUE = 6
	GRASS = 7
	WOOD = 8
	ROCK = 9
	SNOW = 10
	PEBBLE = 11
	PLASTIC = 12
	DIAMOND_PLATE = 13

class CollisionTypes(enum.Enum):
	SOLID = 0
	COLLIDER = 1


default_augments = {
	ComponentTypes.GATE_NOR:           [],
	ComponentTypes.GATE_AND:           [],
	ComponentTypes.GATE_OR:            [],
	ComponentTypes.GATE_XOR:           [],
	ComponentTypes.BUTTON:             [],
	ComponentTypes.FLIPFLOP:           [],
	ComponentTypes.LED:                [175, 175, 175, 100, 25, 0],
	ComponentTypes.SOUND:              [1567.98, WaveTypes.SINE],
	ComponentTypes.CONDUCTOR:          [],
	ComponentTypes.CUSTOM_IO:          [],
	ComponentTypes.GATE_NAND:          [],
	ComponentTypes.GATE_XNOR:          [],
	ComponentTypes.RANDOM:             [0.5],
	ComponentTypes.TEXT:               [65],
	ComponentTypes.TILE:               [75, 75, 75, MaterialTypes.STUD, CollisionTypes.SOLID],
	ComponentTypes.NODE:               [],
	ComponentTypes.DELAY:              [20],
	ComponentTypes.ANTENNA:            [0, AntennaTypes.LOCAL],
	ComponentTypes.IMPROVED_CONDUCTOR: [],
	ComponentTypes.LED_MIXER:          [0.0]
}

# <ID>,<STATE>,<X>,<Y>,<Z>,<BLOCK-DEPENDANT-AUGMENTS>
class Component:
	def __init__(self, type=ComponentTypes.GATE_NOR, state=StateTypes.OFF, position=(0, 0, 0), inputs=None, outputs=None, augments=None):
		self.augments = augments or default_augments[ComponentTypes(type)]
		self.position = np.array(position)
		self.outputs = outputs or []
		self.inputs = inputs or []
		self.state = state
		self.type = ComponentTypes(type)

	def connection_count(self):
		return len(self.inputs) + len(self.outputs)
	
	def clone(self):
		return Component(self.type, self.state, self.position.copy(), self.inputs.copy(), self.outputs.copy(), self.augments)
	
	def __repr__(self):
		return f"<Component type={self.type.name} state={self.state.name}>"

def _build_position(position, rounding):
	pos = []
	
	for v in position:
		if round(v) - v == 0:
			pos.append(int(v))
		elif int(rounding) == 1:
			pos.append(int(round(v)))
		elif int(rounding) > 0:
			pos.append(round(v * int(rounding)) / int(rounding))
		else:
			pos.append(v)

	return pos

def _build_augments(augments, instance_type):
	augment_list = [int(c.value) if issubclass(type(c), enum.Enum) else int(c) for c in augments]
	
	if augment_list == default_augments[instance_type]:
		return ''
	
	return "".join(f"+{int(value)}" for value in augment_list)[1:]

def _parse_augments(augment_list, block_type):
	default = default_augments[block_type]
	
	if len(default) <= 0:
		return tuple()

	for idx, val in enumerate(augment_list.split('+')):
		if val == '':
			continue

		augment_type = type(default[idx])

		if issubclass(augment_type, enum.Enum):
			yield augment_type(int(val))
		else:
			yield augment_type(val)

def serialize_block(instance, optimize=False, rounding=True):
	position = _build_position(instance.position, rounding)
	augment = _build_augments(instance.augments, instance.type)

	space = '' if optimize else '0'
	return f"{instance.type.value},{instance.state.value or space},{position[0] or space},{position[1] or space},{position[2] or space},{augment}"

def deserialize_block(data):
	[raw_type, state, x, y, z, augments] = data.split(',')
	block_type = ComponentTypes(int(raw_type))

	return Component(
		type=block_type,
		state=StateTypes(int(state or 0)),
		position=np.array(tuple(map(float, [x or 0, y or 0, z or 0]))),
		augments=tuple(_parse_augments(augments, block_type))
	)


def serialize_wire(source, target):
	return f"{source},{target}"

def deserialize_wire(wire, components):
	if len(wire) <= 0:
		return
	
	[source, target] = [components[int(id) - 1] for id in wire.split(',')]
	
	source.outputs.append(target)
	target.inputs.append(source)


class Creation:
	components = []

	def __init__(self, components=None):
		if components is None:
			components = []
		self.components = components

	def remove_component(self, component):
		self.components.remove(component)
		return component

	def remove_components(self, components):
		return [self.remove_component(component) for component in components]

	def add_component(self, component):
		self.components.append(component)
		return component

	def add_components(self, components):
		return [self.add_component(component) for component in components]

	def new_component(self, *args, **kwargs):
		return self.add_component(Component(*args, **kwargs))

	def clear(self):
		self.components.clear()

	def clone(self):
		return Creation([block.clone() for block in self.components])

	def get_inputs(self):
		for component in self.components:
			if len(component.inputs) == 0 and len(component.outputs) > 0:
				yield component
	
	def get_outputs(self):
		for component in self.components:
			if len(component.inputs) > 0 and len(component.outputs) == 0:
				yield component

	def get_unconnected(self):
		for component in self.components:
			if len(component.inputs) == 0 and len(component.outputs) == 0:
				yield component

	def components_by_type(self, component_type):
		for component in self.components:
			if component.type == component_type:
				yield component

	def topological_sort_recursive(self, node, direction="outputs", explored=None, stack=None, depth=0):
		# @todo Change to non recursive
		if explored is None:
			explored = list()

		if stack is None:
			stack = list()
		
		explored.append(node)

		for subnode in node.__getattribute__(direction):
			if subnode not in explored:
				self.topological_sort_recursive(subnode, direction, explored, stack, depth + 1)

		stack.append((node, depth))

		return stack, explored
	
	def find_requirements(self, root, direction="outputs"):
		unexplored = [(root, 0)]
		explored = []
		result = []

		while len(unexplored):
			(node, depth) = unexplored.pop()
			
			explored.append(node)
			result.append((node, depth))

			for subnode in node.__getattribute__(direction):
				if subnode in explored:
					continue
				
				unexplored.append((subnode, depth + 1))
			
			depth += 1

		return result

	def topological_sort(self, node, direction="outputs"):
		pass
	
	def longest_topological_path(self, node, direction="outputs"):
		[stack, _] = self.topological_sort(node, direction)
		
		return max([item[1] for item in stack])

	def make_connection(self, source, target):
		assert source in self.components, "Source component not in self.components"
		assert target in self.components, "Target component not in self.components"

		source.outputs.append(target)
		target.inputs.append(source)
	
	def bridge_connections(self):
		changes = 0

		for component in self.components:
			for i in component.inputs:
				if component in i.outputs:
					continue

				i.outputs.append(component)
				changes += 1

			for o in component.outputs:
				if component in o.inputs:
					continue

				o.inputs.append(component)
				changes += 1

		return changes
	
	def deduplicate_components(self):
		components = self.components
		size = len(components)
		seen = []

		for component in components:
			if component in seen:
				components.remove(component)
			else:
				seen.append(component)
		
		return size - len(seen)

	def serialize(self, optimize_wires=True, optimize_blocks=True, round_positions=True):
		serialized_wires = ""
		serialized_components = ""
		
		connection_list = set()
		components = self.components

		# Generates a connection between two points if it does not already exist in the connection list.
		def serialize_connection(a, b):
			if optimize_wires:
				connection = ((b + 1) << 32) | ((a + 1) << 0)

				if connection not in connection_list:
					connection_list.add(connection)
				else:
					return ''
			
			return serialize_wire(a + 1, b + 1) + ';'

		self.deduplicate_components()

		for src, component in enumerate(components):
			serialized_components += serialize_block(component, optimize_blocks, round_positions) + ';'
			
			for i in component.inputs:
				serialized_wires += serialize_connection(components.index(i), src) # i -> src

			for o in component.outputs:
				serialized_wires += serialize_connection(src, components.index(o)) # src -> o
		
		return f"{serialized_components[:-1]}?{serialized_wires[:-1]}??" # @todo Customs
	
	def deserialize(self, string, clear=True):
		clear and self.clear()

		[components, connections, _customs, *_] = [part.split(';') for part in string.split('?')]

		for component in components:
			self.add_component(deserialize_block(component))
		
		for connection in connections:
			deserialize_wire(connection, self.components)

	def deserialize_file(self, filepath, clear=True):
		self.deserialize(pathlib.Path(filepath).read_text(), clear)
	
	def serialize_file(self, filepath, **kwargs):
		pathlib.Path(filepath).write_text(self.serialize(**kwargs))

import blifparser.blifparser as blifparser
import pyperclip
import itertools

from CircuitMaker import Creation, Component, ComponentTypes

class Wire:
	def __init__(self, inputs = None, outputs = None):
		self.inputs = inputs or []
		self.outputs = outputs or []

class WireMapping:
	def __init__(self):
		self.translation_table = {}
		self.mapping = {}

	def get(self, name):
		if name in self.translation_table:
			name = self.translation_table[name]

		if name in self.mapping:
			return self.mapping[name]
		else:
			wire = Wire()
			self.mapping[name] = wire
			
			return wire

	def add_translation(self, origin, target):
		self.translation_table[origin] = target

def map_params(params):
	return dict(map(lambda x: x.split('='), params))

def map_component(node_name):
	c_mapping = {
		"NOR": ComponentTypes.GATE_NOR,
		"OR": ComponentTypes.NODE,
		"AND": ComponentTypes.GATE_AND,
		"XOR": ComponentTypes.GATE_XOR,
		"NAND": ComponentTypes.GATE_NAND,
		"XNOR": ComponentTypes.GATE_XNOR
	}

	match node_name:
		case "BUF":
			return ComponentTypes.NODE
		
		case "NOT":
			return ComponentTypes.GATE_NOR

		case _:
			[name, _size] = node_name.split('_')
			
			if name in c_mapping:
				return c_mapping[name]
			else:
				raise ValueError(f"Unknown component of type \"{node_name}\"")

def gen_reg(creation, feature_set=False, feature_rst=False):
	state_carrier = Component(ComponentTypes.FLIPFLOP)
	write_gate = Component(ComponentTypes.GATE_AND, outputs=[state_carrier])
	comparator = Component(ComponentTypes.GATE_XOR, inputs=[state_carrier], outputs=[write_gate])

	creation.add_components([state_carrier, write_gate, comparator])
	
	if feature_rst:
		reset_gate = Component(ComponentTypes.GATE_AND, inputs=[state_carrier], outputs=[state_carrier])
		creation.add_component(reset_gate)
	else:
		reset_gate = None
	
	if feature_set:
		set_inverter = Component(ComponentTypes.GATE_NOR, inputs=[state_carrier])
		set_gate = Component(ComponentTypes.GATE_AND, inputs=[set_inverter], outputs=[state_carrier])
		creation.add_components([set_inverter, set_gate])
	else:
		set_gate = None

	return [write_gate, comparator, state_carrier, set_gate, reset_gate]

def main():

	creation = Creation()
	blif = blifparser.BlifParser("yosys_project/build/synthesized.blif").blif

	wire_mapping = WireMapping()
	
	for item in blif.booleanfunctions:
		print(item.inputs, item.output, item.truthtable)
		if item.truthtable == [['1', '1']]:
			for input_wire in item.inputs:
				wire_mapping.add_translation(input_wire, item.output)
	
	x = 0

	for wire_name in blif.outputs.outputs:
		#component = creation.new_component(ComponentTypes.NODE, position=(10 - (x % 10), 20 - (x // 10), 0))
		component = creation.new_component(ComponentTypes.NODE, position=(x, 0, 0))
		#creation.new_component(ComponentTypes.TILE, position=(x, 1, 0), augments=(0, 255, 0))

		wire = wire_mapping.get(wire_name)
		wire.outputs.append(component)
		x += 1

	#x = 11
	for wire_name in blif.inputs.inputs:
		component = creation.new_component(ComponentTypes.NODE, position=(x, 0, 0))
		creation.new_component(ComponentTypes.TILE, position=(x, 1, 0), augments=(255, 0, 0))
		#component = creation.new_component(ComponentTypes.flipflop, position=(x := x + 1, 0, 32))

		wire = wire_mapping.get(wire_name)
		wire.inputs.append(component)
		x += 1

	#wire = wire_mapping.get("$false")
	#wire.inputs.append(creation.new_component(ComponentTypes.GATE_AND, position=(0, -1, 0)))

	wire = wire_mapping.get("$true")
	wire.inputs.append(creation.new_component(ComponentTypes.GATE_NOR, position=(0, -1, 0)))

	for node in blif.subcircuits:
		name = node.modelname

		if name in ["$print"]:
			continue

		if name == "REG":
			[clock, value, output, *_] = gen_reg(creation)

			for (key, val) in map_params(node.params).items():
				wire = wire_mapping.get(val)

				match key:
					case "CLK":
						wire.outputs.append(clock)
					
					case "IS":
						wire.outputs.append(value)
					
					case "OS":
						wire.inputs.append(output)
			
		elif name == "REG_SET":
			[clock, value, output, state_set, _] = gen_reg(creation, feature_set=True)

			for (key, val) in map_params(node.params).items():
				wire = wire_mapping.get(val)

				match key:
					case "CLK":
						wire.outputs.append(clock)
					
					case "IS":
						wire.outputs.append(value)
					
					case "OS":
						wire.inputs.append(output)

					case "SET":
						wire.outputs.append(state_set)
		
		elif name == "REG_RST":
			[clock, value, output, _, state_rst] = gen_reg(creation, feature_rst=True)

			for (key, val) in map_params(node.params).items():
				wire = wire_mapping.get(val)

				match key:
					case "CLK":
						wire.outputs.append(clock)
					
					case "IS":
						wire.outputs.append(value)
					
					case "OS":
						wire.inputs.append(output)

					case "RST":
						wire.outputs.append(state_rst)
					
		elif name == "REG_SR":
			[clock, value, output, state_set, state_rst] = gen_reg(creation, True, True)

			for (key, val) in map_params(node.params).items():
				wire = wire_mapping.get(val)

				match key:
					case "CLK":
						wire.outputs.append(clock)
					
					case "IS":
						wire.outputs.append(value)
					
					case "OS":
						wire.inputs.append(output)

					case "RST":
						wire.outputs.append(state_rst)
					
					case "SET":
						wire.outputs.append(state_set)
		else:
			component_type = map_component(node.modelname)

			node_instance = creation.new_component(component_type)

			for (key, val) in map_params(node.params).items():
				wire = wire_mapping.get(val)
				
				if key == 'Y':
					wire.inputs.append(node_instance)
				else:
					wire.outputs.append(node_instance)
	
	for wire in wire_mapping.mapping.values():
		for node_out in wire.outputs:
			for node_in in wire.inputs:
				node_in.outputs.append(node_out)


	creation.bridge_connections()
	
	io_table = list(itertools.chain(creation.get_inputs(), creation.get_outputs(), creation.get_unconnected()))

	#for obj in io_table:
		#if obj.type not in [ComponentTypes.NODE, ComponentTypes.TILE]:
		#	creation.remove_component(obj)

	for idx, node in enumerate(filter(lambda v: v not in io_table, creation.components)):
		idx += x
		node.position = (idx % x, 0, idx // x)

	time_min, time_max = [], []

	#for node_in in creation.get_inputs():
	for node_out in creation.get_outputs():
		#[stack, _] = creation.topological_sort(node_out, "inputs")
		#print(creation.longest_topological_path(node_out, "inputs"))
		#print(f"{len(stack) / len(creation.components) * 100:.2f}")
		pass
			#result = creation.propagation_time(node_in, node_out)
			
			#if not result:
			#	continue

			#time_min.append(result[0])
			#time_max.append(result[1])

	#print(min(time_min), max(time_max))

	pyperclip.copy(creation.serialize())

if __name__ == "__main__":
	main()
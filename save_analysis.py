import argparse
import networkx
import pathlib


from CircuitMaker import Component, ComponentTypes, Creation
from enum import Enum


def parse_arguments():
	parser = argparse.ArgumentParser(description="Utility that prints statistics about a save")

	parser.add_argument(
		"--input", "-i",
		help="The save file to use",
		required=True, type=str
	)

	return parser.parse_args()

def genlen(generator):
	return len(list(generator))

def main():
	arguments = parse_arguments()

	print("Deserializing...")
	creation = Creation()
	creation.deserialize_file(arguments.input)

	print("Bridging connections...")
	# The output of bridge_connections is basically useless as it depends on the behavior of the deserializer.
	creation.bridge_connections()

	components = creation.components
	component_count = len(components)

	print("Acquiring interface data...")
	unconnected_count = genlen(creation.get_unconnected())
	output_count      = genlen(creation.get_outputs())
	input_count       = genlen(creation.get_inputs())

	print("Enumerating connections...")
	output_wire_count = 0
	input_wire_count = 0

	for component in components:
		output_wire_count += len(component.outputs)
		input_wire_count += len(component.inputs)

	# @todo For unknown reasons this assert fails sometimes.
	assert input_wire_count == output_wire_count, f"Something caused bridge_connections to fail. {input_wire_count} != {output_wire_count}"

	print(f"\nComponents: {component_count}")
	for component_type in ComponentTypes:
		type_count = genlen(creation.components_by_type(component_type))

		if type_count == 0:
			continue

		print(f"   {component_type.name}: {type_count} ({(type_count / component_count) * 100.0:.2f}%)")

	print("\nInterface:")
	print(f"   Unconnected: {unconnected_count} ({(unconnected_count / component_count) * 100.0:.2f}%)")
	print(f"   Outputs: {output_count} ({(output_count / component_count) * 100.0:.2f}%)")
	print(f"   Inputs: {input_count} ({(input_count / component_count) * 100.0:.2f}%)")
	
	print("\nConnections:")
	print(f"   Wires: {(input_wire_count + output_wire_count) // 2}")


if __name__ == "__main__":
	main()
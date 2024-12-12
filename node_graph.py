import argparse
import networkx
import pathlib


from CircuitMaker import Component, ComponentTypes, Creation
from enum import Enum


class GraphType(Enum):
	GRAPHML = "graphml"
	GEXF = "gexf"

c_bridge_antennas = True
c_output = "graph.graphml"
c_format = "graphml"


def enum_to_string(enum_object):
	return f"[{', '.join([mode.value for mode in enum_object])}]"

def parse_arguments():
	parser = argparse.ArgumentParser(description="Utility to convert CM2 logic circuits into a graph")

	parser.add_argument(
		"--input", "-i",
		help="The save file to use",
		required=True, type=str
	)

	# Optional Arguments
	parser.add_argument(
		"--output", "-o",
		help="The output filename",
		type=str, default=c_output
	)

	parser.add_argument(
		"--format", "-f",
		help=f"The output graph format, possible values: [{enum_to_string(GraphType)}]",
		type=str, default=c_format
	)

	parser.add_argument(
		"--bridge-antennas", "-b",
		help=f"Should antennas be bridged? (Defaults to {c_bridge_antennas})",
		type=bool, default=c_bridge_antennas
	)

	return parser.parse_args()


def write_graph(graph, filepath, file_format):
	match (file_format):
		case GraphType.GRAPHML.value:
			return networkx.write_graphml(graph, filepath)
		case GraphType.GEXF.value:
			return networkx.write_gexf(graph, filepath)

def bridge_antennas(creation):
	channels = {}

	for node in creation.components:
		if node.type != ComponentTypes.ANTENNA:
			continue
		
		(channel, _mode) = node.augments

		node_list = channels[channel] if channel in channels else []
		node_list.append(node)

		channels[channel] = node_list

	for _channel, nodes in channels.items():
		for node in nodes:
			node.outputs.extend(filter(lambda item: item != node, nodes))

def main():
	arguments = parse_arguments()

	creation = Creation()
	graph = networkx.graph.Graph()
	
	creation.deserialize_file(arguments.input)

	if arguments.bridge_antennas:
		bridge_antennas(creation)

	creation.bridge_connections()
	
	index_map = {}

	for idx, component in enumerate(creation.components):
		index_map[component] = idx
		[pos_x, pos_y, pos_z] = component.position

		graph.add_node(idx, type=component.type.value, pos_x=pos_x, pos_y=pos_y, pos_z=pos_z)
	
	for idx, component in enumerate(creation.components):
		for node in component.outputs:
			graph.add_edge(idx, index_map[node])

	print(f"Graph built.\n\tNodes: {len(graph.nodes.values())}\n\tConnections: {len(graph.edges.values())}")

	write_graph(graph, arguments.output, arguments.format)

if __name__ == "__main__":
	main()
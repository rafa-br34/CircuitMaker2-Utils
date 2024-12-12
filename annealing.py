import matplotlib.pyplot as plt
import argparse
import random
import numpy as np

import vispy.scene as scene
import vispy

from mpl_toolkits.mplot3d import Axes3D
from CircuitMaker import Creation, ComponentTypes
from tqdm import tqdm

c_neighbors = [
	( 1,  1, -1), ( 1,  1, 0), ( 1,  1, 1),
	( 0,  1, -1), ( 0,  1, 0), ( 0,  1, 1),
	(-1,  1, -1), (-1,  1, 0), (-1,  1, 1),
	
	( 1,  0, -1), ( 1,  0, 0), ( 1,  0, 1),
	( 0,  0, -1),              ( 0,  0, 1),
	(-1,  0, -1), (-1,  0, 0), (-1,  0, 1),
	
	( 1, -1, -1), ( 1, -1, 0), ( 1, -1, 1),
	( 0, -1, -1), ( 0, -1, 0), ( 0, -1, 1),
	(-1, -1, -1), (-1, -1, 0), (-1, -1, 1),
]

"""
c_neighbors = [
	( 0, -1,  0),
	( 0,  1,  0),
	(-1,  0,  0),
	( 1,  0,  0),
	( 0,  0, -1),
	( 0,  0,  1)
]
"""

c_neighbors = [
	(-1,  0,  0),
	( 1,  0,  0),
	( 0,  0, -1),
	( 0,  0,  1),
	(-1,  0,  1),
	( 1,  0, -1)
]


c_colors = {
	ComponentTypes.GATE_NOR: [0.7, 0, 0],
	ComponentTypes.GATE_AND: [0, 0.7, 0],
	ComponentTypes.GATE_OR: [0.2, 0.2, 0.8],
	ComponentTypes.GATE_XOR: [0.6, 0, 0.4],
	ComponentTypes.BUTTON: [0.6, 0.2, 0],
	ComponentTypes.FLIPFLOP: [0.2, 0.2, 0.2],
	ComponentTypes.LED: [0.8, 0.8, 0.8],
	ComponentTypes.SOUND: [0.3, 0.3, 0],
	ComponentTypes.CONDUCTOR: [0, 0, 0.6],
	ComponentTypes.CUSTOM_IO: [1, 0, 0],
	ComponentTypes.GATE_NAND: [0, 0, 1],
	ComponentTypes.GATE_XNOR: [1, 0, 1],
	ComponentTypes.RANDOM: [0.6, 0.6, 0],
	ComponentTypes.TEXT: [0.3, 0.3, 0.6],
	ComponentTypes.TILE: [0.1, 0.1, 0.1],
	ComponentTypes.NODE: [1, 1, 0],
	ComponentTypes.DELAY: [0.3, 0, 0.3],
	ComponentTypes.ANTENNA: [0, 0.5, 0.3]
}

def cast_position(position):
	return tuple(map(int, position))

class _SpatialMap:
	def __init__(self):
		self.mapping = set()

	def clear(self):
		self.mapping.clear()

	def mark(self, position):
		self.mapping.add(cast_position(position))

	def unmark(self, position):
		self.mapping.remove(cast_position(position))
	
	def neighbors(self, position):
		position = cast_position(position)

		for offset in random.sample(c_neighbors, len(c_neighbors)):
			coord = np.array(position) + offset

			if position[2] < 0 and offset[2] < 0:
				continue

			if tuple(coord) not in self.mapping:
				yield coord

	def get_neighbor(self, position):
		for neighbor in self.neighbors(position):
			return neighbor
		
		return position

class SpatialLookup:
	def __init__(self):
		self.lookup = {}

	def index(self, position, item):
		self.lookup[cast_position(position)] = item

	def delete(self, position):
		del self.lookup[cast_position(position)]

	def value(self, position):
		return self.lookup[cast_position(position)]
	
	def swap(self, pos_a, pos_b):
		val_a = self.value(pos_a)
		val_b = self.value(pos_b)

		self.index(pos_b, val_a)
		self.index(pos_a, val_b)

	def occupied_neighbors(self, position):
		position = cast_position(position)

		for offset in random.sample(c_neighbors, len(c_neighbors)):
			coord = np.array(position) + offset

			if cast_position(coord) in self.lookup:
				yield coord
	
	def empty_neighbors(self, position):
		position = cast_position(position)

		for offset in random.sample(c_neighbors, len(c_neighbors)):
			coord = np.array(position) + offset

			if cast_position(coord) not in self.lookup:
				yield coord

class RollingAverage:
	def __init__(self, sample_count=1024):
		self.samples = [0] * sample_count
		self.current = 0
		self.size = sample_count

	def sample(self, value):
		self.samples[self.current] = value
		self.current = (self.current + 1) % self.size

	def resize(self, size):
		for _ in range(self.size - size):
			self.samples.pop()
		
		for _ in range(size - self.size):
			self.samples.append(0)

		self.size = size

	def calculate(self):
		return sum(self.samples) / max(self.samples)

class LossTable:
	def __init__(self):
		self.table = {}
		self.total = 0

	def add_items(self, items):
		for item in items:
			self.add_item(item)

	def add_item(self, item):
		self.table[item] = 0
		self.local_heuristic(item)
	
	def local_heuristic(self, item, proposed=None):
		center = proposed if proposed is not None else item.position
		total = 0
		last = self.table[item]

		for node in [*item.outputs, *item.inputs]:
			total += np.linalg.norm(center - node.position)

		self.table[item] = total

		return self.total - (last - total)

	def update_total(self):
		self.total = sum(self.table.values())


def wire_length(component, position=None):
	total = 0
	#done = []

	center = position if position is not None else component.position

	for node in [*component.outputs, *component.inputs]:
		#if node in done:
		#	continue

		total += np.linalg.norm(center - node.position)
		#done.append(node)

	return total

def graph(components):
	canvas = scene.SceneCanvas(keys="interactive", show=True)
	view = canvas.central_widget.add_view()

	positions = np.ndarray((len(components), 3))
	colors = np.ndarray((len(components), 3))

	for idx, component in enumerate(components):
		positions[idx, :] = component.position
		colors[idx, :] = c_colors[component.type]
		

	scatter = scene.visuals.Markers()
	scatter.set_data(positions, edge_width=0, face_color=colors, size=5, symbol='o')

	view.camera = "turntable"
	view.add(scatter)

	scene.visuals.XYZAxis(parent=view.scene)
	vispy.app.run()

def parse_arguments():
	parser = argparse.ArgumentParser(description="Utility to convert CM2 logic circuits into a graph")

	parser.add_argument(
		"--input", "-i",
		help="The image file to use",
		required=True, type=str
	)

	return parser.parse_args()

def _main():
	initial_temperature = 100
	iterations = 5_000_000

	spatial_map = SpatialMap()
	creation = Creation()
	creation.deserialize()
	creation.bridge_connections()

	components = creation.components
	energy = 0

	for component in components:
		component.position = np.array([random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)])
		spatial_map.mark(component.position)
		energy += wire_length(component)
	
	print(energy)

	bar = tqdm()
	bar.total = iterations

	for i in range(iterations):
		time = i / iterations

		#temperature = initial_temperature / (i + 1)
		temperature = initial_temperature * (1 - time)
		
		candidate = random.choice(components)
		
		proposed_position = spatial_map.get_neighbor(candidate.position)
		current_position = candidate.position

		proposed_loss = wire_length(candidate, proposed_position)
		current_loss = wire_length(candidate, current_position)
		

		difference = proposed_loss - current_loss
		criterion = np.pow(-difference / temperature, 2)

		if difference < 0:# or random.random() < criterion:
			candidate.position = proposed_position
			
			#spatial_map.unmark(current_position)
			#spatial_map.mark(proposed_position)

			energy += difference
		
		
		if i % 1024 == 0:
			bar.n = i
			bar.set_postfix({
				"temp": temperature,
				"loss": int(current_loss),
				"energy": energy
			})
			#print(f"[{i}] Current: {current_loss:.2f}, Temperature: {temperature:.2f}")

		if i % 8192 == 0:
			spatial_map.clear()

			for component in components:
				spatial_map.mark(component.position)
	
	bar.close()
	print(creation.serialize())

def main():
	initial_temperature = 100
	iterations = 100_000_000

	arguments = parse_arguments()

	spatial_lookup = SpatialLookup()
	loss_average = RollingAverage()
	loss_table = LossTable()
	creation = Creation()
	creation.deserialize_file(arguments.input)
	creation.bridge_connections()

	blacklist = [*creation.get_inputs(), *creation.get_outputs()]
	components = creation.components
	energy = 0

	for component in components:
		if component in blacklist:
			continue
		
		spatial_lookup.index(component.position, component)
		energy += wire_length(component)

	loss_average.resize(len(components))
	loss_table.add_items(components)
	
	print(energy)

	bar = tqdm()
	bar.total = iterations
	i = 0

	def iterate():
		nonlocal i, energy
		
		time = i / iterations

		#temperature = initial_temperature / (i + 1)
		#temperature = initial_temperature / (np.sqrt(i) * time + 1) ** 1.5
		temperature = initial_temperature * (1.0 - time)

		candidate = None
		positions = tuple()

		while not candidate or len(positions) == 0 or candidate in blacklist:
			candidate = random.choice(components)
			if candidate:
				positions = tuple(spatial_lookup.occupied_neighbors(candidate.position))
		
		proposed_position = random.choice(positions)
		current_position = candidate.position

		neighbor = spatial_lookup.value(proposed_position)

		current_loss = wire_length(candidate, current_position) + wire_length(neighbor, proposed_position)

		candidate.position = proposed_position
		neighbor.position = current_position
		proposed_loss = wire_length(candidate, proposed_position) + wire_length(neighbor, current_position)
		
		difference = proposed_loss - current_loss
		criterion = np.pow(-difference / temperature, 2)

		if difference < 0 or random.random() < criterion:
			spatial_lookup.swap(current_position, proposed_position)

			energy += difference
		else:
			candidate.position = current_position
			neighbor.position = proposed_position

		loss_average.sample(current_loss)

		if i % 1024 == 0:
			bar.n = i
			bar.set_postfix({
				"temp": temperature,
				"loss": int(current_loss),
				"average": loss_average.calculate()
			})

		i += 1

	canvas = scene.SceneCanvas(keys="interactive", show=True)
	view = canvas.central_widget.add_view()
	scatter = scene.visuals.Markers()

	d = 360
	def update(_):
		nonlocal d
		if i < iterations and d == 0:
			for _ in range(256):
				iterate()
		else:
			d -= 1
		
		positions = np.ndarray((len(components), 3))
		colors = np.ndarray((len(components), 3))

		for idx, component in enumerate(components):
			#for node in [*component.outputs, *component.inputs]:
			#	scene.visuals.Line(pos=(np.array(position), np.array(node.position)), color=(1, 0, 0), parent=canvas.scene)
			
			positions[idx, :] = component.position
			colors[idx, :] = c_colors[component.type]
		
		scatter.set_data(positions, edge_width=0, face_color=colors, size=5, symbol='o')

	view.camera = "turntable"
	view.add(scatter)

	scene.visuals.XYZAxis(parent=view.scene)

	timer = vispy.app.Timer()
	timer.connect(update)
	timer.start()

	vispy.app.run()
	
	bar.close()
	print(creation.serialize())


if __name__ == "__main__":
	main()
let CircuitMaker = {}

const Components = Object.freeze({
	NOR:       0,
	AND:       1,
	OR:        2,
	XOR:       3,
	Button:    4,
	FlipFlop:  5,
	LED:       6,
	Sound:     7,
	Conductor: 8,
	Custom:    9,
	NAND:      10,
	XNOR:      11,
	Random:    12,
	Text:      13,
	Tile:      14,
	Node:      15,
	Delay:     16,
	Antenna:   17
})
CircuitMaker.Components = Components

const States = Object.freeze({
	Off: 0,
	On:  1
})
CircuitMaker.State = States

const WaveTypes = Object.freeze({
	Sine:     0,
	Square:   1,
	Triangle: 2,
	Sawtooth: 3
})
CircuitMaker.WaveTypes = WaveTypes

const DefaultAugments = Object.freeze({
	[Components.NOR]:       [],
	[Components.AND]:       [],
	[Components.OR]:        [],
	[Components.XOR]:       [],
	[Components.Button]:    [],
	[Components.FlipFlop]:  [],
	[Components.LED]:       [175, 175, 175, 100, 25, 0],
	[Components.Sound]:     [1567.98, WaveTypes.Sine],
	[Components.Conductor]: [],
	[Components.Custom]:    [],
	[Components.NAND]:      [],
	[Components.XNOR]:      [],
	[Components.Random]:    [0.5],
	[Components.Text]:      [65],
	[Components.Tile]:      [75, 75, 75],
	[Components.Node]:      [],
	[Components.Delay]:     [20],
	[Components.Antenna]:   [0]
})
CircuitMaker.DefaultAugments = DefaultAugments

class Component {
	Type = Components.NOR
	State = States.Off
	Position = { X: 0, Y: 0, Z: 0 }

	Augments = null

	Inputs = []
	Outputs = []

	constructor(Values) {
		this.Position = Values.Position || { X: 0, Y: 0, Z: 0 }
		this.Augments = Values.Augments || DefaultAugments[this.Type]
		this.Outputs  = Values.Outputs || []
		this.Inputs   = Values.Inputs || []
		this.State    = Values.State || States.Off
		this.Type     = Values.Type || Components.NOR

		this.Position = {...this.Position}
	}

	ConnectionCount() {
		return this.Inputs.length + this.Outputs.length
	}

	Clone() {
		return new Component(this.Type, this.State, {...this.Position}, this.Inputs.slice(), this.Outputs.slice(), this.Augments.slice())
	}
}
CircuitMaker.Component = Component


function SerializeBlock(Block, Rounding = 0) {
	let PositionVector = Object.values(Block.Position)

	let Position = (Rounding > 0 ? PositionVector.map(V => Math.round(V * Rounding) / Rounding) : PositionVector).join(',')
	let Augments = Block.Augments.join() == DefaultAugments[Block.Type].join() ? "" : Block.Augments.join('+')
	
	return `${Block.Type},${Block.State || ''},${Position},${Augments}`
}

function DeserializeBlock(Data) {
	let [ Type, State, X, Y, Z, Augments ] = Data.split(",")

	return new Component({
		Type,
		State,
		Position: { X, Y, Z },
		Augments: Augments.length > 0 ? Augments.split('+') : DefaultAugments[Type]
	})
}

function SerializeWire(Source, Target) {
	return `${Source},${Target}`
}

function DeserializeWire(Data, Components) {
	let [Source, Target] = Data.split(",").map((Index) => Components[Index - 1])

	Source.Outputs.push(Target)
	Target.Inputs.push(Source)
}

class Creation {
	Components = []

	constructor(Components = null) {
		this.Components = Components || []
	}

	RemoveComponent(Component) {
		let Index = this.Components.findIndex((Value) => Value == Component)
		return Index < 0 ? null : this.Components.pop(Index)
	}

	RemoveComponents(Components) {
		return this.Components = this.Components.map((A) => Components.find((B) => A == B) > 0 ? null : A).filter(A => A)
	}

	AddComponent(Item) {
		this.Components.push(Item = Item.constructor == Component ? Item : new Component(Item))
		return Item
	}

	AddComponents(Items) {
		let List = []
		for (let Item of Items) {
			List.push(this.AddComponent(Item))
		}
		return List
	}

	Clear() {
		this.Components = []
	}

	Clone() {
		return new Creation(this.Components.map((Component) => Component.Clone()))
	}

	MakeConnection(Source, Target) {
		console.assert(this.Components.find(Source), "Source component does not exist")
		console.assert(this.Components.find(Target), "Target component does not exist")

		Source.Outputs.push(Target)
		Target.Inputs.push(Source)
	}

	BridgeConnections() {
		let Changes = 0
		for (let Component of this.Components) {
			for (let Input of Component.Inputs) {
				if (!Input.Outputs.find(Component)) {
					Input.Outputs.push(Component)
					Changes++
				}
			}
			for (let Outputs of Component.Outputs) {
				if (!Outputs.Inputs.find(Component)) {
					Outputs.Inputs.push(Component)
					Changes++
				}
			}
		}
		return Changes
	}

	Serialize(Rounding = 0, OptimizeWires = true) {
		let SerializedBlocks = ""
		let SerializedWires = ""

		let Flags = new Set()

		function SerializeConnection(A, B) {
			if (OptimizeWires) {
				let Connection = `${A}-${B}`

				if (Flags.has(Connection)) {
					return ''
				}
				else {
					Flags.add(Connection)
				}
			}
			return SerializeWire(A + 1, B + 1) + ';'
		}

		let Components = this.Components
		
		let ComponentToIndex = new Map()
		for (let Index = 0; Index < Components.length; Index++) {
			ComponentToIndex.set(Components[Index], Index)
		}

		for (let Source = 0; Source < Components.length; Source++) {
			let Component = Components[Source]

			SerializedBlocks += SerializeBlock(Component, Rounding) + ';'

			for (let I of Component.Inputs) {
				SerializedWires += SerializeConnection(ComponentToIndex.get(I), Source) // i -> src
			}
			for (let O of Component.Outputs) {
				SerializedWires += SerializeConnection(Source, ComponentToIndex.get(O)) // src -> o
			}
		}

		return `${SerializedBlocks.substring(0, SerializedBlocks.length - 1)}?${SerializedWires.substring(0, SerializedWires.length - 1)}??`
	}

	Deserialize(Data, Clear = true) {
		Clear && this.Clear()
		
		let [Components, Connections, _Buildings, _BuildingsData] = Data.split('?').map(Chunk => Chunk.split(';'))

		for (let Component of Components) {
			this.AddComponent(DeserializeBlock(Component))
		}

		for (let Connection of Connections) {
			DeserializeWire(Connection, this.Components)
		}
	}
}
CircuitMaker.Creation = Creation


return (typeof(module) == "undefined" ? {} : module).exports = CircuitMaker
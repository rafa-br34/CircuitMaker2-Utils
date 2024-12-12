let Commands = {}
let CM = this.CM

function CreateLine(Creation, Size, Configs, Lambda) {
	let List = []

	for (let i = 0; i < Size; i++) {
		let [ X, Y, Z ] = Lambda(i)
		List.push(Creation.AddComponent({ ...Configs, Position: {X, Y, Z} }))
	}

	return List
}

let c_Orientation = Object.freeze({
	Horizontal: 0,
	Vertical: 1
})
Commands.c_Orientation = c_Orientation


Commands.Register = function(Size = 8, Orientation = 1) {
	let Creation = new CM.Creation()

	let Axis0 = Orientation == c_Orientation.Vertical ? 'X' : 'Z'
	let Axis1 = Orientation == c_Orientation.Vertical ? 'Y' : 'X'
	
	let Position = { X: 0, Y: 0, Z: 0 }
	Position[Axis0] = -1
	Position[Axis1] = Size

	let RisingEdgeGate = Creation.AddComponent({
		Type: CM.Components.NOR,
		Position: Position
	})
	Position[Axis0]++

	let TriggerGate = Creation.AddComponent({
		Type: CM.Components.AND,
		Position: Position,
		Inputs: [RisingEdgeGate]
	})
	Position[Axis0]++

	// ClockInput
	Creation.AddComponent({
		Type: CM.Components.OR,
		Position: Position,
		Outputs: [TriggerGate, RisingEdgeGate]
	})

	for (let i = 0; i < Size; i++) {
		Position = { X: 0, Y: 0, Z: 0 }
		Position[Axis0] = 1
		Position[Axis1] = i

		let StateCarrier = Creation.AddComponent({
			Type: CM.Components.FlipFlop,
			Position
		})
		Position[Axis0]--

		let WriteGate = Creation.AddComponent({
			Type: CM.Components.AND,
			Position,
			Inputs: [TriggerGate],
			Outputs: [StateCarrier]
		})
		Position[Axis0]--

		// Comparator
		Creation.AddComponent({
			Type: CM.Components.XOR,
			Position,
			Inputs: [StateCarrier],
			Outputs: [WriteGate]
		})
	}

	return Creation.Serialize(0)
}

let c_MemoryFlags = Object.freeze({
	Writable: 1 << 0,
	OutputLock: 1 << 1
})
Commands.c_MemoryFlags = c_MemoryFlags

Commands.Memory = function(Bandwidth, RowCount, Flags, Data = []) {
	let Creation = new CM.Creation()

	let Height = 2 + (Flags & c_MemoryFlags.Writable ? 2 : 0) + (Flags & c_MemoryFlags.OutputLock ? 1 : 0)

	let ReadWrite
	let RowSelect
	let Outputs
	let Inputs

	let RowConfig = { Type: CM.Components.Node }

	RowSelect = CreateLine(Creation, RowCount, RowConfig, (R) => [R, Height - 2, -1])
	Outputs = CreateLine(Creation, Bandwidth, RowConfig, (O) => [-1, Height - 2, O])

	if (Flags & c_MemoryFlags.Writable) {
		Inputs = CreateLine(Creation, Bandwidth, RowConfig, (R) => [RowCount, Height - 3, R])
		ReadWrite = CreateLine(Creation, Bandwidth, RowConfig, (S) => [RowCount, Height - 4, S])
	}
	
	for (let r = 0; r < RowCount; r++) {
		for (let b = 0; b < Bandwidth; b++) {
			let Bit = (Data || [])[r * Bandwidth + b]

			let Position = {X: r, Y: Height - 1, Z: b}

			let StateCarrier = Creation.AddComponent({
				Type: CM.Components.FlipFlop,
				Position,
				Augments: Bit && [2,0],
				State: Bit,
			})
			Position.Y--

			let OutputGate = Creation.AddComponent({
				Type: CM.Components.AND,
				Position,
				Inputs: [StateCarrier, RowSelect[r]],
				Outputs: [Outputs[b]]
			})
			Position.Y--

			if (Flags & c_MemoryFlags.Writable) {
				let FeedbackGate = Creation.AddComponent({
					Type: CM.Components.XOR,
					Position,
					Inputs: [StateCarrier, Inputs[b]]
				})
				Position.Y--

				Creation.AddComponent({
					Type: CM.Components.AND,
					Position,
					Inputs: [FeedbackGate, RowSelect[r], ReadWrite[b]],
					Outputs: [StateCarrier]
				})
				Position.Y--

				if (Flags & c_MemoryFlags.OutputLock) {
					Creation.AddComponent({
						Type: CM.Components.NOR,
						Position,
						Inputs: [ReadWrite[b]],
						Outputs: [OutputGate]
					})
					Position.Y--
				}
			}
		}
	}

	return Creation.Serialize(0)
}

let c_CounterType = Object.freeze({
	Asynchronous: 0,
	Synchronous: 1
})
Commands.c_CounterType = c_CounterType

Commands.Counter = function(Size = 8, Type = c_CounterType.Asynchronous) {
	let Creation = new CM.Creation()

	if (Type == c_CounterType.Synchronous) {
		let StateChain = CreateLine(Creation, Size, { Type: CM.Components.FlipFlop }, (I) => [I, 0, 1])
		let StateGates = CreateLine(Creation, Size, { Type: CM.Components.AND },      (I) => [I, 0, 0])
		
		// Clock
		Creation.AddComponent({
			Type: CM.Components.Node,
			Position: {X: Size, Y: 0, Z: 0},
			Outputs: StateGates
		})
	
		for (let b = 0; b < Size; b++) {
			StateGates[b].Inputs = StateChain.slice(b + 1)
			StateChain[b].Inputs = [StateGates[b]]
		}
	}
	else {
		let StateChain = CreateLine(Creation, Size, { Type: CM.Components.FlipFlop }, (I) => [I, 0, 0])
		let StateGates = CreateLine(Creation, Size, { Type: CM.Components.NOR },      (I) => [I, 0, 1])

		// Clock
		let Last = Creation.AddComponent({
			Type: CM.Components.Node,
			Position: {X: Size, Y: 0, Z: 0}
		})

		for (let b = Size; b > 0; b--) {
			StateChain[b - 1].Inputs = [Last]
			Last = StateChain[b - 1]
			StateGates[b - 1].Inputs = [Last]
		}
	}

	return Creation.Serialize(0)
}

/*
CM = Function(String(fs.readFileSync("DiscordIntegration/CircuitMaker.js")))(); Commands = Function(String(fs.readFileSync("DiscordIntegration/Commands.js")))()
*/
return (typeof(module) == "undefined" ? {} : module).exports = Commands
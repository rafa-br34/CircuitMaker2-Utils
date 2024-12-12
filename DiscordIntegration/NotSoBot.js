/*
.t create/edit help ```
Available tags:
.t text <text> // Generates a save string with some text
.t memory <bandwidth=8> <row-count=8> <writable?> <output_lock?> // Generates read-only or read-write memory
.t register <size=8> <orientation=(vertical[default], horizontal)> // Generates a register
.t counter <size=8> <type=(async/asynchronous, sync/synchronous[default])> // Generates a counter

// Unimplemented tags
.t cla-adder
.t image <resize-x> <resize-y>

// Other tags
.t cmd <command> // Executes a shell on the bot's docker environment
.t eval <code> // Evaluates NodeJS code
.t userinfo // Returns your current userinfo
```
If some tag breaks please ping <@642064514476408832> 
The source code for both the commands and the serializer can be found [here](<https://gist.github.com/rafa-br34/b48c0a1b10877237e87db9b6077cf7a4>)
*/



.t create/edit text {
	js:
	let LOG = console.log

	let Command = discord.message.content
	if (!Command) { LOG("Invalid command"); return }
	if ((Command = Command.replace(/\.t\s+[A-Za-z]+(\s?)+/, "")).length <= 0) { LOG("No command specified"); return }

	let fs = require("fs")
	let Result = ""
	let X = 0, Y = 0
	for (let Character of Command) {
		if (Character == '\r') { continue }
		if (Character == '\n') { Y++; X=0; continue }
		Result += `13,0,${X},0,${Y},${Character.charCodeAt()};`
		X++
	}
	fs.writeFileSync("./output/savestring.txt", Result.substring(0, Result.length - 1) + "???")
}

.t create/edit register {
	js:
	let TNOW = Date.now; let TCALC = (A,B) => (B-A)/1000
	let LOG = console.log
	let Get = (Host, Path, Module = require("https")) => {
		return new Promise((Resolve, _Reject) => {
			Module.get({host: Host, path: Path}, (Response) => {
				let Data = ""
				Response
				.on("data", (Chunk) => Data += Chunk)
				.on("end", () => Resolve(Data))
			})
		})
	}

	let Arguments = discord.message.content
	if (!Arguments) { LOG("Invalid command"); return }
	Arguments = Arguments.replace(/\.t\s+[A-Za-z]+(\s?)+/, "").split(/\s/).filter(S => S)

	let FileLink = FileName => ["gist.githubusercontent.com", `/rafa-br34/b48c0a1b10877237e87db9b6077cf7a4/raw/${FileName}?_=${Math.random()}`]
	let GetModule = FileName => Get(...FileLink(FileName))
	
	let LoadStart = TNOW()
	Promise.all([GetModule("CircuitMaker.js"), GetModule("Commands.js")]).then(([_CM, _Commands]) => {
		let CM = Function(_CM)()
		let Commands = Function(_Commands).call({CM})

		let CompStart = TNOW()
		require("fs").writeFileSync(
			"./output/savestring.txt",
			Commands.Register(
				parseInt(Arguments[0]) || 8,
				{HORIZONTAL: 0, VERTICAL: 1}[(Arguments[1] || "HORIZONTAL").toUpperCase()] || 0
			)
		)

		let LT = TCALC(LoadStart, CompStart); let CT = TCALC(CompStart, TNOW()); LOG(`Loaded modules in ${LT.toFixed(3)} seconds\nSynthesized circuit in ${CT.toFixed(3)} seconds`);
	})
}

.t create/edit memory {
	js:
	let TNOW = Date.now; let TCALC = (A,B) => (B-A)/1000
	let LOG = console.log
	let Get = (Host, Path, Module = require("https")) => {
		return new Promise((Resolve, _Reject) => {
			Module.get({host: Host, path: Path}, (Response) => {
				let Data = ""
				Response
				.on("data", (Chunk) => Data += Chunk)
				.on("end", () => Resolve(Data))
			})
		})
	}

	let Arguments = discord.message.content
	if (!Arguments) { LOG("Invalid command"); return }
	Arguments = Arguments.replace(/\.t\s+[A-Za-z]+(\s?)+/, "").split(/\s/).filter(S => S)

	let FileLink = FileName => ["gist.githubusercontent.com", `/rafa-br34/b48c0a1b10877237e87db9b6077cf7a4/raw/${FileName}?_=${Math.random()}`]
	let GetModule = FileName => Get(...FileLink(FileName))

	let LoadStart = TNOW()
	Promise.all([GetModule("CircuitMaker.js"), GetModule("Commands.js")]).then(([_CM, _Commands]) => {
		let CM = Function(_CM)()
		let Commands = Function(_Commands).call({CM})

		let CompStart = TNOW()
		require("fs").writeFileSync(
			"./output/savestring.txt",
			Commands.Memory(
				parseInt(Arguments[0]) || 8,
				parseInt(Arguments[1]) || 8,
				(Arguments.find((V) => V.toUpperCase() == "WRITABLE") && Commands.c_MemoryFlags.Writable || 0) + (Arguments.find((V) => V.toUpperCase() == "OUTPUT_LOCK") && Commands.c_MemoryFlags.OutputLock || 0)
			)
		)

		let LT = TCALC(LoadStart, CompStart); let CT = TCALC(CompStart, TNOW()); LOG(`Loaded modules in ${LT.toFixed(3)} seconds\nSynthesized circuit in ${CT.toFixed(3)} seconds`);
	})
}

.t create/edit counter {
	js:
	let TNOW = Date.now; let TCALC = (A,B) => (B-A)/1000
	let LOG = console.log
	let Get = (Host, Path, Module = require("https")) => {
		return new Promise((Resolve, _Reject) => {
			Module.get({host: Host, path: Path}, (Response) => {
				let Data = ""
				Response
				.on("data", (Chunk) => Data += Chunk)
				.on("end", () => Resolve(Data))
			})
		})
	}

	let Arguments = discord.message.content
	if (!Arguments) { LOG("Invalid command"); return }
	Arguments = Arguments.replace(/\.t\s+[A-Za-z]+(\s?)+/, "").split(/\s/).filter(S => S)

	let FileLink = FileName => ["gist.githubusercontent.com", `/rafa-br34/b48c0a1b10877237e87db9b6077cf7a4/raw/${FileName}?_=${Math.random()}`]
	let GetModule = FileName => Get(...FileLink(FileName))

	let LoadStart = TNOW()
	Promise.all([GetModule("CircuitMaker.js"), GetModule("Commands.js")]).then(([_CM, _Commands]) => {
		let CM = Function(_CM)()
		let Commands = Function(_Commands).call({CM})

		let CompStart = TNOW()
		require("fs").writeFileSync(
			"./output/savestring.txt",
			Commands.Counter(
				parseInt(Arguments[0]) || 8,
				{ASYNCHRONOUS: 0, ASYNC: 0, SYNCHRONOUS: 1, SYNC: 1}[(Arguments[1] || "ASYNC").toUpperCase()] || 0
			)
		)

		let LT = TCALC(LoadStart, CompStart); let CT = TCALC(CompStart, TNOW()); LOG(`Loaded modules in ${LT.toFixed(3)} seconds\nSynthesized circuit in ${CT.toFixed(3)} seconds`);
	})
}

.t create/edit render {
	js:
	let TNOW = Date.now; let TCALC = (A,B) => (B-A)/1000
	let LOG = console.log
	let Get = (Host, Path, Module = require("https")) => {
		return new Promise((Resolve, _Reject) => {
			Module.get({host: Host, path: Path}, (Response) => {
				let Data = ""
				Response
				.on("data", (Chunk) => Data += Chunk)
				.on("end", () => Resolve(Data))
			})
		})
	}

	let Arguments = discord.message.content
	if (!Arguments) { LOG("Invalid command"); return }
	Arguments = Arguments.replace(/\.t\s+[A-Za-z]+(\s?)+/, "").split(/\s/).filter(S => S)

	let FileLink = FileName => ["gist.githubusercontent.com", `/rafa-br34/b48c0a1b10877237e87db9b6077cf7a4/raw/${FileName}?_=${Math.random()}`]
	let GetModule = FileName => Get(...FileLink(FileName))

	let LoadStart = TNOW()
	Promise.all([GetModule("CircuitMaker.js"), GetModule("Commands.js")]).then(([_CM, _Commands]) => {
		let CM = Function(_CM)()
		let Commands = Function(_Commands).call({CM})

		let CompStart = TNOW()
		require("fs").writeFileSync(
			"./output/savestring.txt",
			Commands.Counter(
				parseInt(Arguments[0]) || 8,
				{ASYNCHRONOUS: 0, ASYNC: 0, SYNCHRONOUS: 1, SYNC: 1}[(Arguments[1] || "ASYNC").toUpperCase()] || 0
			)
		)

		let LT = TCALC(LoadStart, CompStart); let CT = TCALC(CompStart, TNOW()); LOG(`Loaded modules in ${LT.toFixed(3)} seconds\nSynthesized circuit in ${CT.toFixed(3)} seconds`);
	})
}

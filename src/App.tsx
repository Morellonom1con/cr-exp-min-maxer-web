import { useState } from "react";
import IntegerInput from "./input";
import "./App.css";

function App() {
	const [playerTag, setPlayerTag] = useState("");
	const [values, setValues] = useState({
		Gold: 0,
		Common: 0,
		Rare: 0,
		Epic: 0,
		Legendary: 0,
		Champion: 0,
	});
	const [result, setResult] = useState("");
	const [loading, setLoading] = useState(false);

	function updateValue(label: string, newValue: number) {
		setValues((prev) => ({ ...prev, [label]: newValue }));
	}

	async function handleSubmit() {
		setLoading(true);
		try {
			const response = await fetch("http://localhost:8000/upgrade_plan", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					player_tag: playerTag,
					total_gold: values.Gold,
					common_wildcards: values.Common,
					rare_wildcards: values.Rare,
					epic_wildcards: values.Epic,
					legendary_wildcards: values.Legendary,
					champion_wildcards: values.Champion,
				}),
			});

			const data = await response.json();
			setResult(JSON.stringify(data, null, 2));
		} catch (err) {
			setResult("Error: " + err);
		}
		setLoading(false);
	}

	return (
		<div style={{ padding: 20 }}>
			<h2>Clash Royale Upgrade Planner</h2>
			<label>
				Player Tag:
				<input
					type="text"
					value={playerTag}
					onChange={(e) => setPlayerTag(e.target.value)}
					className="border rounded px-2 py-1 ml-2"
				/>
			</label>
			<br />
			<IntegerInput label="Gold" onChange={(v) => updateValue("Gold", v)} />
			<br />
			<label>Wildcards</label>
			<br />
			<IntegerInput label="Common" onChange={(v) => updateValue("Common", v)} />
			<br />
			<IntegerInput label="Rare" onChange={(v) => updateValue("Rare", v)} />
			<br />
			<IntegerInput label="Epic" onChange={(v) => updateValue("Epic", v)} />
			<br />
			<IntegerInput
				label="Legendary"
				onChange={(v) => updateValue("Legendary", v)}
			/>
			<br />
			<IntegerInput
				label="Champion"
				onChange={(v) => updateValue("Champion", v)}
			/>
			<br />
			<button
				onClick={handleSubmit}
				className="border px-4 py-2 mt-2"
				disabled={loading}
			>
				{loading ? "Calculating..." : "Calculate Upgrade Plan"}
			</button>

			{result && (
				<pre style={{ marginTop: "1rem", background: "#f5f5f5", padding: "1rem" }}>
					{result}
				</pre>
			)}
		</div>
	);
}

export default App;

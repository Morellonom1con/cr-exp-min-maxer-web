// input.tsx
import { useState } from "react";

type IntegerInputProps = {
	label: string;
	onChange: (value: number) => void;
};

export default function IntegerInput({ label, onChange }: IntegerInputProps) {
	const [value, setValue] = useState(0);

	function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
		const newVal = parseInt(e.target.value) || 0;
		setValue(newVal);
		onChange(newVal);
	}

	return (
		<>
			<label>{label}</label>
			<input
				type="number"
				value={value}
				onChange={handleChange}
				className="border rounded px-2 py-1 ml-2"
			/>
		</>
	);
}

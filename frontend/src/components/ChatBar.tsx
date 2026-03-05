import React, { useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";

type ChatBarProps = {
	input: string;
	setInput: React.Dispatch<React.SetStateAction<string>>;
	sendMessage: (input: string) => void;
	disabled?: boolean;
};

const ChatBar: React.FC<ChatBarProps> = ({ input, setInput, sendMessage, disabled = false }) => {
	const textareaRef = useRef<HTMLTextAreaElement | null>(null);
	const [isHovered, setIsHovered] = useState(false);

	const handleInput = (e: ChangeEvent<HTMLTextAreaElement>) => {
		setInput(e.target.value);
		const textarea = textareaRef.current;
		if (!textarea) return;
		textarea.style.height = "auto";
		textarea.style.height = `${textarea.scrollHeight}px`;
	};

	const submit = () => {
		if (disabled || !input.trim()) return;
		sendMessage(input);
		setInput("");
		if (textareaRef.current) {
			textareaRef.current.style.height = "auto";
		}
	};

	const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			submit();
		}
	};

	const canSubmit = !disabled && !!input.trim();

	return (
		<div
			className="flex items-end mx-1 cursor-text rounded-sm"
			onClick={(e) => {
				if (!(e.target as HTMLElement).closest("button")) {
					textareaRef.current?.focus();
				}
			}}
			style={{
				border: "1px solid rgba(180,140,60,0.28)",
				background: "rgba(8,10,18,0.9)",
				transition: "border-color 0.2s",
			}}
		>
			<textarea
				ref={textareaRef}
				value={input}
				onChange={handleInput}
				onKeyDown={handleKeyDown}
				placeholder="Seek the wisdom of the Old Mage…"
				rows={1}
				disabled={disabled}
				className="flex-1 bg-transparent border-none outline-none resize-none overflow-y-auto px-4 py-3 leading-relaxed"
				style={{
					fontFamily: "'Crimson Text', serif",
					fontSize: "1.05rem",
					color: "#d4c4a0",
					maxHeight: 120,
					scrollbarWidth: "thin",
					scrollbarColor: "rgba(180,140,60,0.2) transparent",
				}}
			/>

			<button
				onClick={submit}
				disabled={disabled || !input.trim()}
				onMouseEnter={() => setIsHovered(true)}
				onMouseLeave={() => setIsHovered(false)}
				aria-label="Send"
				className="flex items-center justify-center shrink-0 m-2 rounded-full"
				style={{
					width: 40,
					height: 40,
					border: canSubmit && isHovered ? "1px solid rgba(180,140,60,0.7)" : "1px solid rgba(180,140,60,0.35)",
					background: canSubmit && isHovered ? "rgba(180,140,60,0.15)" : "rgba(40,30,10,0.6)",
					color: canSubmit && isHovered ? "#e8d090" : "rgba(180,140,60,0.7)",
					boxShadow: canSubmit && isHovered ? "0 0 12px rgba(180,140,60,0.25), inset 0 0 8px rgba(180,140,60,0.05)" : "none",
					fontSize: "1.1rem",
					cursor: canSubmit ? "pointer" : "default",
					opacity: disabled ? 0.35 : 1,
					transition: "background 0.2s, color 0.2s, border-color 0.2s, box-shadow 0.2s",
				}}
			>
				✦
			</button>
		</div>
	);
};

export default ChatBar;

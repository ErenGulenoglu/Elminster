import React, { useEffect, useRef } from "react";
import type { Message } from "../types/chat";

type ChatLogProps = {
	messages: Message[];
	loading: boolean;
};

const ChatLog: React.FC<ChatLogProps> = ({ messages, loading }) => {
	const containerRef = useRef<HTMLDivElement | null>(null);

	useEffect(() => {
		const el = containerRef.current;
		if (!el) return;
		el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
	}, [messages, loading]);

	return (
		<div className="relative mx-1">
			{/* Ornamental border overlay */}
			<div className="absolute inset-0 pointer-events-none rounded-sm" style={{ border: "1px solid rgba(180,140,60,0.2)", zIndex: 2 }} aria-hidden="true" />

			<div
				ref={containerRef}
				className="overflow-y-auto flex flex-col gap-4 p-5 h-[60vh] rounded-sm"
				style={{
					// height: "clamp(300px, 52vh, 520px)", FIX HERE
					// FIX WITDH, FIX HEIGHT, develop on frontend
					background: "linear-gradient(rgba(8,10,20,0.88), rgba(8,10,20,0.88))",
					scrollbarWidth: "thin",
					scrollbarColor: "rgba(180,140,60,0.25) transparent",
				}}
			>
				{messages.map((m, i) => {
					const isUser = m.role === "user";
					return (
						<div key={i} className="flex flex-col gap-1" style={{ animation: "fadeSlideIn 0.35s ease both" }}>
							{/* Label */}
							<span
								className={`text-xs tracking-widest uppercase ${isUser ? "text-right" : ""}`}
								style={{
									fontFamily: "'Cinzel', serif",
									color: isUser ? "rgba(140,180,160,0.7)" : "rgba(180,140,60,0.6)",
								}}
							>
								{isUser ? "Seeker" : "Elminster"}
							</span>

							{/* Bubble */}
							<div
								className={`relative text-base leading-relaxed px-4 py-3 rounded-sm ${isUser ? "self-end" : "self-start"}`}
								style={
									isUser
										? {
												fontFamily: "'Crimson Text', serif",
												background: "rgba(50,80,65,0.25)",
												border: "1px solid rgba(100,160,120,0.2)",
												borderRight: "2px solid rgba(100,160,120,0.4)",
												color: "#b8d4c4",
												maxWidth: "82%",
												textAlign: "right",
											}
										: {
												fontFamily: "'Crimson Text', serif",
												background: "rgba(40,30,10,0.4)",
												border: "1px solid rgba(180,140,60,0.2)",
												borderLeft: "2px solid rgba(180,140,60,0.5)",
												color: "#d4c4a0",
												maxWidth: "90%",
											}
								}
							>
								{m.content}
							</div>
						</div>
					);
				})}

				{/* Thinking indicator */}
				{loading && (
					<div className="flex items-center gap-2 px-4 py-2" style={{ animation: "fadeSlideIn 0.3s ease both" }}>
						<span
							className="text-xs tracking-widest uppercase"
							style={{
								fontFamily: "'Cinzel', serif",
								color: "rgba(180,140,60,0.5)",
							}}
						>
							Elminster ponders
						</span>
						<div className="flex gap-1">
							{[0, 1, 2].map((n) => (
								<span
									key={n}
									className="block w-1.5 h-1.5 rounded-full"
									style={{
										background: "rgba(180,140,60,0.5)",
										animation: `thinkingDot 1.2s ${n * 0.2}s ease-in-out infinite`,
									}}
								/>
							))}
						</div>
					</div>
				)}
			</div>
		</div>
	);
};

export default ChatLog;

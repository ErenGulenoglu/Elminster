import { useState, useEffect } from "react";
import api from "@/api";

import { Textarea } from "../components/ui/textarea";

type Message = {
	role: "user" | "elminster";
	content: string;
};

function Home() {
	useEffect(() => {
		document.title = "Elminster";
	});

	const [messages, setMessages] = useState<Message[]>([]);
	const [input, setInput] = useState("");
	const [loading, setLoading] = useState(false);

	async function sendMessage() {
		if (!input.trim()) return;

		const userMessage: Message = {
			role: "user",
			content: input,
		};

		setMessages((prev) => [...prev, userMessage]);
		setInput("");
		setLoading(true);

		try {
			const res = await api.post("http://localhost:8000/chat", {
				message: userMessage.content,
			});

			const botMessage: Message = {
				role: "elminster",
				content: res.data.response,
			};

			setMessages((prev) => [...prev, botMessage]);
		} catch (error) {
			setMessages((prev) => [
				...prev,
				{
					role: "elminster",
					content: "⚠️ Elminster is unavailable.",
				},
			]);
		} finally {
			setLoading(false);
		}
	}
	return (
		<div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "serif" }}>
			<h2>Elminster</h2>

			<div
				style={{
					border: "1px solid #ccc",
					padding: 16,
					minHeight: 300,
					marginBottom: 16,
				}}
			>
				{messages.map((m, i) => (
					<div key={i} style={{ marginBottom: 12 }}>
						<strong>{m.role === "user" ? "You" : "Elminster"}:</strong> {m.content}
					</div>
				))}

				{loading && <em>Elminster is thinking…</em>}
			</div>

			<input
				className="resize-none focus:outline-none"
				value={input}
				onChange={(e) => setInput(e.target.value)}
				onKeyDown={(e) => e.key === "Enter" && sendMessage()}
				placeholder="Ask Elminster..."
				style={{ width: "80%", padding: 8 }}
			/>
			<textarea
				className="resize-none focus:outline-none"
				value={input}
				onChange={(e) => setInput(e.target.value)}
				onKeyDown={(e) => {
					if (e.key === "Enter" && !e.shiftKey) {
						e.preventDefault();
						sendMessage();
					}
				}}
				placeholder="Ask Elminster..."
				style={{ width: "80%", padding: 8 }}
			/>
			<Textarea value={input} onChange={(e: any) => setInput(e.target.value)} placeholder="Ask Elminster..." style={{ width: "80%", padding: 8 }} />
			<button onClick={sendMessage} style={{ padding: 8, marginLeft: 8 }}>
				Send
			</button>
		</div>
	);
}

export default Home;

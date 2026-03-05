import { useState } from "react";
import type { Message } from "../types/chat";
import { talkToElminster } from "../api/chat";

interface UseChatReturn {
	messages: Message[];
	loading: boolean;
	error: string | null;
	sendMessage: (input: string) => Promise<void>;
}

export function useChat(): UseChatReturn {
	const [messages, setMessages] = useState<Message[]>([]);
	const [loading, setLoading] = useState<boolean>(false);
	const [error, setError] = useState<string | null>(null);

	const sendMessage = async (input: string): Promise<void> => {
		if (!input.trim() || loading) return;

		const userMessage: Message = { role: "user", content: input };
		setMessages((prev) => [...prev, userMessage]);
		setLoading(true);
		setError(null);

		try {
			const response = await talkToElminster({ message: input });
			setMessages((prev) => [...prev, { role: "elminster", content: response }]);
		} catch (err) {
			setMessages((prev) => [...prev, { role: "elminster", content: "⚠️ Elminster is unavailable." }]);
			setError(err instanceof Error ? err.message : "An unknown error occurred");
		} finally {
			setLoading(false);
		}
	};

	return { messages, loading, error, sendMessage };
}

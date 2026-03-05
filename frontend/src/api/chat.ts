import api from "../api";

export interface SendMessageRequest {
	message: string;
}

export interface SendMessageResponse {
	response: string;
}

export async function talkToElminster(payload: SendMessageRequest): Promise<string> {
	const res = await api.post<SendMessageResponse>("/chat", payload);

	return res.data.response;
}

import axios from "axios";

const isDevelopment = import.meta.env.MODE === "development";

const api = isDevelopment
	? axios.create({
			baseURL: import.meta.env.VITE_API_BASE_URL_LOCAL,
			withCredentials: true, // to send cookies in CORS requests
		})
	: axios.create({
			baseURL: import.meta.env.VITE_API_BASE_URL_DEPLOY,
			withCredentials: true, // to send cookies in CORS requests
		});

export default api;

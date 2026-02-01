import { useState, useEffect } from "react";
import api from "@/api";
import type { Message } from "../types/chat";

import ChatBar from "../components/ChatBar";
import ChatLog from "../components/ChatLog";

function Home() {
  useEffect(() => {
    document.title = "Elminster";
  });

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    // Mesaj geri gelirken kullanicinin mesaj gonderememesi gerekir.
    // Bu sure zarfi icerisinde textbari ve butonu deaktive et.

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
    <div className="flex flex-col w-full h-100vh justify-center items-center">
      <main className="flex flex-col w-[90%] xl:w-[40%] h-full my-16 gap-8">
        <ChatLog messages={messages} loading={loading} />
        <ChatBar input={input} setInput={setInput} sendMessage={sendMessage} />
      </main>
    </div>
  );
}

export default Home;

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

    el.scrollTo({
      top: el.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  return (
    <div
      ref={containerRef}
      className="border border-1 border-white p-4 h-[70vh] overflow-y-auto"
    >
      {messages.map((m, i) => (
        <div key={i} style={{ marginBottom: 12 }}>
          <strong>{m.role === "user" ? "You" : "Elminster"}:</strong>{" "}
          {m.content}
        </div>
      ))}

      {loading && <em>Elminster is thinking…</em>}
    </div>
  );
};

export default ChatLog;

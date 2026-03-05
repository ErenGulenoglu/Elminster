import { useState, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import ChatBar from "../components/ChatBar";
import ChatLog from "../components/ChatLog";
import SigilHeader from "../components/SigilHeader";
import FloatingRunes from "../components/FloatingRunes";

function Home() {
	const [input, setInput] = useState<string>("");
	const { messages, loading, sendMessage } = useChat();

	useEffect(() => {
		document.title = "Elminster";
	}, []);

	return (
		<>
			{/* Keyframes injected once at page level — only what Tailwind can't express */}
			<style>{`
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

        @keyframes runeFloat {
          from { transform: translateY(0px) rotate(-3deg); opacity: 0.6; }
          to   { transform: translateY(-14px) rotate(3deg); opacity: 1; }
        }
        @keyframes shimmer {
          0%   { background-position: -400px 0; }
          100% { background-position:  400px 0; }
        }
        @keyframes pulseGlow {
          0%, 100% { opacity: 0.5; }
          50%       { opacity: 1; }
        }
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(10px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes thinkingDot {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40%            { transform: scale(1);   opacity: 1; }
        }

        /* Textarea placeholder colour — not expressible in Tailwind */
        .elminster-input::placeholder {
          color: rgba(180,140,60,0.3);
          font-style: italic;
        }
      `}</style>

			<div
				className="relative flex flex-col items-center justify-center min-h-screen overflow-hidden"
				style={{
					background: "#0a0c14",
					backgroundImage: `
            radial-gradient(ellipse 80% 60% at 50% 0%,  rgba(30,20,70,0.9)  0%, transparent 70%),
            radial-gradient(ellipse 60% 40% at 80% 100%, rgba(10,40,30,0.6) 0%, transparent 60%)
          `,
					fontFamily: "'Crimson Text', Georgia, serif",
					color: "#d4c4a0",
				}}
			>
				{/* Ambient background runes */}
				<FloatingRunes />

				{/* Main panel */}
				<main className="relative flex flex-col z-10" style={{ width: "min(680px, 94vw)", maxHeight: "96vh" }}>
					<SigilHeader />
					<ChatLog messages={messages} loading={loading} />
					<div className="mt-3 mb-4">
						<ChatBar input={input} setInput={setInput} sendMessage={sendMessage} disabled={loading} />
					</div>
					{/* Add really small stars spread in the background for extra ambience */}
					{/* Footer */}
					<p
						className="text-center text-xs tracking-widest uppercase"
						style={{
							fontFamily: "'Cinzel', serif",
							color: "rgba(180,140,60,0.22)",
						}}
					>
						The Weave connects all things
					</p>
				</main>
			</div>
		</>
	);
}

export default Home;

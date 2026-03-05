import React, { useRef } from "react";

const RUNES: string[] = ["᛭", "ᚱ", "ᚹ", "ᛗ", "ᚦ", "ᛁ", "ᚾ", "ᛖ", "ᛚ", "ᚠ", "ᚢ", "ᛒ"];

interface RuneData {
  char: string;
  size: string;
  left: string;
  top: string;
  dur: number;
  delay: number;
}

const FloatingRunes: React.FC = () => {
  const runes = useRef<RuneData[]>(
    Array.from({ length: 18 }, (_, i) => ({
      char: RUNES[i % RUNES.length],
      size: `${1.2 + Math.random() * 2.4}rem`,
      left: `${Math.random() * 96}%`,
      top: `${Math.random() * 96}%`,
      dur: 4 + Math.random() * 6,
      delay: Math.random() * 4,
    }))
  ).current;

  return (
    <>
      {runes.map((r, i) => (
        <span
          key={i}
          aria-hidden="true"
          style={{
            position: "absolute",
            fontFamily: "'Cinzel', serif",
            color: "rgba(180,140,60,0.18)",
            fontSize: r.size,
            left: r.left,
            top: r.top,
            animation: `runeFloat ${r.dur}s ease-in-out ${r.delay}s infinite alternate`,
            pointerEvents: "none",
            userSelect: "none",
            zIndex: 0,
          }}
        >
          {r.char}
        </span>
      ))}
    </>
  );
};

export default FloatingRunes;

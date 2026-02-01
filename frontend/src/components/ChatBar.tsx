import React, { useRef } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";

import { Button } from "./ui/button";
import { ArrowUp } from "lucide-react";

type ChatBarProps = {
  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  sendMessage: () => void;
};

const ChatBar: React.FC<ChatBarProps> = ({ input, setInput, sendMessage }) => {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const handleInput = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);

    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = "auto"; // reset
    textarea.style.height = `${textarea.scrollHeight}px`;
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-row w-full h-auto min-h-16 bg-secondary rounded-xl justify-center items-center">
      <div className="flex w-[85%] justify-center items-center">
        <textarea
          ref={textareaRef}
          className="
          resize-none
          focus:outline-none
          leading-6
          w-full
          overflow-y-auto
          max-h-24
          my-4
          px-2
        "
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask Elminster..."
          rows={1}
        />
      </div>
      <div className="flex w-[10%] justify-center items-center">
        <Button
          className="rounded-full cursor-pointer"
          variant="outline"
          size="icon"
          aria-label="Submit"
          onClick={sendMessage}
        >
          <ArrowUp />
        </Button>
      </div>
    </div>
  );
};

export default ChatBar;

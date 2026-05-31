import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';

// 1. Định nghĩa Interface cho Props
interface StepChatFreeProps {
  onUpdate: (data: { message: string }) => void;
  onNext: () => void;
}

function StepChatFree({ onUpdate, onNext }: StepChatFreeProps) {
  const [text, setText] = useState<string>("");

  // 2. Định nghĩa kiểu cho Ref trỏ tới thẻ Textarea
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 3. Hiệu ứng tự động tăng chiều cao (Autosize)
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    
    ta.style.height = "auto";
    // Giới hạn chiều cao tối đa là 160px để không choán hết màn hình
    ta.style.height = Math.min(ta.scrollHeight, 160) + "px";
  }, [text]);

  const handleSend = (): void => {
    if (text.trim()) {
      onUpdate({ message: text.trim() });
      onNext();
      setText("");
    }
  };

  // 4. Xử lý sự kiện bàn phím (Enter để gửi, Shift+Enter để xuống dòng)
  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // Chặn xuống dòng mặc định của phím Enter
      handleSend();
    }
  };

  return (
  <div className="flex items-end gap-3 px-4 py-3">
    {/* Textarea */}
    <textarea
      ref={textareaRef}
      value={text}
      onChange={(
        e: React.ChangeEvent<HTMLTextAreaElement>
      ) => setText(e.target.value)}
      onKeyDown={handleKey}
      rows={1}
      placeholder="Ví dụ: Ăn sáng món Việt, tối món Âu phong cách lãng mạn..."
      className="
        min-h-[52px]
        max-h-[180px]
        flex-1 resize-none
        rounded-[28px]
        border border-orange-200
        bg-orange-50/50
        px-5 py-3
        text-sm text-slate-700
        placeholder:text-slate-400
        outline-none transition-all duration-200
        focus:border-orange-400
        focus:bg-white
        focus:ring-4 focus:ring-orange-100
      "
    />

    {/* Send button */}
    <button
      onClick={handleSend}
      disabled={!text.trim()}
      aria-label="Gửi"
      className={`
        flex h-[52px] w-[52px]
        shrink-0 items-center justify-center
        rounded-full
        transition-all duration-200
        ${
          text.trim()
            ? `
              bg-gradient-to-r
              from-orange-500 to-amber-500
              text-white
              shadow-lg shadow-orange-200
              hover:scale-105
              active:scale-95
            `
            : `
              bg-slate-100
              text-slate-400
              cursor-not-allowed
            `
        }
      `}
    >
      <Send size={18} />
    </button>
  </div>
);
}

export default StepChatFree;
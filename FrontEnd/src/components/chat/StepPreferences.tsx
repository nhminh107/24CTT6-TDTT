import React, { useState } from 'react';
import { ChevronRight } from 'lucide-react';

// 1. Định nghĩa "hợp đồng" dữ liệu cho Props
interface StepPreferencesProps {
  onUpdate: (data: { preferences: string[] }) => void;
  onNext: () => void;
}

// 2. Khai báo danh sách Tag (Dùng export để tránh lỗi redeclare variable)
export const PREFERENCE_TAGS: string[] = [
  "Cay", 
  "Hải sản", 
  "Lãng mạn", 
  "Không gian mở", 
  "Gia đình", 
  "Vỉa hè", 
  "Sang trọng"
];

function StepPreferences({ onUpdate, onNext }: StepPreferencesProps) {
  // 3. Khai báo kiểu dữ liệu là một mảng các chuỗi: string[]
  const [selected, setSelected] = useState<string[]>([]);

  // 4. Định nghĩa kiểu cho tham số tag là string
  const toggle = (tag: string): void => {
    setSelected((prev) => {
      const isExist = prev.includes(tag);
      const next = isExist 
        ? prev.filter((t) => t !== tag) 
        : [...prev, tag];
      
      // Cập nhật lên JSON tổng của session
      onUpdate({ preferences: next });
      return next;
    });
  };

  return (
  <div className="mx-auto w-full max-w-xl rounded-[32px] border border-orange-100 bg-white p-5 shadow-[0_8px_30px_rgba(251,146,60,0.08)]">
    {/* Header */}
    <div className="mb-5">
      <p className="text-sm font-medium text-orange-500">
        ✨ Sở thích
      </p>

      <h2 className="mt-1 text-xl font-semibold text-slate-900">
        Bạn thích gì?
      </h2>

      <p className="mt-1 text-sm text-slate-500">
        Chọn một hoặc nhiều sở thích để gợi ý phù hợp hơn
      </p>
    </div>

    {/* Tags */}
    <div className="mb-6 flex flex-wrap gap-3">
      {PREFERENCE_TAGS.map((tag) => {
        const active =
          selected.includes(tag);

          return (
            <button
              key={tag}
              type="button"
              onClick={() => toggle(tag)}
              className={`
                rounded-full px-5 py-3
                text-sm font-medium
                transition-all duration-200
                hover:scale-[1.02]
                ${
                  active
                    ? `
                      bg-gradient-to-r
                      from-orange-500 to-amber-500
                      text-white
                      shadow-lg shadow-orange-200
                    `
                    : `
                      border border-orange-200
                      bg-orange-50
                      text-orange-700
                      hover:bg-orange-100
                    `
                }
              `}
            >
              {tag}
            </button>
          );
        })}
      </div>

      {/* Footer */}
      <div className="flex justify-end">
        <button
          onClick={onNext}
          className="
            flex items-center gap-2
            rounded-3xl
            bg-gradient-to-r
            from-orange-500 to-amber-500
            px-6 py-4
            font-semibold text-white
            shadow-lg shadow-orange-200
            transition-all duration-200
            hover:scale-[1.02]
            hover:shadow-xl
          "
        >
          Tiếp tục

          {selected.length > 0 && (
            <span
              className="
                rounded-full
                bg-white/95
                px-2.5 py-1
                text-xs font-bold
                text-orange-500
              "
            >
              {selected.length}
            </span>
          )}

          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

export default StepPreferences;
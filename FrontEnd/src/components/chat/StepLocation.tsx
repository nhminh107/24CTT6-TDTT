import React, { useState, useRef, useEffect } from 'react';
import { ChevronRight } from 'lucide-react';

// 1. Định nghĩa kiểu dữ liệu cho Props
interface StepLocationProps {
  onUpdate: (data: { location: string; placeId?: string }) => void;
  onNext: () => void;
}

interface LocationOption {
  id: string;
  name: string;
  subtitle?: string;
}

type ApiSuggestion = {
  description?: string;
  place_id?: string;
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

function StepLocation({ onUpdate, onNext }: StepLocationProps) {
  const [value, setValue] = useState<string>("");
  const [showDropdown, setShowDropdown] = useState<boolean>(false);
  const [locating, setLocating] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [options, setOptions] = useState<LocationOption[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch suggestions từ API
  useEffect(() => {
    const trimmed = value.trim();
    if (!trimmed) {
      setOptions([]);
      setShowDropdown(false);
      return;
    }

    setLoading(true);
    const controller = new AbortController();
    const handle = setTimeout(async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/maps/suggestions?q=${encodeURIComponent(trimmed)}`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          setOptions([]);
          setShowDropdown(true);
          return;
        }
        const data = (await response.json()) as ApiSuggestion[];
        const mapped = Array.isArray(data)
          ? data
              .filter((item) => item.description)
              .map((item) => ({
                id: item.place_id || item.description || "",
                name: item.description || "",
                subtitle: "Gợi ý từ bản đồ"
              }))
          : [];
        setOptions(mapped);
        setShowDropdown(true);
      } catch {
        setOptions([]);
        setShowDropdown(true);
      } finally {
        setLoading(false);
      }
    }, 350);

    return () => {
      controller.abort();
      clearTimeout(handle);
    };
  }, [value]);

  const handleLocate = (): void => {
    setLocating(true);
    // Giả lập lấy vị trí (1.4 giây cho nó có cảm giác "đang tìm kiếm" thật)
    setTimeout(() => {
      const detectedLocation = "Quận 1, TP.HCM";
      setValue(detectedLocation);
      onUpdate({ location: detectedLocation });
      setLocating(false);
    }, 1400);
  };

  const handleSelect = (option: LocationOption): void => {
    setValue(option.name);
    onUpdate({ location: option.name, placeId: option.id });
    setShowDropdown(false);
  };

  const handleConfirm = (): void => {
    if (value.trim()) {
      onUpdate({ location: value });
      onNext();
    }
  };

  return (
  <div className="mx-auto w-full max-w-xl rounded-[32px] border border-orange-100 bg-white p-5 shadow-[0_8px_30px_rgba(251,146,60,0.08)]">
    {/* Header */}
    <div className="mb-4">
      <p className="text-sm font-medium text-orange-500">
        📍 Vị trí của bạn
      </p>

      <h2 className="mt-1 text-xl font-semibold text-slate-900">
        Bạn đang ở đâu?
      </h2>

      <p className="mt-1 text-sm text-slate-500">
        Nhập quận/huyện hoặc dùng vị trí hiện tại
      </p>
    </div>

    {/* Input */}
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(
          e: React.ChangeEvent<HTMLInputElement>
        ) => setValue(e.target.value)}
        onFocus={() => setShowDropdown(true)}
        placeholder="Ví dụ: Quận 1, Bình Thạnh..."
        className="
          w-full rounded-3xl border border-orange-200
          bg-orange-50/40 px-5 py-4
          text-slate-800 placeholder:text-slate-400
          outline-none transition-all duration-200
          focus:border-orange-400
          focus:bg-white
          focus:ring-4 focus:ring-orange-100
        "
      />

      {/* Dropdown */}
      {showDropdown && (
        <div
          className="
            absolute z-20 mt-3 max-h-60 w-full overflow-y-auto
            rounded-3xl border border-orange-100
            bg-white p-2 shadow-xl
          "
        >
          {loading ? (
            <div className="px-4 py-3 text-center text-sm text-slate-500">
              🔍 Đang tìm kiếm...
            </div>
          ) : options.length > 0 ? (
            options.map((option) => (
              <button
                key={option.id}
                onClick={() =>
                  handleSelect(option)
                }
                className="
                  flex w-full items-start rounded-2xl
                  px-4 py-3 text-left text-sm
                  text-slate-700 transition
                  hover:bg-orange-50
                  hover:text-orange-600
                "
              >
                <div className="flex flex-col">
                  <span className="font-medium">📍 {option.name}</span>
                  {option.subtitle && (
                    <span className="text-xs text-slate-400">{option.subtitle}</span>
                  )}
                </div>
              </button>
            ))
          ) : value.trim() ? (
            <div className="px-4 py-3 text-center text-sm text-slate-500">
              Không tìm thấy kết quả
            </div>
          ) : null}
        </div>
      )}
    </div>

    {/* Action buttons */}
    <div className="mt-5 flex gap-3">
      {/* Locate button */}
      <button
        onClick={handleLocate}
        disabled={locating}
        className="
          flex-1 rounded-3xl border border-orange-200
          bg-white px-5 py-4
          font-medium text-orange-600
          transition-all duration-200
          hover:bg-orange-50
          disabled:cursor-not-allowed
          disabled:opacity-60
        "
      >
        {locating
          ? "📡 Đang định vị..."
          : "📍 Lấy vị trí"}
      </button>

      {/* Continue button */}
      <button
        onClick={handleConfirm}
        disabled={!value.trim()}
        className="
          flex-1 rounded-3xl
          bg-gradient-to-r
          from-orange-500 to-amber-500
          px-5 py-4
          font-semibold text-white
          shadow-lg shadow-orange-200
          transition-all duration-200
          hover:scale-[1.02]
          hover:shadow-xl
          disabled:cursor-not-allowed
          disabled:opacity-50
        "
      >
        Tiếp tục →
      </button>
    </div>
  </div>
);
}

export default StepLocation;
import React, { useState } from 'react';
import { ChevronRight } from 'lucide-react'; // Giả định bạn dùng lucide-react như prompt trước

// 1. Định nghĩa kiểu dữ liệu cho từng nút chọn nhanh (Chip)
interface BudgetChip {
  label: string;
  value: number;
}

// 2. Định nghĩa Props cho Component
interface StepBudgetProps {
  onUpdate: (data: { budget: number }) => void;
  onNext: () => void;
}

// Giả định danh sách Chip (nên để export để tránh lỗi redeclare nếu dùng ở nhiều nơi)
export const BUDGET_CHIPS: BudgetChip[] = [
  { label: "200k", value: 200000 },
  { label: "500k", value: 500000 },
  { label: "1tr", value: 1000000 },
];

function StepBudget({ onUpdate, onNext }: StepBudgetProps) {
  // 3. Khai báo kiểu dữ liệu cho State
  const [value, setValue] = useState<string>("");
  const [selected, setSelected] = useState<number | null>(null);

  // 4. Định nghĩa kiểu cho tham số chip
  const handleChip = (chip: BudgetChip): void => {
    setSelected(chip.value);
    setValue(chip.value.toString());
    onUpdate({ budget: chip.value });
  };

  const handleConfirm = (): void => {
    const num = parseInt(value);
    if (!isNaN(num) && num > 0) {
      onUpdate({ budget: num });
      onNext();
    }
  };

  return (
  <div className="mx-auto w-full max-w-xl rounded-[32px] border border-orange-100 bg-white p-5 shadow-[0_8px_30px_rgba(251,146,60,0.08)]">
    {/* Header */}
    <div className="mb-5">
      <p className="text-sm font-medium text-orange-500">
        💰 Ngân sách
      </p>

      <h2 className="mt-1 text-xl font-semibold text-slate-900">
        Bạn muốn chi khoảng bao nhiêu?
      </h2>

      <p className="mt-1 text-sm text-slate-500">
        Chọn nhanh hoặc nhập ngân sách mong muốn
      </p>
    </div>

    {/* Budget chips */}
    <div className="mb-5 flex flex-wrap gap-3">
      {BUDGET_CHIPS.map((chip) => {
        const active =
          selected === chip.value;

        return (
          <button
            key={chip.value}
            type="button"
            onClick={() =>
              handleChip(chip)
            }
            className={`
              rounded-full px-5 py-3 text-sm font-medium
              transition-all duration-200
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
            {chip.label}
          </button>
        );
      })}
    </div>

    {/* Input */}
    <div className="relative mb-6">
      <span
        className="
          absolute left-5 top-1/2
          -translate-y-1/2
          text-lg font-semibold
          text-orange-500
        "
      >
        ₫
      </span>

      <input
        type="number"
        value={value}
        placeholder="Nhập số tiền..."
        className="
          w-full rounded-3xl
          border border-orange-200
          bg-orange-50/40
          py-4 pl-12 pr-5
          text-slate-800
          placeholder:text-slate-400
          outline-none transition-all duration-200
          focus:border-orange-400
          focus:bg-white
          focus:ring-4 focus:ring-orange-100
        "
        onChange={(
          e: React.ChangeEvent<HTMLInputElement>
        ) => {
          setValue(e.target.value);
          setSelected(null);
        }}
      />
    </div>

    {/* Actions */}
    <div className="flex gap-3">
      {/* Skip */}
      <button
        onClick={onNext}
        className="
          flex-1 rounded-3xl
          border border-orange-200
          bg-white px-5 py-4
          font-medium text-orange-600
          transition-all duration-200
          hover:bg-orange-50
        "
      >
        Bỏ qua
      </button>

      {/* Continue */}
      <button
        onClick={handleConfirm}
        disabled={
          !value ||
          isNaN(parseInt(value))
        }
        className="
          flex flex-1 items-center
          justify-center gap-2
          rounded-3xl
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
        Tiếp theo
        <ChevronRight size={16} />
      </button>
    </div>
  </div>
);
}

export default StepBudget;
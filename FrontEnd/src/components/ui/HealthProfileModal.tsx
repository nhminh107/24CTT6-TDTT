"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, ShieldCheck, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { useEffect } from "react";
// ─── Types ────────────────────────────────────────────────────────────────────



export interface HealthProfile {
  selected_conditions: string[];
  selected_allergies: string[];
  diet_mode: "strict" | "casual";
  more_descriptions: string;
}

interface HealthProfileModalProps {
  open: boolean;
  onClose: () => void;
  profile: HealthProfile;
  onChange: (profile: HealthProfile) => void;
}





// ─── Data ─────────────────────────────────────────────────────────────────────

const CONDITIONS = [
  "Gout", 
  "Dạ dày", 
  "Dạ dày / Đại tràng", 
  "Tiểu đường (Diabetes)", 
  "Béo phì / Giảm cân", 
  "Low GI Diet"
];

const ALLERGIES = [
  "Đậu phộng", 
  "Bột mì", 
  "Dị ứng Hải sản", 
  "Dị ứng Hải sản vỏ cứng", 
  "Dị ứng Đậu phộng / Hạt", 
  "Bất dung nạp Lactose", 
  "Dị ứng Gluten (Celiac)"
];

// ─── Chip component ───────────────────────────────────────────────────────────

function Chip({
  label,
  selected,
  onClick,
  disabled,        // ← thêm
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
  disabled?: boolean;  // ← thêm
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}   // ← thêm
      className={cn(
        "rounded-full border px-4 py-2 text-xs font-semibold transition-all duration-200",
        disabled
          ? "cursor-not-allowed border-slate-100 bg-slate-50 text-slate-300"  // ← thêm
          : selected
            ? "border-orange-400 bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-md shadow-orange-200"
            : "border-slate-200 bg-white text-slate-600 hover:border-orange-300 hover:text-orange-600"
      )}
    >
      {label}
    </button>
  );
}

// ─── Main modal ───────────────────────────────────────────────────────────────

export default function HealthProfileModal({
  open,
  onClose,
  profile,
  onChange,
}: HealthProfileModalProps) {
  const [local, setLocal] = useState<HealthProfile>(profile);

  const hasTags =
  local.selected_conditions.length > 0 ||
  local.selected_allergies.length > 0;

const hasDescription =
  local.more_descriptions.trim().length > 0;

  // sync khi mở lại
    useEffect(() => {
    if (open) { 
      setLocal(profile);
    }
  }, [profile, open]);

  const { user } = useAuth();
  const toggle = (field: "selected_conditions" | "selected_allergies", value: string) => {
    setLocal((prev) => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter((v) => v !== value)
        : [...prev[field], value],
    }));
  };

  const handleSave = async () => {
  try {
      onChange(local);
      onClose();
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <AnimatePresence onExitComplete={() => {}}>
      {open && (
        <motion.div
          key="backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
          className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 backdrop-blur-sm sm:items-center"
          onClick={(e) => e.target === e.currentTarget && onClose()}
        >
          <motion.div
            key="sheet"
            initial={{ opacity: 0, y: 40, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 40, scale: 0.97 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="relative w-full max-w-lg overflow-hidden rounded-t-[36px] bg-white shadow-2xl sm:rounded-[36px]"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-100 px-6 py-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-orange-500 to-amber-500 shadow-md shadow-orange-200">
                  <ShieldCheck size={20} className="text-white" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">Hồ sơ sức khỏe</h2>
                  <p className="text-xs text-slate-500">Giúp AI gợi ý phù hợp hơn với bạn</p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            {/* Body — scrollable */}
            <div className="max-h-[70vh] space-y-7 overflow-y-auto px-6 py-6">

              {/* Bệnh nền */}
              <section>
                <div className="mb-3 flex items-center gap-2">
                  <AlertTriangle size={15} className="text-amber-500" />
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-700">
                    Bệnh nền
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {CONDITIONS.map((c) => (
                    <Chip
                      key={c}
                      label={c}
                      selected={local.selected_conditions.includes(c)}
                      onClick={() => toggle("selected_conditions", c)}
                      disabled={hasDescription}   
                    />
                  ))}
                </div>
              </section>

              {/* Dị ứng */}
              <section>
                <div className="mb-3 flex items-center gap-2">
                  <AlertTriangle size={15} className="text-red-400" />
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-700">
                    Dị ứng thực phẩm
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {ALLERGIES.map((a) => (
                    <Chip
                      key={a}
                      label={a}
                      selected={local.selected_allergies.includes(a)}
                      onClick={() => toggle("selected_allergies", a)}
                      disabled={hasDescription}
                    />
                  ))}
                </div>
              </section>

              {/* Chế độ */}
              <section>
                <div className="mb-3">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-700">
                    Mức độ ăn kiêng
                  </span>
                </div>
                <div className="flex overflow-hidden rounded-2xl border border-slate-200">
                  <button
                    type="button"
                    onClick={() => setLocal((p) => ({ ...p, diet_mode: "strict" }))}
                    className={cn(
                      "flex-1 py-3 text-sm font-semibold transition-all",
                      local.diet_mode === "strict"
                        ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white"
                        : "bg-white text-slate-500 hover:bg-slate-50"
                    )}
                  >
                    🔒 Ăn nghiêm ngặt
                  </button>
                  <button
                    type="button"
                    onClick={() => setLocal((p) => ({ ...p, diet_mode: "casual" }))}
                    className={cn(
                      "flex-1 py-3 text-sm font-semibold transition-all",
                      local.diet_mode === "casual"
                        ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white"
                        : "bg-white text-slate-500 hover:bg-slate-50"
                    )}
                  >
                    😌 Xả láng
                  </button>
                </div>
                <p className="mt-2 text-xs text-slate-400">
                  {local.diet_mode === "strict"
                    ? "AI sẽ lọc ketat theo bệnh nền & dị ứng của bạn."
                    : "AI vẫn gợi ý đa dạng, chỉ cảnh báo nhẹ khi cần."}
                </p>
              </section>

              {/* Mô tả thêm */}
              <section>
                <div className="mb-3">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-700">
                    Ghi chú thêm
                  </span>
                </div>
                <textarea
                  value={local.more_descriptions}
                  onChange={(e) =>
                    setLocal((p) => ({ ...p, more_descriptions: e.target.value }))
                  }
                  disabled={hasTags}
                  maxLength={200}
                  rows={3}
                  placeholder="Ví dụ: Tôi đang giảm cân, không ăn đồ chiên rán..."
                  className="w-full resize-none rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-orange-400 focus:bg-white focus:ring-4 focus:ring-orange-100"
                />
                <p className="mt-1 text-right text-xs text-slate-400">
                  {local.more_descriptions.length}/200
                </p>
              </section>
            </div>

            {/* Footer */}
            <div className="border-t border-slate-100 px-6 py-4">
              <button
                type="button"
                onClick={handleSave}
                className="w-full rounded-2xl bg-gradient-to-r from-orange-500 to-amber-500 py-3.5 text-sm font-bold text-white shadow-md shadow-orange-200 transition hover:opacity-90 active:scale-[0.98]"
              >
                Lưu hồ sơ sức khỏe
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

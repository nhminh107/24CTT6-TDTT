"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X, ShieldCheck, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
import { useEffect } from "react";
import Swal from 'sweetalert2';
import { Loader2 } from "lucide-react";
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
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSave = async () => {
    setIsSaving(true); 

    try {
      // 1. Đẩy dữ liệu ra component cha thông qua props onChange.
      await onChange(local); 
      
      // 🌟 2. HIỂN THỊ TRẠNG THÁI THÀNH CÔNG TÙY CHỈNH
      setShowSuccess(true);
      
      // Chờ 2 giây để người dùng thấy thông báo rồi mới đóng
      setTimeout(() => {
        onClose();
        // Reset lại trạng thái sau khi đóng (để lần sau mở lại không bị hiện success luôn)
        setTimeout(() => setShowSuccess(false), 500);
      }, 2000);

    } catch (error) {
      console.error("Lỗi khi cập nhật hồ sơ sức khỏe:", error);
      
      // Có thể giữ Swal cho lỗi nếu lười, nhưng tốt nhất nên đồng bộ
      Swal.fire({
        title: 'Thất bại!',
        text: 'Chưa lưu được hồ sơ, bạn kiểm tra lại kết nối mạng xem sao nhé.',
        icon: 'error',
        confirmButtonText: 'Thử lại',
        confirmButtonColor: '#f97316',
        customClass: {
          popup: 'rounded-[32px]',
          confirmButton: 'rounded-xl px-6 py-2.5'
        }
      });
    } finally {
      setIsSaving(false); 
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 backdrop-blur-sm sm:items-center p-4"
          onClick={(e) => e.target === e.currentTarget && onClose()}
        >
          <motion.div
            key="sheet"
            initial={{ opacity: 0, y: 100, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 100, scale: 0.95 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative w-full max-w-lg overflow-hidden rounded-[32px] bg-white shadow-2xl sm:rounded-[40px]"
          >
            <AnimatePresence mode="wait">
              {!showSuccess ? (
                <motion.div
                  key="form"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0, scale: 0.95, filter: "blur(10px)" }}
                  transition={{ duration: 0.2 }}
                >
                  {/* Header */}
                  <div className="flex items-center justify-between border-b border-slate-100 px-8 py-6">
                    <div className="flex items-center gap-4">
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-amber-500 shadow-lg shadow-orange-200">
                        <ShieldCheck size={24} className="text-white" />
                      </div>
                      <div>
                        <h2 className="text-lg font-bold text-slate-900">Hồ sơ sức khỏe</h2>
                        <p className="text-xs font-medium text-slate-500">Tối ưu gợi ý AI theo thể trạng của bạn</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={onClose}
                      className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-50 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
                    >
                      <X size={20} />
                    </button>
                  </div>

                  {/* Body — scrollable */}
                  <div className="max-h-[60vh] space-y-8 overflow-y-auto px-8 py-8 scrollbar-hide">

                    {/* Bệnh nền */}
                    <section>
                      <div className="mb-4 flex items-center gap-2">
                        <div className="h-1.5 w-1.5 rounded-full bg-orange-500" />
                        <span className="text-[13px] font-bold text-slate-700">
                          Bệnh nền & Thể trạng
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-2.5">
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
                      <div className="mb-4 flex items-center gap-2">
                        <div className="h-1.5 w-1.5 rounded-full bg-red-500" />
                        <span className="text-[13px] font-bold text-slate-700">
                          Dị ứng thực phẩm
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-2.5">
                        {Array.from(new Set([...ALLERGIES, ...local.selected_allergies])).map((a) => (
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
                      <div className="mb-4">
                        <span className="text-[13px] font-bold text-slate-700">
                          Mức độ ưu tiên
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 p-1.5 bg-slate-50 rounded-2xl border border-slate-100">
                        <button
                          type="button"
                          onClick={() => setLocal((p) => ({ ...p, diet_mode: "strict" }))}
                          className={cn(
                            "flex items-center justify-center gap-2 py-3 text-[14px] font-bold transition-all rounded-xl",
                            local.diet_mode === "strict"
                              ? "bg-white text-orange-600 shadow-sm border border-orange-100"
                              : "text-slate-500 hover:text-slate-700"
                          )}
                        >
                          <span className="text-base">🔒</span> Nghiêm ngặt
                        </button>
                        <button
                          type="button"
                          onClick={() => setLocal((p) => ({ ...p, diet_mode: "casual" }))}
                          className={cn(
                            "flex items-center justify-center gap-2 py-3 text-[14px] font-bold transition-all rounded-xl",
                            local.diet_mode === "casual"
                              ? "bg-white text-orange-600 shadow-sm border border-orange-100"
                              : "text-slate-500 hover:text-slate-700"
                          )}
                        >
                          <span className="text-base">😌</span> Linh hoạt
                        </button>
                      </div>
                      <p className="mt-3 text-[11px] text-slate-400 text-center font-medium leading-relaxed">
                        {local.diet_mode === "strict"
                          ? "AI sẽ loại bỏ hoàn toàn các món ăn vi phạm chỉ định của bạn."
                          : "AI ưu tiên các món phù hợp nhưng vẫn giữ lại các gợi ý đa dạng."}
                      </p>
                    </section>

                    {/* Mô tả thêm */}
                    <section>
                      <div className="mb-4">
                        <span className="text-[13px] font-bold text-slate-700">
                          Ghi chú riêng cho AI
                        </span>
                      </div>
                      <div className="relative">
                        <textarea
                          value={local.more_descriptions}
                          onChange={(e) =>
                            setLocal((p) => ({ ...p, more_descriptions: e.target.value }))
                          }
                          disabled={hasTags}
                          maxLength={200}
                          rows={3}
                          placeholder="Ví dụ: Tôi không ăn cay, đang trong chế độ Eat Clean..."
                          className="w-full resize-none rounded-2xl border border-slate-200 bg-white px-5 py-4 text-sm text-slate-700 outline-none transition focus:border-orange-400 focus:ring-4 focus:ring-orange-100 placeholder:text-slate-300"
                        />
                        <div className="absolute bottom-4 right-4 text-[10px] font-bold text-slate-300">
                          {local.more_descriptions.length}/200
                        </div>
                      </div>
                    </section>
                  </div>

                  {/* Footer */}
                  <div className="px-8 pb-8 pt-4">
                    <button
                      type="button"
                      onClick={handleSave}
                      disabled={isSaving}
                      className="group relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl bg-gradient-to-r from-orange-500 to-amber-500 py-4 text-sm font-bold text-white shadow-lg shadow-orange-200 transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-70"
                    >
                      {isSaving ? (
                        <Loader2 className="h-5 w-5 animate-spin text-white" />
                      ) : (
                        <>
                          <span>Cập nhật hồ sơ</span>
                          <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-500 group-hover:translate-x-full" />
                        </>
                      )}
                    </button>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 1.1 }}
                  className="flex flex-col items-center justify-center px-8 py-20 text-center"
                >
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", damping: 12, stiffness: 200, delay: 0.1 }}
                    className="mb-6 flex h-24 w-24 items-center justify-center rounded-full bg-green-50 text-green-500 shadow-inner"
                  >
                    <ShieldCheck size={48} strokeWidth={2.5} />
                  </motion.div>
                  <motion.h3 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="mb-2 text-2xl font-black text-slate-900"
                  >
                    Đã lưu thành công!
                  </motion.h3>
                  <motion.p 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="text-sm font-medium text-slate-500 max-w-[240px]"
                  >
                    Hồ sơ sức khỏe của bạn đã được cập nhật ổn áp.
                  </motion.p>
                  
                  {/* Progress bar effect */}
                  <div className="mt-10 h-1.5 w-32 overflow-hidden rounded-full bg-slate-100">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 2, ease: "linear" }}
                      className="h-full bg-green-500"
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { Wallet } from "lucide-react";
import { motion } from "framer-motion";
import Navbar from "@/components/layout/Navbar";
import LocationSearch from "@/components/ui/LocationSearch";
import ChatInterface from "@/components/sections/ChatInterface";
import { cn } from "@/lib/utils";

export default function AppPage() {
  const [location, setLocation] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [budget, setBudget] = useState("");
  const [promptInput, setPromptInput] = useState("");
  const [isCompact, setIsCompact] = useState(false);
  const filters = useMemo(
    () => ["Lãng mạn", "Cay", "Hải sản", "View biển", "Chay", "Gia đình"],
    []
  );

  useEffect(() => {
    const upperThreshold = 640;
    const lowerThreshold = 320;
    const handleScroll = () => {
      setIsCompact((prev) => {
        if (prev) {
          return window.scrollY < lowerThreshold ? false : prev;
        }
        return window.scrollY > upperThreshold ? true : prev;
      });
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const budgetPhrase = useMemo(() => {
    const amount = Number(budget);
    if (!amount || Number.isNaN(amount)) {
      return "";
    }
    return `Với ngân sách là ${amount.toLocaleString("vi-VN")} cho 1 người`;
  }, [budget]);

  const applyBudgetToPrompt = (value: string, current: string) => {
    const amount = Number(value);
    const phrase =
      !amount || Number.isNaN(amount)
        ? ""
        : `Với ngân sách là ${amount.toLocaleString("vi-VN")} cho 1 người`;
    const cleaned = current
      .replace(/Với ngân sách là[^.]*cho 1 người\.?/i, "")
      .replace(/\s{2,}/g, " ")
      .replace(/^[\s,.-]+|[\s,.-]+$/g, "")
      .trim();
    if (!phrase) {
      return cleaned;
    }
    if (!cleaned) {
      return phrase;
    }
    return `${phrase}. ${cleaned}`;
  };

  return (
    <div className="min-h-screen bg-white/70 pb-24">
      <Navbar />
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-10">
        <div className="flex flex-col gap-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand-coral/20 bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-flame shadow-soft">
            Ứng dụng RouteAI
          </div>
          <h1 className="font-display text-3xl font-semibold text-slate-900 md:text-4xl">
            Tối ưu lộ trình ẩm thực theo phong cách của bạn.
          </h1>
          <p className="max-w-2xl text-sm text-slate-600 md:text-base">
            Cung cấp vị trí, ngân sách và mong muốn để AI đề xuất tuyến đường ăn uống hợp lý nhất.
          </p>
        </div>

        <motion.div
          layout
          transition={{ duration: 0.85, ease: "easeOut" }}
          className={cn(
            "grid gap-6",
            isCompact
              ? "lg:grid-cols-[0fr_1fr] lg:gap-0"
              : "lg:grid-cols-[1.1fr_1.4fr]"
          )}
        >
          <motion.div
            initial={false}
            animate={
              isCompact
                ? { opacity: 0, scale: 0.96, x: -28 }
                : { opacity: 1, scale: 1, x: 0 }
            }
            transition={{ duration: 0.7, ease: "easeOut" }}
            className={cn(
              "space-y-6 overflow-hidden",
              isCompact ? "pointer-events-none" : "pointer-events-auto"
            )}
          >
            <LocationSearch
              value={location}
              onChange={setLocation}
              onSelect={(option) => {
                setLocation(option.name);
                setPlaceId(option.id);
              }}
            />

            <div>
              <label className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-lagoon">
                Ngân sách tổng
              </label>
              <div className="glass mt-3 flex items-center gap-3 rounded-2xl px-4 py-3 shadow-soft">
                <Wallet className="text-brand-teal" size={18} />
                <input
                  type="number"
                  value={budget}
                  onChange={(event) => {
                    const nextValue = event.target.value;
                    setBudget(nextValue);
                    setPromptInput((prev) =>
                      applyBudgetToPrompt(nextValue, prev)
                    );
                  }}
                  placeholder="Nhập ngân sách"
                  className="w-full min-w-0 bg-transparent text-sm text-slate-700 outline-none"
                />
                <span className="text-xs font-semibold text-slate-500">VNĐ</span>
              </div>
            </div>

            <div className="glass rounded-3xl border border-white/60 p-5 text-sm text-slate-600 shadow-soft">
              <div className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-flame">
                Bộ lọc nhanh
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                {filters.map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => {
                      setPromptInput((prev) => {
                        if (prev.toLowerCase().includes(filter.toLowerCase())) {
                          return prev;
                        }
                        const next = prev ? `${prev}, ${filter}` : filter;
                        return next;
                      });
                    }}
                    className="rounded-full border border-slate-200/60 bg-white/70 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:text-slate-900"
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>
          </motion.div>

          <ChatInterface
            placeId={placeId}
            input={promptInput}
            onInputChange={setPromptInput}
          />
        </motion.div>
      </div>

      <motion.div
        initial={false}
        animate={
          isCompact
            ? { opacity: 1, y: 0, scale: 1 }
            : { opacity: 0, y: 36, scale: 0.94 }
        }
        transition={{ duration: 0.9, ease: "easeOut" }}
        className={cn(
          "fixed right-6 bottom-24 z-40 w-[240px] rounded-2xl border border-white/60 bg-white/80 p-4 text-sm text-slate-600 shadow-soft backdrop-blur",
          isCompact ? "pointer-events-auto" : "pointer-events-none"
        )}
      >
        <div className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-flame">
          Tóm tắt phiên
        </div>
        <div className="mt-3 space-y-2">
          <div>
            Vị trí: <span className="font-semibold text-slate-900">{location || "Chưa chọn"}</span>
          </div>
          <div>
            Ngân sách: <span className="font-semibold text-slate-900">{budgetPhrase || "Chưa nhập"}</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

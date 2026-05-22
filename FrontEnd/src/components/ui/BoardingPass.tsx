"use client";

import { useMemo, useRef, useState } from "react";
import html2canvas from "html2canvas";
import { Compass, Clock, PlaneTakeoff, QrCode, Sparkles, Download } from "lucide-react";
import { cn } from "@/lib/utils";

type MealStop = {
  label: string;
  name: string;
  time: string;
  price: string;
  type: string;
  rating: number;
};

type BoardingPassProps = {
  departure: string;
  meals: MealStop[];
  totalAllowance: string;
  className?: string;
};

export default function BoardingPass({
  departure,
  meals,
  totalAllowance,
  className
}: BoardingPassProps) {
  const passRef = useRef<HTMLDivElement | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const sanitizedMeals = useMemo(() => meals.slice(0, 3), [meals]);

  const waitForStableLayout = async () => {
    if (document.fonts?.ready) {
      await document.fonts.ready;
    }
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  };

  const handleExport = async () => {
    if (!passRef.current || isExporting) {
      return;
    }
    setIsExporting(true);
    try {
      await waitForStableLayout();
      const canvas = await html2canvas(passRef.current, {
        useCORS: true,
        scale: 2,
        backgroundColor: "#ffffff"
      });
      const dataUrl = canvas.toDataURL("image/png");
      const link = document.createElement("a");
      link.href = dataUrl;
      link.download = "routeai-boarding-pass.png";
      link.click();
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = async () => {
    if (!passRef.current || isExporting) {
      return;
    }
    setIsExporting(true);
    try {
      await waitForStableLayout();
      const canvas = await html2canvas(passRef.current, {
        useCORS: true,
        scale: 2,
        backgroundColor: "#ffffff"
      });
      const blob = await new Promise<Blob | null>((resolve) =>
        canvas.toBlob(resolve, "image/png")
      );
      if (!blob) {
        return;
      }
      const file = new File([blob], "routeai-boarding-pass.png", {
        type: "image/png"
      });
      if (navigator.share && navigator.canShare?.({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: "BMI - Lộ trình ẩm thực",
          text: "Khoe vé lịch trình ẩm thực của mình!"
        });
      } else {
        const dataUrl = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        link.href = dataUrl;
        link.download = "routeai-boarding-pass.png";
        link.click();
      }
    } finally {
      setIsExporting(false);
    }
  };

  const nowLabel = new Date().toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs font-semibold uppercase tracking-[0.3em] text-[#C5A059]">
          Xuất vé ẩm thực
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleShare}
            className="inline-flex items-center gap-2 rounded-full border border-[#C5A059]/40 bg-[#FAFAFA] px-4 py-2 text-xs font-semibold text-[#0B3C5D] shadow-soft"
          >
            <Sparkles size={14} />
            Chia sẻ
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-2 rounded-full bg-[#0B3C5D] px-4 py-2 text-xs font-semibold text-[#C5A059] shadow-glow"
          >
            <Download size={14} />
            {isExporting ? "Đang xuất..." : "Tải ảnh"}
          </button>
        </div>
      </div>

      <div className="flex justify-center">
        <div
          ref={passRef}
          className="relative h-[800px] w-[450px] overflow-hidden rounded-[24px] border border-[#0B3C5D]/15 bg-[#FAFAFA] p-6 shadow-[0_32px_80px_rgba(11,60,93,0.25)] before:absolute before:left-[-18px] before:top-[210px] before:h-9 before:w-9 before:rounded-full before:bg-[#FAFAFA] before:shadow-[0_0_0_8px_rgba(250,250,250,1)] after:absolute after:right-[-18px] after:top-[210px] after:h-9 after:w-9 after:rounded-full after:bg-[#FAFAFA] after:shadow-[0_0_0_8px_rgba(250,250,250,1)]"
        >
          <div className="absolute inset-x-0 top-0 h-[120px] bg-[#0B3C5D]" />
          <div className="relative">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#0B3C5D] text-[#C5A059] shadow-soft">
                  <Compass size={22} />
                </span>
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.35em] text-[#C5A059]">
                    BMI
                  </div>
                  <div className="font-display text-xl font-semibold text-white">
                    Food Itinerary Pass
                  </div>
                </div>
              </div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-[#C5A059]">
                BUSINESS CLASS
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-[#C5A059]/40 bg-[#FAFAFA] px-3 py-1 text-[11px] font-semibold text-[#0B3C5D] shadow-soft">
                AI-OPTIMIZED
              </div>
              <div className="text-xs font-semibold uppercase tracking-[0.3em] text-[#C5A059]">
                {nowLabel}
              </div>
            </div>

            <div className="mt-5 h-px w-full border-t border-dashed border-[#C5A059]/30" />

            <div className="mt-5 grid gap-4 rounded-2xl border border-[#0B3C5D]/10 bg-[#FDFBF7] p-4 sm:grid-cols-[1fr_auto_1fr]">
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-[#0B3C5D]/60">
                  Departure
                </div>
                <div className="mt-2 text-base font-semibold text-[#0B3C5D]">
                  {departure || "Chưa chọn vị trí"}
                </div>
                <div className="mt-1 text-xs text-[#0B3C5D]/60">Điểm khởi hành</div>
              </div>
              <div className="flex items-center justify-center">
                <PlaneTakeoff size={28} className="text-[#C5A059]" />
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-[#0B3C5D]/60">
                  Destination
                </div>
                <div className="mt-2 text-base font-semibold text-[#0B3C5D]">
                  CULINARY PASSPORT
                </div>
                <div className="mt-1 text-xs text-[#0B3C5D]/60">Hành trình đa hương vị</div>
              </div>
            </div>

            <div className="mt-4 grid gap-4 rounded-2xl border border-[#0B3C5D]/10 bg-[#FDFBF7] p-4 sm:grid-cols-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#0B3C5D]/60">
                  Passenger
                </div>
                <div className="mt-2 text-sm font-semibold text-[#0B3C5D]">
                  Người xinh đẹp nhất thế giới
                </div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#0B3C5D]/60">
                  Total allowance
                </div>
                <div className="mt-2 text-sm font-semibold text-[#0B3C5D]">
                  {totalAllowance}
                </div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#0B3C5D]/60">
                  Gate time
                </div>
                <div className="mt-2 text-sm font-semibold text-[#0B3C5D]">
                  {nowLabel}
                </div>
              </div>
            </div>

            <div className="mt-6 space-y-4">
              {sanitizedMeals.map((meal, index) => (
                <div key={`${meal.label}-${index}`} className="flex items-center gap-4">
                  <div className="flex items-center gap-2 text-[#0B3C5D]">
                    <Clock size={16} className="text-[#C5A059]" />
                    <div className="text-xs font-semibold tracking-[0.2em]">
                      {meal.time}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.3em] text-[#0B3C5D]/60">
                      {meal.label}
                    </div>
                    <div className="mt-1 text-sm font-semibold text-[#0B3C5D] truncate">
                      {meal.name}
                    </div>
                    <div className="mt-1 text-xs text-[#0B3C5D]/60">
                      {meal.rating.toFixed(1)} sao
                    </div>
                  </div>
                  <div className="text-sm font-semibold text-[#0B3C5D]">
                    {meal.price}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-[#0B3C5D]/60">
                  Mã vé
                </div>
                <div className="flex flex-wrap items-center gap-1">
                  {Array.from({ length: 28 }).map((_, index) => (
                    <span
                      key={`bar-${index}`}
                      className={cn(
                        "h-6 w-1 rounded-full",
                        index % 3 === 0 ? "bg-[#0B3C5D]" : "bg-[#C5A059]/70"
                      )}
                    />
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-2xl border border-[#0B3C5D]/10 bg-[#FDFBF7] px-4 py-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#FAFAFA] text-[#C5A059] shadow-soft">
                  <QrCode size={20} />
                </span>
                <div>
                  <div className="text-xs font-semibold text-[#0B3C5D]">
                    Quét để tự tạo lộ trình tại BMI
                  </div>
                  <div className="mt-1 text-[10px] font-semibold uppercase tracking-[0.3em] text-[#C5A059]">
                    LOGISTICALLY OPTIMIZED BY AI
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}

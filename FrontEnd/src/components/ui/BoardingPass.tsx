"use client";

import { useMemo, useRef, useState } from "react";
import html2canvas from "html2canvas";
import { Compass, Clock, Ticket, QrCode, Sparkles, Download } from "lucide-react";
import { cn } from "@/lib/utils";

type MealStop = {
  label: string;
  name: string;
  time: string;
  price: string;
  type: string;
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

  const handleExport = async () => {
    if (!passRef.current || isExporting) {
      return;
    }
    setIsExporting(true);
    try {
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
        <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
          Xuất vé ẩm thực
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleShare}
            className="inline-flex items-center gap-2 rounded-full border border-slate-200/70 bg-white px-4 py-2 text-xs font-semibold text-slate-600 shadow-soft"
          >
            <Sparkles size={14} />
            Chia sẻ
          </button>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-4 py-2 text-xs font-semibold text-white shadow-glow"
          >
            <Download size={14} />
            {isExporting ? "Đang xuất..." : "Tải ảnh"}
          </button>
        </div>
      </div>

      <div className="flex justify-center">
        <div
          ref={passRef}
          className="relative h-[800px] w-[450px] overflow-hidden rounded-[30px] border border-slate-200/80 bg-[#FAFAFA] p-6 shadow-[0_32px_80px_rgba(15,23,42,0.14)] before:absolute before:left-[-18px] before:top-[210px] before:h-9 before:w-9 before:rounded-full before:bg-[#FAFAFA] before:shadow-[0_0_0_8px_rgba(250,250,250,1)] after:absolute after:right-[-18px] after:top-[210px] after:h-9 after:w-9 after:rounded-full after:bg-[#FAFAFA] after:shadow-[0_0_0_8px_rgba(250,250,250,1)]"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,106,61,0.10),_transparent_45%),radial-gradient(circle_at_bottom,_rgba(12,139,214,0.10),_transparent_50%)]" />
          <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-brand-coral via-brand-flame to-brand-lagoon" />
          <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-amber-300 via-amber-200 to-brand-coral" />
          <div className="relative">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-coral to-brand-flame text-white shadow-glow">
                  <Compass size={22} />
                </span>
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.35em] text-brand-lagoon">
                    BMI
                  </div>
                  <div className="font-display text-xl font-semibold text-slate-900">
                    Food Itinerary Pass
                  </div>
                </div>
              </div>
              <div className="text-xs font-semibold uppercase tracking-[0.4em] text-slate-600">
                BUSINESS CLASS
              </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <div className="inline-flex items-center gap-2 rounded-full border border-amber-200/70 bg-amber-50 px-3 py-1 text-[11px] font-semibold text-amber-700 shadow">
                <Ticket size={14} />
                AI-OPTIMIZED
              </div>
              <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                {nowLabel}
              </div>
            </div>

            <div className="mt-5 h-px w-full border-t border-dashed border-slate-300" />

            <div className="mt-5 grid gap-4 rounded-2xl border border-slate-200/70 bg-white/90 p-4 sm:grid-cols-2">
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                  Departure
                </div>
                <div className="mt-2 text-base font-semibold text-slate-900">
                  {departure || "Chưa chọn vị trí"}
                </div>
                <div className="mt-1 text-xs text-slate-500">Điểm khởi hành</div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                  Destination
                </div>
                <div className="mt-2 text-base font-semibold text-slate-900">
                  CITY CULINARY
                </div>
                <div className="mt-1 text-xs text-slate-500">Hành trình đa hương vị</div>
              </div>
            </div>

            <div className="mt-4 grid gap-4 rounded-2xl border border-slate-200/70 bg-white/90 p-4 sm:grid-cols-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500">
                  Passenger
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  Người xinh đẹp nhất thế giới
                </div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500">
                  Total allowance
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {totalAllowance}
                </div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-500">
                  Gate time
                </div>
                <div className="mt-2 text-sm font-semibold text-slate-900">
                  {nowLabel}
                </div>
              </div>
            </div>

            <div className="mt-6 space-y-5">
              {sanitizedMeals.map((meal, index) => (
                <div key={`${meal.label}-${index}`} className="flex items-start gap-4">
                  <div className="flex flex-col items-center">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-brand-flame shadow">
                      <Clock size={18} />
                    </span>
                    {index < sanitizedMeals.length - 1 && (
                      <div className="mt-2 h-10 w-px border-l border-dashed border-slate-300" />
                    )}
                  </div>
                  <div className="flex-1 rounded-2xl border border-slate-200/70 bg-white px-4 py-3 shadow-sm">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="inline-flex items-center gap-2 text-sm font-semibold text-slate-900">
                        <Sparkles size={14} className="text-brand-coral" />
                        {meal.label}
                      </div>
                      <div className="text-xs font-semibold text-brand-lagoon">
                        {meal.time}
                      </div>
                    </div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">
                      {meal.name}
                    </div>
                    <div className="mt-1 text-xs text-slate-500">
                      {meal.type}
                    </div>
                    <div className="mt-2 text-xs font-semibold text-slate-500">
                      {meal.price}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
                  Mã vé
                </div>
                <div className="flex flex-wrap items-center gap-1">
                  {Array.from({ length: 28 }).map((_, index) => (
                    <span
                      key={`bar-${index}`}
                      className={cn(
                        "h-6 w-1 rounded-full",
                        index % 3 === 0 ? "bg-slate-900" : "bg-slate-400"
                      )}
                    />
                  ))}
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200/70 bg-white/90 px-4 py-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-brand-lagoon shadow">
                  <QrCode size={20} />
                </span>
                <div>
                  <div className="text-xs font-semibold text-slate-600">
                    Quét để tự tạo lộ trình tại BMI
                  </div>
                  <div className="mt-1 text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                    YOUR JOURNEY, OUR TASTE.
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

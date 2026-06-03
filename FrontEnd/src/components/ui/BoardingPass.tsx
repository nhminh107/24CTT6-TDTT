"use client";

import { useMemo, useRef, useState } from "react";
import html2canvas from "html2canvas";
import { Compass, Clock, PlaneTakeoff, QrCode, Sparkles, Download, X, Star } from "lucide-react";
import { cn } from "@/lib/utils";

type BoardingPassProps = {
  itinerary: any[];
  onClose: () => void;
  className?: string;
};

export default function BoardingPass({
  itinerary,
  onClose,
  className
}: BoardingPassProps) {
  const passRef = useRef<HTMLDivElement | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const totalBudget = useMemo(() => {
    return itinerary.reduce((sum, item) => {
      const p = item.avg_price !== undefined ? item.avg_price : item.price;
      const numericPrice = typeof p === "number" ? p : 0;
      return sum + numericPrice;
    }, 0);
  }, [itinerary]);

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
      link.download = "bmi-boarding-pass.png";
      link.click();
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className={cn("relative flex max-w-lg flex-col gap-4 overflow-hidden rounded-[32px] bg-white p-6 shadow-2xl", className)}>
        <button
          onClick={onClose}
          className="absolute right-4 top-4 z-10 flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200"
        >
          <X size={20} />
        </button>

        <div className="flex flex-wrap items-center justify-between gap-3 pr-12">
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-[#C5A059]">
            Vé ẩm thực của bạn
          </div>
          <button
            type="button"
            onClick={handleExport}
            className="inline-flex items-center gap-2 rounded-full bg-[#0B3C5D] px-4 py-2 text-xs font-semibold text-[#C5A059] shadow-glow"
          >
            <Download size={14} />
            {isExporting ? "Đang xuất..." : "Tải ảnh"}
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto">
          <div
            ref={passRef}
            className="relative w-[450px] overflow-hidden rounded-[24px] border border-[#0B3C5D]/15 bg-[#FAFAFA] p-6 shadow-sm"
          >
            <div className="absolute inset-x-0 top-0 h-[120px] bg-[#0B3C5D]" />
            <div className="relative">
              <div className="flex items-center justify-between">
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
                <div className="text-right">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#C5A059]">
                    PREMIUM GUEST
                  </div>
                  <div className="mt-1 text-xs font-bold text-white">#{Math.random().toString(36).substr(2, 6).toUpperCase()}</div>
                </div>
              </div>

              <div className="mt-8 grid gap-4 rounded-2xl border border-[#0B3C5D]/10 bg-[#FDFBF7] p-4 grid-cols-[1fr_auto_1fr]">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#0B3C5D]/60">
                    Departure
                  </div>
                  <div className="mt-1 text-sm font-bold text-[#0B3C5D]">
                    BMI SMART APP
                  </div>
                </div>
                <div className="flex items-center justify-center">
                  <PlaneTakeoff size={24} className="text-[#C5A059]" />
                </div>
                <div className="text-right">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#0B3C5D]/60">
                    Destination
                  </div>
                  <div className="mt-1 text-sm font-bold text-[#0B3C5D]">
                    YUMMY WORLD
                  </div>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 rounded-2xl border border-[#0B3C5D]/10 bg-[#FDFBF7] p-4">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#0B3C5D]/60">
                    Total Budget
                  </div>
                  <div className="mt-1 text-sm font-bold text-brand-flame">
                    {totalBudget.toLocaleString("vi-VN")} VNĐ
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#0B3C5D]/60">
                    Issue Date
                  </div>
                  <div className="mt-1 text-sm font-bold text-[#0B3C5D]">
                    {nowLabel}
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <div className="text-[10px] font-semibold uppercase tracking-[0.3em] text-[#0B3C5D]/60">
                  Culinary Stops
                </div>
                {itinerary.map((stop, index) => (
                  <div key={`${stop.meal}-${index}`} className="flex items-center gap-4 border-b border-slate-100 pb-3 last:border-0">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-orange-50 text-[10px] font-bold text-orange-600">
                      {stop.meal}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-bold text-[#0B3C5D] truncate">
                        {stop.name}
                      </div>
                      <div className="mt-0.5 text-[10px] text-slate-500 truncate">
                        {stop.address}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Star size={10} className="fill-yellow-400 text-yellow-400" />
                        <span className="text-[10px] font-bold">{stop.star || stop.rating || 0}</span>
                      </div>
                      <div className="mt-0.5 text-[10px] font-bold text-brand-teal">
                        {(() => {
                          const p = stop.avg_price !== undefined ? stop.avg_price : stop.price;
                          if (typeof p === "number") {
                            return `${p.toLocaleString("vi-VN")}đ`;
                          }
                          return p || "Chưa cập nhật";
                        })()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-8 flex items-center justify-between border-t border-dashed border-[#C5A059]/40 pt-6">
                <div className="space-y-2">
                  <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#0B3C5D]/60">
                    Auth Ticket
                  </div>
                  <div className="flex items-center gap-1">
                    {Array.from({ length: 20 }).map((_, i) => (
                      <span key={i} className={cn("h-8 w-[2px]", i % 4 === 0 ? "bg-[#0B3C5D]" : "bg-[#C5A059]/40")} />
                    ))}
                  </div>
                </div>
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-soft">
                  <QrCode size={40} className="text-[#0B3C5D]" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

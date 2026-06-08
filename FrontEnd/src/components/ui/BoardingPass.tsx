"use client";

import { useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import html2canvas from "html2canvas";
import { Compass, PlaneTakeoff, QrCode, Download, X, Star } from "lucide-react";
import { cn, formatMealDisplay } from "@/lib/utils";

const EXPORT_WIDTH = 450;
const EXPORT_MIN_HEIGHT = 680;
const EXPORT_MAX_HEIGHT = 960;

function getExportHeight(stopCount: number): number {
  const base = 520;
  const perStop = stopCount <= 3 ? 72 : stopCount <= 5 ? 58 : 48;
  return Math.min(EXPORT_MAX_HEIGHT, Math.max(EXPORT_MIN_HEIGHT, base + stopCount * perStop));
}

function getExportStopTier(stopCount: number): "normal" | "medium" | "compact" {
  if (stopCount <= 2) return "normal";
  if (stopCount <= 4) return "medium";
  return "compact";
}

function TicketSvgIcon({
  name,
  size,
  className,
}: {
  name: "compass" | "plane" | "star" | "qr";
  size: number;
  className?: string;
}) {
  const strokeColor = name === "qr" ? "#0B3C5D" : "#C5A059";

  if (name === "compass") {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden className={className}>
        <circle cx="12" cy="12" r="10" stroke="#C5A059" strokeWidth="2" />
        <path d="m16.24 7.76-2.12 6.36-6.36 2.12 2.12-6.36 6.36-2.12z" fill="#C5A059" stroke="#C5A059" strokeWidth="1.5" />
      </svg>
    );
  }
  if (name === "plane") {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden className={className}>
        <path d="M2 22h20" stroke="#C5A059" strokeWidth="2" strokeLinecap="round" />
        <path d="M6.36 17.4 4 17l-2-4 1.1-.55a2 2 0 0 1 1.8 0l.17.1a2 2 0 0 0 1.8 0L8 12 5 3l.5-.5a2 2 0 0 1 2.3-.3l12.9 6.4a2 2 0 0 1 .7 3.2L8.5 17.2a2 2 0 0 1-2.1-.8Z" fill="#C5A059" stroke="#C5A059" strokeWidth="1.5" />
      </svg>
    );
  }
  if (name === "star") {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden className={className}>
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.56 5.82 22 7 14.14l-5-4.87 6.91-1.01L12 2z" fill="#FACC15" stroke="#FACC15" strokeWidth="1" />
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden className={className}>
      <rect x="3" y="3" width="7" height="7" stroke={strokeColor} strokeWidth="2" />
      <rect x="14" y="3" width="7" height="7" stroke={strokeColor} strokeWidth="2" />
      <rect x="3" y="14" width="7" height="7" stroke={strokeColor} strokeWidth="2" />
      <path d="M14 14h2v2h-2zM18 14h2v2h-2zM14 18h2v2h-2zM18 18h3v3h-3z" fill={strokeColor} />
    </svg>
  );
}

type BoardingPassProps = {
  itinerary: any[];
  onClose: () => void;
  className?: string;
  variant?: "inline" | "modal";
};

type TicketLayout = "inline" | "modal" | "export";

function BoardingPassTicket({
  itinerary,
  layout,
  totalBudget,
  nowLabel,
  ticketNumber,
}: {
  itinerary: any[];
  layout: TicketLayout;
  totalBudget: number;
  nowLabel: string;
  ticketNumber: string;
}) {
  const isExport = layout === "export";
  const isInline = layout === "inline";
  const exportStopTier = isExport ? getExportStopTier(itinerary.length) : null;
  const isCompactExport = exportStopTier === "compact";
  const isMediumExport = exportStopTier === "medium";

  const renderIcon = (
    name: "compass" | "plane" | "star" | "qr",
    size: number,
    lucideClassName?: string
  ) => {
    if (isExport) {
      return <TicketSvgIcon name={name} size={size} />;
    }
    if (name === "compass") return <Compass size={size} />;
    if (name === "plane") return <PlaneTakeoff size={size} className={lucideClassName} />;
    if (name === "star") return <Star size={size} className={lucideClassName} />;
    return <QrCode size={size} className={lucideClassName} />;
  };

  return (
    <div
      className={cn(
        "relative overflow-hidden border border-[#0B3C5D]/15 bg-[#FAFAFA] shadow-sm",
        isExport && "box-border w-[450px] rounded-[24px] p-6",
        !isExport && isInline && "mx-auto w-full max-w-full rounded-[20px] p-3",
        !isExport && !isInline && "mx-auto w-full max-w-[450px] rounded-[24px] p-6"
      )}
      style={isExport ? { width: EXPORT_WIDTH, minHeight: getExportHeight(itinerary.length) } : undefined}
    >
      <div
        className={cn(
          "absolute inset-x-0 top-0 bg-[#0B3C5D]",
          isExport || !isInline ? "h-[120px]" : "h-[100px]"
        )}
      />
      <div className={cn("relative flex min-w-0 flex-col", isExport ? "min-h-full" : "h-full")}>
        <div className="flex shrink-0 items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span
              className={cn(
                "flex shrink-0 items-center justify-center rounded-2xl bg-[#0B3C5D] text-[#C5A059] shadow-soft",
                isExport || !isInline ? "h-12 w-12" : "h-9 w-9 rounded-xl"
              )}
            >
              {renderIcon("compass", isExport || !isInline ? 22 : 16)}
            </span>
            <div className="min-w-0">
              <div
                className={cn(
                  "font-semibold uppercase text-[#C5A059]",
                  isExport ? "text-xs leading-normal tracking-[0.35em]" : isInline ? "text-[9px] tracking-[0.15em]" : "text-xs tracking-[0.35em]"
                )}
              >
                BMI
              </div>
              <div
                className={cn(
                  "font-display font-semibold text-white",
                  isExport ? "text-xl leading-snug" : isInline ? "truncate text-sm" : "text-xl"
                )}
              >
                Food Itinerary Pass
              </div>
            </div>
          </div>
          <div className={cn("shrink-0 text-right", isExport && "min-w-[110px]")}>
            <div
              className={cn(
                "font-semibold uppercase text-[#C5A059]",
                isExport ? "text-[10px] leading-normal tracking-[0.2em]" : isInline ? "truncate text-[8px] tracking-[0.1em]" : "text-[10px] tracking-[0.2em]"
              )}
            >
              PREMIUM GUEST
            </div>
            <div
              className={cn(
                "mt-1 font-bold text-white",
                isExport ? "text-xs leading-normal" : isInline ? "truncate text-[9px]" : "text-xs"
              )}
            >
              #{ticketNumber}
            </div>
          </div>
        </div>

        <div
          className={cn(
            "mt-8 grid shrink-0 grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] rounded-2xl border border-[#0B3C5D]/10 bg-[#FDFBF7]",
            isExport ? "gap-4 p-4" : isInline ? "mt-4 gap-1 p-2.5 rounded-xl" : "gap-4 p-4"
          )}
        >
          <div className="min-w-0">
            <div className={cn("font-semibold uppercase text-[#0B3C5D]/60", isExport ? "text-[10px] leading-normal tracking-[0.2em]" : isInline ? "text-[9px] tracking-[0.1em]" : "text-[10px] tracking-[0.2em]")}>
              Departure
            </div>
            <div className={cn("mt-1 font-bold text-[#0B3C5D]", isExport ? "text-sm leading-normal" : isInline ? "truncate text-[10px]" : "text-sm")}>
              BMI SMART APP
            </div>
          </div>
          <div className="flex shrink-0 items-center justify-center px-1">
            {renderIcon("plane", isExport || !isInline ? 24 : 16, "text-[#C5A059]")}
          </div>
          <div className="min-w-0 text-right">
            <div className={cn("font-semibold uppercase text-[#0B3C5D]/60", isExport ? "text-[10px] leading-normal tracking-[0.2em]" : isInline ? "text-[9px] tracking-[0.1em]" : "text-[10px] tracking-[0.2em]")}>
              Destination
            </div>
            <div className={cn("mt-1 font-bold text-[#0B3C5D]", isExport ? "text-sm leading-normal" : isInline ? "truncate text-[10px]" : "text-sm")}>
              YUMMY WORLD
            </div>
          </div>
        </div>

        <div
          className={cn(
            "mt-4 grid shrink-0 grid-cols-2 rounded-2xl border border-[#0B3C5D]/10 bg-[#FDFBF7]",
            isExport ? "gap-4 p-4" : isInline ? "mt-2.5 gap-2 p-2.5 rounded-xl" : "gap-4 p-4"
          )}
        >
          <div className="min-w-0">
            <div className={cn("font-semibold uppercase text-[#0B3C5D]/60", isExport ? "text-[10px] leading-normal tracking-[0.2em]" : isInline ? "text-[9px] tracking-[0.1em]" : "text-[10px] tracking-[0.2em]")}>
              Total Budget
            </div>
            <div className={cn("mt-1 font-bold text-brand-flame", isExport ? "text-sm leading-normal" : isInline ? "truncate text-xs" : "text-sm")}>
              {totalBudget.toLocaleString("vi-VN")} VNĐ
            </div>
          </div>
          <div className="min-w-0 text-right">
            <div className={cn("font-semibold uppercase text-[#0B3C5D]/60", isExport ? "text-[10px] leading-normal tracking-[0.2em]" : isInline ? "text-[9px] tracking-[0.1em]" : "text-[10px] tracking-[0.2em]")}>
              Issue Date
            </div>
            <div className={cn("mt-1 font-bold text-[#0B3C5D]", isExport ? "text-sm leading-normal" : isInline ? "truncate text-[10px]" : "text-sm")}>
              {nowLabel}
            </div>
          </div>
        </div>

        <div className={cn("mt-6 flex flex-col", isInline && !isExport && "mt-4", isExport && "flex-1")}>
          <div className={cn("shrink-0 font-semibold uppercase text-[#0B3C5D]/60", isExport ? "text-[10px] leading-normal tracking-[0.3em]" : isInline ? "text-[9px] tracking-[0.15em]" : "text-[10px] tracking-[0.3em]")}>
            Culinary Stops
          </div>
          <div className={cn("mt-3", isExport && "flex-1")}>
            <div
              className={cn(
                isCompactExport ? "space-y-2" : isMediumExport ? "space-y-2.5" : "space-y-3"
              )}
            >
              {itinerary.map((stop, index) => (
                <div
                  key={`${stop.meal}-${index}`}
                  className={cn(
                    "flex min-w-0 items-start gap-3 border-b border-slate-100 last:border-0",
                    isCompactExport ? "gap-2 pb-2" : isMediumExport ? "pb-2.5" : "pb-3",
                    isInline && !isExport && "items-center gap-2 pb-2.5"
                  )}
                >
                  <div
                    className={cn(
                      "flex shrink-0 items-center justify-center rounded-xl bg-orange-50 text-center font-bold text-orange-600",
                      isCompactExport ? "h-8 w-8 text-[9px] px-0.5" : isMediumExport ? "h-9 w-9 text-[9px] px-0.5" : isExport || !isInline ? "h-10 w-10 text-[10px] px-1" : "h-9 w-9 rounded-lg text-[9px] px-0.5"
                    )}
                  >
                    {formatMealDisplay(stop.meal)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div
                      className={cn(
                        "font-bold text-[#0B3C5D]",
                        isCompactExport ? "text-xs leading-snug break-words" : isMediumExport ? "text-sm leading-snug break-words" : isExport ? "text-sm leading-snug break-words" : isInline ? "truncate text-xs" : "truncate text-sm"
                      )}
                    >
                      {stop.name}
                    </div>
                    <div
                      className={cn(
                        "mt-0.5 text-slate-500",
                        isCompactExport ? "text-[9px] leading-normal break-words line-clamp-1" : isMediumExport ? "text-[10px] leading-normal break-words line-clamp-2" : isExport ? "text-[10px] leading-normal break-words" : isInline ? "truncate text-[9px]" : "truncate text-[10px]"
                      )}
                    >
                      {stop.address}
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {renderIcon("star", isExport || !isInline ? 10 : 9, "fill-yellow-400 text-yellow-400")}
                      <span className={cn("font-bold", isExport || !isInline ? "text-[10px] leading-normal" : "text-[9px]")}>
                        {stop.star || stop.rating || 0}
                      </span>
                    </div>
                    <div className={cn("mt-0.5 font-bold text-brand-teal", isExport || !isInline ? "text-[10px] leading-normal" : "text-[9px]")}>
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
          </div>
        </div>

        <div
          className={cn(
            "mt-auto flex shrink-0 items-center justify-between gap-3 border-t border-dashed border-[#C5A059]/40 pt-6",
            isInline && !isExport && "mt-4 pt-3"
          )}
        >
          <div className="min-w-0 flex-1 space-y-2">
            <div className={cn("font-semibold uppercase text-[#0B3C5D]/60", isExport ? "text-[10px] leading-normal tracking-[0.2em]" : isInline ? "text-[9px] tracking-[0.1em]" : "text-[10px] tracking-[0.2em]")}>
              Auth Ticket
            </div>
            <div className="flex max-w-full items-center gap-1">
              {Array.from({ length: 20 }).map((_, i) => (
                <span
                  key={i}
                  className={cn(
                    "w-[2px] shrink-0",
                    isExport || !isInline ? "h-8" : "h-6",
                    i % 4 === 0 ? "bg-[#0B3C5D]" : "bg-[#C5A059]/40"
                  )}
                />
              ))}
            </div>
          </div>
          <div
            className={cn(
              "flex shrink-0 items-center justify-center rounded-2xl bg-white shadow-soft",
              isExport || !isInline ? "h-16 w-16" : "h-10 w-10 rounded-xl"
            )}
          >
            {renderIcon("qr", isExport || !isInline ? 40 : 24, "text-[#0B3C5D]")}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BoardingPass({
  itinerary,
  onClose,
  className,
  variant = "inline",
}: BoardingPassProps) {
  const passRef = useRef<HTMLDivElement | null>(null);
  const exportRef = useRef<HTMLDivElement | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const ticketNumber = useMemo(
    () => Math.random().toString(36).substr(2, 6).toUpperCase(),
    []
  );

  const totalBudget = useMemo(() => {
    return itinerary.reduce((sum, item) => {
      const p = item.avg_price !== undefined ? item.avg_price : item.price;
      const numericPrice = typeof p === "number" ? p : 0;
      return sum + numericPrice;
    }, 0);
  }, [itinerary]);

  const nowLabel = useMemo(
    () =>
      new Date().toLocaleString("vi-VN", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }),
    []
  );

  const waitForStableLayout = async () => {
    if (document.fonts?.ready) {
      await document.fonts.ready;
    }
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  };

  const handleExport = async () => {
    if (!exportRef.current || isExporting) {
      return;
    }
    setIsExporting(true);
    const node = exportRef.current;

    try {
      await waitForStableLayout();
      const canvas = await html2canvas(node, {
        useCORS: true,
        scale: 2,
        backgroundColor: "#ffffff",
        logging: false,
        onclone: (clonedDoc, clonedElement) => {
          const el = clonedElement as HTMLElement;
          el.style.visibility = "visible";
          el.style.opacity = "1";
          el.style.position = "static";
          el.style.left = "0";
          el.style.top = "0";
          el.style.overflow = "visible";

          el.querySelectorAll("svg").forEach((svg) => {
            const htmlSvg = svg as SVGSVGElement;
            if (!htmlSvg.getAttribute("width")) {
              htmlSvg.setAttribute("width", String(htmlSvg.clientWidth || 24));
            }
            if (!htmlSvg.getAttribute("height")) {
              htmlSvg.setAttribute("height", String(htmlSvg.clientHeight || 24));
            }
          });

          let parent = el.parentElement;
          while (parent && parent !== clonedDoc.body) {
            parent.style.visibility = "visible";
            parent.style.opacity = "1";
            parent.style.overflow = "visible";
            parent = parent.parentElement;
          }
        },
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

  const isInline = variant === "inline";
  const displayLayout: TicketLayout = isInline ? "inline" : "modal";
  const exportHeight = useMemo(() => getExportHeight(itinerary.length), [itinerary.length]);

  const passContent = (
    <>
      {typeof document !== "undefined" &&
        createPortal(
          <div
            aria-hidden
            ref={exportRef}
            className="pointer-events-none fixed left-0 top-0"
            style={{ width: EXPORT_WIDTH, minHeight: exportHeight, zIndex: -1, visibility: "hidden" }}
          >
            <BoardingPassTicket
              itinerary={itinerary}
              layout="export"
              totalBudget={totalBudget}
              nowLabel={nowLabel}
              ticketNumber={ticketNumber}
            />
          </div>,
          document.body
        )}

      <div
        className={cn(
          "relative flex w-full min-w-0 max-w-full flex-col gap-3 overflow-hidden",
          isInline ? "h-full flex-1" : "max-w-lg rounded-[32px] bg-white p-6 shadow-2xl",
          className
        )}
      >
        <div className="flex shrink-0 items-center justify-between gap-2">
          <div className="min-w-0 truncate text-[10px] font-semibold uppercase tracking-[0.15em] text-[#C5A059]">
            Vé ẩm thực của bạn
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            <button
              type="button"
              onClick={handleExport}
              className={cn(
                "inline-flex items-center rounded-full bg-[#0B3C5D] font-semibold text-[#C5A059] shadow-glow",
                isInline ? "gap-1 px-2.5 py-1.5 text-[9px]" : "gap-2 px-4 py-2 text-xs"
              )}
            >
              <Download size={isInline ? 12 : 14} />
              {isExporting ? "Đang xuất..." : "Tải ảnh"}
            </button>
            <button
              onClick={onClose}
              className={cn(
                "flex items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200",
                isInline ? "h-7 w-7" : "h-10 w-10"
              )}
            >
              <X size={isInline ? 16 : 18} />
            </button>
          </div>
        </div>

        <div
          className={cn(
            "min-h-0 min-w-0 w-full max-w-full overflow-x-hidden overflow-y-auto",
            isInline ? "flex-1" : "max-h-[70vh]"
          )}
        >
          <div ref={passRef}>
            <BoardingPassTicket
              itinerary={itinerary}
              layout={displayLayout}
              totalBudget={totalBudget}
              nowLabel={nowLabel}
              ticketNumber={ticketNumber}
            />
          </div>
        </div>
      </div>
    </>
  );

  if (variant === "modal" && typeof document !== "undefined") {
    return createPortal(
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
        {passContent}
      </div>,
      document.body
    );
  }

  return passContent;
}

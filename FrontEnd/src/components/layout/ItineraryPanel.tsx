"use client";

import { motion, Reorder } from "framer-motion";
import { Star, X, Trash2, Ticket, Map as MapIcon, GripVertical } from "lucide-react";
import { useRef, useMemo, useState, useEffect } from "react";
import Link from "next/link";
import RestaurantCard from "@/components/ui/RestaurantCard";
import BoardingPass from "@/components/ui/BoardingPass";
import { formatMealDisplay } from "@/lib/utils";

type ItineraryPanelProps = {
  location: string;
  budget: string;
  mealStops: any[];
  restaurants: any[];
  selectedRestaurantId: string | null;
  currentTab: "itinerary" | "detail";
  onSelectRestaurant: (id: string) => void;
  onTabChange: (tab: "itinerary" | "detail") => void;
  onCloseDetail: () => void;
  currentItinerary?: any[];
  onDeleteMeal?: (id: string) => void;
  onResetItinerary?: () => void;
  onReorder?: (orderedItems: { id: string }[]) => void;
  showBoardingPass?: boolean;
  onShowBoardingPassChange?: (open: boolean) => void;
  hasHealthProfile?: boolean;
  onOpenHealthProfile?: () => void;
};

export default function ItineraryPanel({
  location,
  budget,
  mealStops,
  restaurants,
  selectedRestaurantId,
  currentTab,
  onSelectRestaurant,
  onTabChange,
  onCloseDetail,
  currentItinerary = [],
  onDeleteMeal,
  onResetItinerary,
  onReorder,
  showBoardingPass = false,
  onShowBoardingPassChange,
  hasHealthProfile = false,
  onOpenHealthProfile,
}: ItineraryPanelProps) {
  const [localItinerary, setLocalItinerary] = useState(currentItinerary);
  const isInternalUpdate = useRef(false);
  const hasItineraryItems = currentItinerary.length > 0;

  // Đồng bộ local state khi prop thay đổi (ví dụ khi thêm/xóa bữa ăn từ server)
  useEffect(() => {
    // Nếu đây là bản cập nhật do chính component này thực hiện (kéo thả), bỏ qua đồng bộ để tránh bị giật/reset
    if (isInternalUpdate.current) {
      isInternalUpdate.current = false;
      return;
    }
    setLocalItinerary(currentItinerary);
  }, [currentItinerary]);

  const handleReorder = (newOrder: any[]) => {
    isInternalUpdate.current = true;
    setLocalItinerary(newOrder);

    // Reorder chỉ thay đổi thứ tự hiển thị, không đổi nhãn bữa ăn của nhà hàng.
    if (onReorder) {
      onReorder(newOrder.map(item => ({ id: item.id })));
    }
  };

  const selectedRestaurant = useMemo(
    () => restaurants.find((r) => r.id === selectedRestaurantId) || 
          currentItinerary.find((r) => r.id === selectedRestaurantId) || null,
    [restaurants, currentItinerary, selectedRestaurantId]
  );

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      {/* Tab Buttons */}
      <div className="flex gap-2 overflow-x-auto border-b border-slate-200/60">
        <button
          onClick={() => onTabChange("itinerary")}
          className={`shrink-0 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] transition sm:px-4 sm:tracking-[0.2em] ${
            currentTab === "itinerary"
              ? "border-b-2 border-brand-coral text-brand-coral"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Lịch trình
        </button>
        <button
          onClick={() => onTabChange("detail")}
          className={`shrink-0 px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] transition sm:px-4 sm:tracking-[0.2em] ${
            currentTab === "detail"
              ? "border-b-2 border-brand-coral text-brand-coral"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Chi tiết
        </button>
      </div>

      {/* Content */}
      {currentTab === "itinerary" ? (
        showBoardingPass ? (
          <div className="flex min-h-0 min-w-0 w-full max-w-full flex-1 flex-col overflow-hidden">
            <BoardingPass
              variant="inline"
              itinerary={currentItinerary}
              onClose={() => onShowBoardingPassChange?.(false)}
            />
          </div>
        ) : (
        <div className="flex flex-1 flex-col gap-4 overflow-hidden">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-flame">
              Lịch trình của bạn
            </h2>
            {currentItinerary.length > 0 && (
              <button
                onClick={onResetItinerary}
                className="text-[10px] font-bold text-slate-400 hover:text-rose-500"
              >
                Đặt lại
              </button>
            )}
          </div>

          <Link
            href="/explore"
            className={`group relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl border py-2.5 text-[10px] font-bold transition-all active:scale-[0.98] ${
              hasItineraryItems
                ? "border-brand-coral/40 bg-gradient-to-r from-brand-coral to-brand-flame text-white shadow-glow hover:shadow-lg"
                : "border-slate-200 bg-slate-50 text-slate-600 shadow-sm hover:border-brand-coral hover:bg-white hover:text-brand-coral"
            }`}
          >
            {hasItineraryItems && (
              <span className="pointer-events-none absolute inset-y-0 -left-1/3 w-1/3 animate-[map-button-shine_2.4s_ease-in-out_infinite] bg-white/25 blur-md" />
            )}
            <MapIcon
              size={14}
              className={`relative transition-colors ${
                hasItineraryItems ? "text-white" : "text-slate-400 group-hover:text-brand-coral"
              }`}
            />
            <span className="relative">XEM BẢN ĐỒ KHÁM PHÁ</span>
          </Link>

          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            {/* Meal Stops Timeline */}
            {localItinerary.length > 0 ? (
              <Reorder.Group
                axis="y"
                values={localItinerary}
                onReorder={handleReorder}
                className="space-y-3"
              >
                {localItinerary.map((stop, index) => (
                  <Reorder.Item
                    key={stop.id}
                    value={stop}
                    className="group relative"
                  >
                    <button
                      type="button"
                      onClick={() => onSelectRestaurant(stop.id)}
                      className="w-full text-left rounded-xl border border-slate-200/60 bg-white/50 p-3 pl-8 transition hover:border-brand-coral hover:bg-white"
                    >
                      {/* Drag Handle */}
                      <div className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-300 cursor-grab active:cursor-grabbing">
                        <GripVertical size={16} />
                      </div>

                      {/* Stop Label */}
                      <div className="mb-2 flex items-center justify-between">
                        <span className="inline-flex items-center rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-2.5 py-0.5 text-[10px] font-bold text-white">
                          {formatMealDisplay(stop.meal)}
                        </span>
                      </div>

                      {/* Restaurant Info */}
                      <div className="space-y-1.5">
                        <p className="text-xs font-bold text-slate-900 line-clamp-2 pr-6">
                          {stop.name}
                        </p>
                        <p className="text-[10px] text-slate-500 line-clamp-1">
                          {stop.address}
                        </p>

                          <div className="flex items-center gap-2">
                            <div className="flex items-center gap-1">
                              <Star size={10} className="fill-yellow-400 text-yellow-400" />
                              <span className="text-[10px] font-bold text-slate-600">
                                {stop.star || stop.rating || 0}
                              </span>
                            </div>
                            <div className="h-1 w-1 rounded-full bg-slate-300" />
                            <span className="text-[10px] font-semibold text-brand-teal">
                              {(() => {
                                const p = stop.avg_price !== undefined ? stop.avg_price : stop.price;
                                if (typeof p === "number") {
                                  return `${p.toLocaleString("vi-VN")}đ`;
                                }
                                return p || "Chưa cập nhật";
                              })()}
                            </span>
                          </div>
                      </div>
                    </button>
                    
                    <button
                      onClick={() => onDeleteMeal?.(stop.id)}
                      className="absolute right-2 top-2 rounded-lg p-1.5 text-slate-300 transition hover:bg-rose-50 hover:text-rose-500"
                    >
                      <Trash2 size={14} />
                    </button>
                  </Reorder.Item>
                ))}
              </Reorder.Group>
            ) : (
              <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-slate-200/60 bg-white/30 p-4 text-center">
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-slate-500">
                    Chưa có quán nào
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Bấm "Chọn" ở các quán AI gợi ý để lên lịch trình
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Export Button */}
          {currentItinerary.length > 0 && (
            <button
              onClick={() => onShowBoardingPassChange?.(true)}
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-coral to-brand-flame py-3 text-sm font-bold text-white shadow-glow transition hover:opacity-90"
            >
              <Ticket size={18} />
              Xuất vé ẩm thực
            </button>
          )}

        </div>
        )
      ) : selectedRestaurant ? (
        <div className="flex-1 overflow-y-auto">
          {/* Close Button */}
          <button
            onClick={onCloseDetail}
            className="mb-4 inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 transition-all duration-200 hover:border-orange-200 hover:bg-orange-50 hover:text-orange-600 shadow-sm"
          >
            <X size={14} className="stroke-[2.5]" />
            Đóng chi tiết
          </button>

          {/* Restaurant Card */}
          <div className="w-full">
            <RestaurantCard
              restaurant={selectedRestaurant}
              hasHealthProfile={hasHealthProfile}
              onOpenHealthProfile={onOpenHealthProfile}
            />
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-center rounded-2xl border border-dashed border-slate-200/60 bg-white/30 p-4 text-center">
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500">
              Chưa chọn nhà hàng
            </p>
            <p className="text-[11px] text-slate-400">
              Bấm vào nhà hàng từ lịch trình để xem chi tiết
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

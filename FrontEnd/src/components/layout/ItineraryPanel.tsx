"use client";

import { motion } from "framer-motion";
import { MapPin, Clock, DollarSign, Star, X, Trash2, Ticket, ArrowLeft, Map as MapIcon } from "lucide-react";
import { useMemo, useState } from "react";
import Link from "next/link";
import RestaurantCard from "@/components/ui/RestaurantCard";
import BoardingPass from "@/components/ui/BoardingPass";
import MapExplore from "@/components/ui/MapExplore";

type ItineraryPanelProps = {
  location: string;
  budget: string;
  mealStops: any[];
  restaurants: any[];
  selectedRestaurantId: string | null;
  currentTab: "itinerary" | "detail" | "map";
  onSelectRestaurant: (id: string) => void;
  onTabChange: (tab: "itinerary" | "detail" | "map") => void;
  onCloseDetail: () => void;
  currentItinerary?: any[];
  onDeleteMeal?: (meal: string) => void;
  onResetItinerary?: () => void;
  userPlaceId?: string;
  onItineraryChange?: () => void;
  onUserLocationChange?: (location: { location: string; placeId: string }) => void;
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
  userPlaceId,
  onItineraryChange,
  onUserLocationChange,
}: ItineraryPanelProps) {
  const [showBoardingPass, setShowBoardingPass] = useState(false);

  const selectedRestaurant = useMemo(
    () => restaurants.find((r) => r.id === selectedRestaurantId) || 
          currentItinerary.find((r) => r.id === selectedRestaurantId) || null,
    [restaurants, currentItinerary, selectedRestaurantId]
  );

  return (
    <div className="flex h-full flex-col gap-4 p-4">
      {/* Tab Buttons */}
      <div className="flex gap-2 border-b border-slate-200/60">
        <button
          onClick={() => onTabChange("itinerary")}
          className={`px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] transition ${
            currentTab === "itinerary"
              ? "border-b-2 border-brand-coral text-brand-coral"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Lịch trình
        </button>
        <button
          onClick={() => onTabChange("detail")}
          className={`px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] transition ${
            currentTab === "detail"
              ? "border-b-2 border-brand-coral text-brand-coral"
              : "text-slate-500 hover:text-slate-700"
          }`}
        >
          Chi tiết
        </button>
      </div>

      {/* Content */}
      {currentTab === "map" ? (
        <div className="flex-1 flex flex-col gap-3 overflow-hidden">
          <button
            onClick={() => onTabChange("itinerary")}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 transition-all duration-200 hover:border-brand-coral hover:bg-orange-50 hover:text-brand-coral shadow-sm w-fit"
          >
            <ArrowLeft size={14} />
            Quay lại lịch trình
          </button>
          <div className="flex-1 overflow-hidden rounded-2xl border border-slate-100 shadow-inner">
            <MapExplore
              userPlaceId={userPlaceId}
              userLocationText={location}
              currentItinerary={currentItinerary}
              onItineraryChange={onItineraryChange}
              onUserLocationChange={onUserLocationChange}
              onUserLocationChange={onUserLocationChange}
            />
          </div>
        </div>
      ) : currentTab === "itinerary" ? (
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
            className="flex items-center gap-2 w-full justify-center py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-[10px] font-bold text-slate-600 hover:bg-white hover:border-brand-coral hover:text-brand-coral transition-all shadow-sm active:scale-[0.98] group"
          >
            <MapIcon size={14} className="text-slate-400 group-hover:text-brand-coral transition-colors" />
            XEM BẢN ĐỒ KHÁM PHÁ
          </Link>

          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            {/* Meal Stops Timeline */}
            {currentItinerary.length > 0 ? (
              <div className="space-y-3">
                {currentItinerary.map((stop, index) => (
                  <motion.div
                    key={stop.meal}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="group relative"
                  >
                    <button
                      type="button"
                      onClick={() => onSelectRestaurant(stop.id)}
                      className="w-full text-left rounded-xl border border-slate-200/60 bg-white/50 p-3 transition hover:border-brand-coral hover:bg-white"
                    >
                      {/* Stop Label */}
                      <div className="mb-2 flex items-center justify-between">
                        <span className="inline-flex items-center rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-2.5 py-0.5 text-[10px] font-bold text-white">
                          {stop.meal}
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
                      onClick={() => onDeleteMeal?.(stop.meal)}
                      className="absolute right-2 top-2 rounded-lg p-1.5 text-slate-300 transition hover:bg-rose-50 hover:text-rose-500"
                    >
                      <Trash2 size={14} />
                    </button>
                  </motion.div>
                ))}
              </div>
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
              onClick={() => setShowBoardingPass(true)}
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-coral to-brand-flame py-3 text-sm font-bold text-white shadow-glow transition hover:opacity-90"
            >
              <Ticket size={18} />
              Xuất vé ẩm thực
            </button>
          )}

          {showBoardingPass && (
            <BoardingPass 
              itinerary={currentItinerary} 
              onClose={() => setShowBoardingPass(false)} 
            />
          )}
        </div>
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
            <RestaurantCard restaurant={selectedRestaurant} />
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

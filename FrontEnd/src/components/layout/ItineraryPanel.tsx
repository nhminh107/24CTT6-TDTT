"use client";

import { motion } from "framer-motion";
import { MapPin, Clock, DollarSign, Star, X } from "lucide-react";
import { useMemo } from "react";
import RestaurantCard from "@/components/ui/RestaurantCard";

type MealStop = {
  label: string;
  name: string;
  time: string;
  price: string;
  type: string;
  rating: number;
};

type Restaurant = {
  id: string;
  name: string;
  address: string;
  rating: number;
  price: string | number;
  phone: string | number;
  mapUrl: string;
  imageUrl: string;
  semanticText: string;
  meals?: string[];
  healthTagsDisplay?: {
    warnings?: string[];
    notes?: string[];
  };
  warnings?: string[];
  notes?: string[];
};

type ItineraryPanelProps = {
  location: string;
  budget: string;
  mealStops: MealStop[];
  restaurants: Restaurant[];
  selectedRestaurantId: string | null;
  currentTab: "itinerary" | "detail";
  onSelectRestaurant: (id: string) => void;
  onTabChange: (tab: "itinerary" | "detail") => void;
  onCloseDetail: () => void;
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
  onCloseDetail
}: ItineraryPanelProps) {
  const selectedRestaurant = useMemo(
    () => restaurants.find((r) => r.id === selectedRestaurantId) || null,
    [restaurants, selectedRestaurantId]
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
      {currentTab === "itinerary" ? (
        <>
          {/* Header */}
          <div>
            <h2 className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-flame">
              Lịch trình được đề xuất
            </h2>
          </div>

          {/* Summary Card */}
          {(location || budget) && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-2xl border border-brand-coral/20 bg-gradient-to-br from-brand-coral/5 to-brand-flame/5 p-4"
            >
              <div className="space-y-3">
                {location && (
                  <div className="flex items-start gap-2">
                    <MapPin size={14} className="mt-0.5 flex-shrink-0 text-brand-coral" />
                    <div className="min-w-0 flex-1">
                      <p className="text-[10px] font-semibold uppercase text-slate-500">
                        Vị trí
                      </p>
                      <p className="text-xs font-semibold text-slate-900 truncate">
                        {location}
                      </p>
                    </div>
                  </div>
                )}

                {budget && budget !== "Chưa nhập" && (
                  <div className="flex items-start gap-2">
                    <DollarSign size={14} className="mt-0.5 flex-shrink-0 text-brand-teal" />
                    <div className="min-w-0 flex-1">
                      <p className="text-[10px] font-semibold uppercase text-slate-500">
                        Ngân sách
                      </p>
                      <p className="text-xs font-semibold text-slate-900">
                        {budget}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Meal Stops Timeline */}
          {mealStops.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-600">
                Dừng chân
              </h3>
              <div className="space-y-2.5">
                {mealStops.map((stop, index) => (
                  <motion.button
                    key={index}
                    type="button"
                    onClick={() => {
                      const restaurant = restaurants[index];
                      if (restaurant) {
                        onSelectRestaurant(restaurant.id);
                      }
                    }}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="group w-full text-left rounded-xl border border-slate-200/60 bg-white/50 p-3 transition hover:border-slate-300 hover:bg-white"
                  >
                    {/* Stop Label */}
                    <div className="mb-2 flex items-center justify-between">
                      <span className="inline-flex items-center rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-2.5 py-0.5 text-[10px] font-bold text-white">
                        {stop.label}
                      </span>
                      <span className="text-[10px] font-semibold text-slate-500">
                        {stop.type}
                      </span>
                    </div>

                    {/* Restaurant Info */}
                    <div className="space-y-1.5">
                      <p className="text-xs font-bold text-slate-900 line-clamp-2">
                        {stop.name}
                      </p>

                      {/* Time & Price */}
                      <div className="flex items-center gap-2 text-[10px]">
                        <div className="flex items-center gap-1 text-slate-500">
                          <Clock size={12} />
                          <span>{stop.time}</span>
                        </div>
                        <div className="h-1 w-1 rounded-full bg-slate-300" />
                        <span className="font-semibold text-slate-600">
                          {stop.price}
                        </span>
                      </div>

                      {/* Rating */}
                      {stop.rating > 0 && (
                        <div className="flex items-center gap-1">
                          {[...Array(5)].map((_, i) => (
                            <Star
                              key={i}
                              size={12}
                              className={
                                i < Math.round(stop.rating)
                                  ? "fill-yellow-400 text-yellow-400"
                                  : "text-slate-300"
                              }
                            />
                          ))}
                          <span className="text-[10px] font-semibold text-slate-500">
                            {stop.rating.toFixed(1)}
                          </span>
                        </div>
                      )}
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {mealStops.length === 0 && (
            <div className="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-slate-200/60 bg-white/30 p-4 text-center">
              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-500">
                  Chưa có lịch trình
                </p>
                <p className="text-[11px] text-slate-400">
                  Bắt đầu chat để AI gợi ý cho bạn
                </p>
              </div>
            </div>
          )}
        </>
      ) : selectedRestaurant ? (
        <div className="flex-1 overflow-y-auto">
          {/* Close Button */}
          <button
            onClick={onCloseDetail}
            className="mb-4 flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-700"
          >
            <X size={14} />
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

"use client";

import React from "react";
import { X, Star, MapPin, Phone, Info, AlertTriangle } from "lucide-react";
import { Restaurant } from "@/lib/utils";

interface RestaurantDetailModalProps {
  restaurant: Restaurant | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function RestaurantDetailModal({
  restaurant,
  isOpen,
  onClose,
}: RestaurantDetailModalProps) {
  if (!isOpen || !restaurant) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-2xl">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 bg-white/80 backdrop-blur-md rounded-full text-slate-600 hover:text-rose-500 transition-colors shadow-sm"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Hero Image */}
        <div className="relative h-64 sm:h-80 w-full overflow-hidden">
          <img
            src={restaurant.imageUrl || "/assets/images/AI.png"}
            alt={restaurant.name}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          <div className="absolute bottom-6 left-6 right-6 text-white">
            <h2 className="text-3xl font-bold mb-2">{restaurant.name}</h2>
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-yellow-400 px-2 py-0.5 rounded-full text-xs font-bold text-black">
                <Star className="w-3 h-3 fill-current mr-1" />
                {restaurant.rating}
              </div>
              <span className="text-sm font-medium opacity-90">
                • {restaurant.price.toLocaleString()} VNĐ
              </span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 sm:p-8 space-y-8">
          {/* Info Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="mt-1 p-2 bg-rose-50 rounded-lg">
                  <MapPin className="w-5 h-5 text-rose-500" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Địa chỉ</h4>
                  <p className="text-slate-800 font-medium">{restaurant.address}</p>
                  <a
                    href={restaurant.mapUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-rose-500 hover:underline inline-block mt-1 font-medium"
                  >
                    Xem trên Google Maps
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="mt-1 p-2 bg-blue-50 rounded-lg">
                  <Phone className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Điện thoại</h4>
                  <p className="text-slate-800 font-medium">{restaurant.phone || "Không có số điện thoại"}</p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl space-y-3 border border-slate-100">
              <h4 className="flex items-center gap-2 text-sm font-bold text-slate-700 uppercase tracking-wider">
                <Info className="w-4 h-4" />
                Giới thiệu
              </h4>
              <p className="text-slate-600 text-sm leading-relaxed">
                {restaurant.semanticText}
              </p>
            </div>
          </div>

          {/* Health Analysis Section */}
          {(restaurant.warnings?.length > 0 || restaurant.notes?.length > 0) && (
            <div className="space-y-4 pt-6 border-t border-slate-100">
              <h3 className="text-xl font-bold text-slate-800">Phân tích sức khỏe</h3>
              
              {restaurant.warnings?.length > 0 && (
                <div className="space-y-3">
                  {restaurant.warnings.map((warning, idx) => (
                    <div
                      key={idx}
                      className="flex gap-3 p-4 bg-amber-50 rounded-xl border border-amber-100"
                    >
                      <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
                      <p className="text-amber-800 text-sm font-medium leading-relaxed">
                        {warning}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {restaurant.notes?.length > 0 && (
                <div className="space-y-3">
                  {restaurant.notes.map((note, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-slate-50 rounded-xl border border-slate-200"
                    >
                      <p className="text-slate-700 text-sm leading-relaxed italic">
                        {note}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Meals Section */}
          {Array.isArray(restaurant.meals) && restaurant.meals.length > 0 && (
            <div className="space-y-4 pt-6 border-t border-slate-100">
              <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider">Phục vụ các bữa</h4>
              <div className="flex flex-wrap gap-2">
                {restaurant.meals.map((meal, idx) => (
                  <span
                    key={idx}
                    className="px-4 py-1.5 bg-slate-100 text-slate-600 rounded-full text-sm font-bold capitalize"
                  >
                    {meal}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

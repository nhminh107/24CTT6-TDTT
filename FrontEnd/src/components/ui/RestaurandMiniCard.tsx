"use client";

import { useMemo } from "react";
import { MapPin, Star, ShieldCheck, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

type Restaurant = {
  id: string; // Thêm id để quản lý việc click chọn
  name: string;
  address: string;
  rating: number;
  price: string | number;
  phone: string | number;
  mapUrl: string;
  imageUrl: string;
  semanticText: string;
  meals?: string[];
  warnings?: string[];
  notes?: string[];
};

type RestaurantMiniCardProps = {
  restaurant: Restaurant;
  isSelected?: boolean;
  onSelect: (id: string) => void;
};

const formatPhoneNumber = (phone: string | number) => {
  if (phone === null || phone === undefined) return "";
  const raw = String(phone).trim();
  if (!raw) return "";
  if (raw.endsWith(".0")) return raw.slice(0, -2);
  return raw;
};

const normalizeImageUrl = (url: string | undefined | null) => {
  if (!url) return "";
  return url.replace(/\\\//g, "/");
};

export default function RestaurantMiniCard({
  restaurant,
  isSelected,
  onSelect,
}: RestaurantMiniCardProps) {
  const imageUrl = useMemo(
    () => normalizeImageUrl(restaurant.imageUrl),
    [restaurant.imageUrl]
  );

  const name = restaurant.name || "Chưa có tên";
  const address = restaurant.address || "Chưa có địa chỉ";
  const rating = typeof restaurant.rating === "number" ? restaurant.rating : 0;

  const warnings = restaurant.warnings ?? [];
  const severity =
    warnings.length === 0
      ? "safe"
      : warnings.length <= 2
      ? "warning"
      : "danger";

  const badgeConfig = {
    safe: {
      className: "border-green-200 bg-green-50 text-green-700",
      icon: ShieldCheck,
    },
    warning: {
      className: "border-yellow-200 bg-yellow-50 text-yellow-700",
      icon: AlertTriangle,
    },
    danger: {
      className: "border-red-200 bg-red-50 text-red-700",
      icon: AlertTriangle,
    },
  };

  const badge = badgeConfig[severity];
  const BadgeIcon = badge.icon;

  return (
    <button
      type="button"
      onClick={() => onSelect(restaurant.id)}
      className={cn(
        "group flex w-full gap-3 overflow-hidden rounded-2xl border bg-white/80 p-3 text-left backdrop-blur-md transition-all duration-300 snap-start",
        isSelected
          ? "border-orange-500 bg-orange-50/50 shadow-md ring-1 ring-orange-500"
          : "border-slate-100 hover:border-orange-300 hover:bg-orange-50/20 hover:shadow-sm"
      )}
    >
      {/* 1. ẢNH ĐẠI DIỆN THU NHỎ */}
      <div className="relative h-20 w-20 shrink-0 overflow-hidden rounded-xl bg-slate-100">
        <img
          src={imageUrl}
          alt={restaurant.name}
          className="h-full w-full object-cover transition duration-500 group-hover:scale-110"
        />
        {/* Floating Mini Badge Sức Khỏe chồng lên ảnh */}
        <div className="absolute left-1 top-1">
          <div
            className={cn(
              "flex h-5 w-5 items-center justify-center rounded-full border shadow-sm backdrop-blur-md",
              badge.className
            )}
            title={severity === "safe" ? "Phù hợp" : "Cần lưu ý sức khỏe"}
          >
            <BadgeIcon size={10} className="stroke-[3]" />
          </div>
        </div>
      </div>

      {/* 2. NỘI DUNG THÔNG TIN CHÍNH */}
      <div className="flex flex-1 flex-col justify-between min-w-0">
        <div>
          {/* Tên nhà hàng */}
          <h4 className={cn(
            "text-sm font-bold leading-tight text-slate-900 truncate transition-colors",
            isSelected ? "text-orange-600" : "group-hover:text-orange-600"
          )}>
            {name}
          </h4>

          {/* Địa chỉ rút gọn */}
          <div className="mt-1 flex items-center text-xs text-slate-500">
            <MapPin size={12} className="mr-1 shrink-0 text-slate-400" />
            <span className="truncate">{address}</span>
          </div>
        </div>

        {/* 3. THÔNG SỐ ĐÁNH GIÁ & GIÁ CẢ */}
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {/* Rating */}
          <div className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-700 border border-amber-100">
            <Star size={11} className="fill-amber-500 text-amber-500" />
            <span>{rating.toFixed(1)}</span>
          </div>

          {/* Price */}
          <div className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
            {typeof restaurant.price === "number"
              ? `${restaurant.price.toLocaleString("vi-VN")}đ`
              : restaurant.price}
          </div>

          {/* Bữa ăn phù hợp (Nếu có) */}
          {!!restaurant.meals?.length && (
            <div className="flex flex-wrap gap-1">
                {restaurant.meals.map((meal) => (
                <span
                    key={meal}
                    className="inline-flex items-center rounded-full bg-orange-50 px-2 py-0.5 text-[11px] font-medium text-orange-600 border border-orange-100/50"
                >
                    {meal}
                </span>
                ))}
            </div>
            )}
        </div>
      </div>
    </button>
  );
}
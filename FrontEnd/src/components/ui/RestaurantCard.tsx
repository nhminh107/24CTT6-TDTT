"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { MapPin, Phone, Star, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { AlertCircle } from "lucide-react";
import {
  AlertTriangle,
  ShieldCheck,
  Info,
} from "lucide-react";

type Restaurant = {
  name: string;
  address: string;
  rating: number;
  price: string | number;
  phone: string | number;
  mapUrl: string;
  imageUrl: string;
  semanticText: string;
  meals?: string[];
  assignedMeal?: string;
  warnings?: string[];
  notes?: string[];
};

type RestaurantCardProps = {
  restaurant: Restaurant;
};

const formatPhoneNumber = (phone: string | number) => {
  if (phone === null || phone === undefined) {
    return "";
  }
  const raw = String(phone).trim();
  if (!raw) {
    return "";
  }
  if (raw.endsWith(".0")) {
    return raw.slice(0, -2);
  }
  return raw;
};



const normalizeImageUrl = (url: string | undefined | null) => {
  if (!url) return "";
  return url.replace(/\\\//g, "/");
};


export default function RestaurantCard2({
  restaurant,
}: RestaurantCardProps) {
  const [open, setOpen] = useState(false);

  const phone = useMemo(
    () => formatPhoneNumber(restaurant.phone),
    [restaurant.phone]
  );

  const phoneLink = useMemo(
    () => phone.replace(/[^\d+]/g, ""),
    [phone]
  );

  const imageUrl = useMemo(
    () => normalizeImageUrl(restaurant.imageUrl),
    [restaurant.imageUrl]
  );

  const name = restaurant.name || "Chưa có tên";
  const address = restaurant.address || "Chưa có địa chỉ";
<<<<<<< HEAD
  const rating = typeof restaurant.rating === "number" ? restaurant.rating : 0;
  const semanticText = restaurant.semanticText || "";
=======
  
  const rating = useMemo(() => {
    const r = restaurant.rating !== undefined ? restaurant.rating : (restaurant as any).star;
    return typeof r === "number" ? r : Number(r) || 0;
  }, [restaurant.rating, (restaurant as any).star]);

  const price = useMemo(() => {
    return restaurant.price !== undefined ? restaurant.price : (restaurant as any).avg_price;
  }, [restaurant.price, (restaurant as any).avg_price]);

  const semanticText = restaurant.semanticText || (restaurant as any).semantic_text || "";
>>>>>>> 1ea4ce362ae7331d10cb92d299b0c231d8033e14
  const mapUrl = restaurant.mapUrl || "https://www.google.com/maps";
    
  const [isOpenWarnings, setIsOpenWarnings] = useState(true);

  const warnings = restaurant.warnings ?? [];
  const notes = restaurant.notes ?? [];

  const severity =
    warnings.length === 0
      ? "safe"
      : warnings.length <= 2
      ? "warning"
      : "danger";

  const badgeConfig = {
  safe: {
    label: "Phù hợp",
    className:
      "border-green-200 bg-green-100 text-green-800 shadow-sm",
    icon: ShieldCheck,
  },

  warning: {
    label: "Cần lưu ý",
    className:
      "border-yellow-200 bg-yellow-100 text-yellow-800 shadow-sm",
    icon: AlertTriangle,
  },

  danger: {
    label: "Rủi ro cao",
    className:
      "border-red-200 bg-red-100 text-red-800 shadow-sm",
    icon: AlertTriangle,
    },
  };

  const badge = badgeConfig[severity];
  const BadgeIcon = badge.icon;

  return (
  <div className="group overflow-hidden rounded-[36px] border border-white/20 bg-white/70 shadow-[0_20px_60px_rgba(15,23,42,0.12)] backdrop-blur-xl transition-all duration-500 hover:-translate-y-2 hover:shadow-[0_30px_80px_rgba(15,23,42,0.18)]">
    
    {/* HERO */}
    <div className="relative h-[360px] overflow-hidden">
      <img
        src={imageUrl}
        alt={restaurant.name}
        className="h-full w-full object-cover transition duration-700 group-hover:scale-110"
      />

      {/* cinematic overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

      {/* floating badge */}
      {/* floating badge */}
      <div className="absolute left-5 top-5">
        <div
          className={cn(
            "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-semibold backdrop-blur-xl",
            badge.className
          )}
        >
          <BadgeIcon size={14} />
          {badge.label}
        </div>
      </div>

      {/* content on image */}
          
      <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
        <h2 className="text-3xl font-bold tracking-tight drop-shadow-md">
          {name}
        </h2>

        {/* unified badges */}
        <div className="mt-4 flex flex-wrap items-center gap-3">
          {/* rating */}
          <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white backdrop-blur-md shadow-lg">
            <Star
              size={15}
              className="fill-yellow-400 text-yellow-400"
            />
            <span>{rating.toFixed(1)}</span>
          </div>

          {/* price */}
          <div className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white backdrop-blur-md shadow-lg">
            {typeof price === "number"
              ? `${price.toLocaleString("vi-VN")}đ`
              : price || "Chưa cập nhật"}
          </div>

          {/* meal time */}
          {restaurant.meals && restaurant.meals.length > 0 && (
            <div className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white backdrop-blur-md shadow-lg">
              {restaurant.meals.join(" • ")}
            </div>
          )}
        </div>

        {/* location */}
        <div className="mt-5 flex items-start text-sm text-white/85">
          <MapPin
            size={17}
            className="mt-[2px] mr-3 shrink-0 text-orange-300"
          />

          <span className="leading-6">
            {address}
          </span>
        </div>
      </div>
    </div>
    {/* BODY */}
    <div className="space-y-5 p-6 pb-10">
      {/* AI Insight */}
      <div className="rounded-[28px] border border-white/40 bg-gradient-to-br from-slate-50 to-white p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-3">
        {/* logo giống mẫu */}
        <div className="relative flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-orange-500 via-orange-400 to-amber-500 shadow-[0_6px_20px_rgba(249,115,22,0.35)]">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-orange-100 text-orange-700 shadow-inner">
            <span className="text-sm font-black leading-none">
              ✦
            </span>
          </div>
        </div>

        <span className="text-[17px] font-semibold tracking-tight text-slate-900">
          AI Health Insight
        </span>
      </div>

    {warnings.length > 0 ? (
      <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
        {/* Nút bấm tiêu đề để ẩn/hiện */}
        <button
          type="button"
          onClick={() => setIsOpenWarnings(!isOpenWarnings)}
          className="flex w-full items-center justify-between rounded-xl bg-amber-100/60 px-3.5 py-2.5 text-left transition-all duration-200 hover:bg-amber-100 outline-none group"
        >
          {/* Bên trái: Tiêu đề bôi đậm, nổi bật hẳn lên */}
          <div className="flex items-center gap-2">
            <AlertCircle size={18} className="text-amber-600 animate-pulse" />
            <span className="text-sm font-bold tracking-wide text-amber-900">
              Cần lưu ý
            </span>
            {/* Badge số lượng hình tròn nhỏ nhìn cực kỳ chuyên nghiệp */}
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-amber-600 text-[11px] font-bold text-white shadow-sm">
              {warnings.length}
            </span>
          </div>

          {/* Bên phải: Nút hành động kèm Icon xoay mượt mà */}
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-700 group-hover:text-amber-900">
            <span>{isOpenWarnings ? "Thu gọn" : "Xem hết"}</span>
            <ChevronDown
              size={15}
              className={`transition-transform duration-300 ${
                isOpenWarnings ? "rotate-180 text-amber-600" : "text-amber-500"
              }`}
            />
          </div>
        </button>

        {/* Nếu isOpenWarnings là true thì mới render danh sách bên dưới */}
        {isOpenWarnings && (
          <ul className="list-disc list-inside space-y-1.5 text-sm leading-6 text-amber-900">
            {warnings.map((warning, index) => {
              // 1. Kiểm tra xem trong câu có dấu ":" không
              if (warning.includes(":")) {
                // Tách câu thành 2 phần: trước và sau dấu ":"
                const indexFirstColon = warning.indexOf(":");
                const title = warning.substring(0, indexFirstColon);
                const description = warning.substring(indexFirstColon + 1);

                return (
                  <li key={index} className="marker:text-amber-500">
                    {/* Phần trước dấu ":" - Bôi đậm màu nâu đen cho nổi bật */}
                    <strong className="font-bold text-slate-900">{title}:</strong>
                    {/* Phần sau dấu ":" - Giữ nguyên chữ thường */}
                    <span className="text-amber-900">{description}</span>
                  </li>
                );
              }

              // 2. Dự phòng trường hợp câu không có dấu ":" thì hiển thị bình thường
              return (
                <li key={index} className="marker:text-amber-500">
                  {warning}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    ) : (
      <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
        <p className="text-sm leading-6 text-emerald-800">
          <span className="font-semibold">
            Hệ thống đánh giá nhà hàng này phù hợp với sức khỏe của bạn:
          </span>{" "}
          Không có cảnh báo nào được đưa ra.
        </p>
      </div>
    )}

        {/* semantic text */}
        <div className="mt-4 rounded-xl bg-amber-50/50 p-4 border-l-4 border-amber-500">
          <div className="mb-1 flex items-center gap-1.5 text-xs font-bold text-amber-700">
            <span>📖</span> Không gian & Hương vị
          </div>
          <p className="text-[14px] font-normal leading-relaxed text-slate-600">
            {semanticText}
          </p>
        </div>
      </div>

      {/* actions */}
      {/* Thay grid thành flex */}
      <div className="flex w-full gap-3">
        {phoneLink && (
          <Link
            href={`tel:${phoneLink}`}
            className="inline-flex w-1/2 items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-orange-500 to-amber-500 py-3.5 text-center text-sm font-semibold text-white shadow-md shadow-orange-200 transition duration-300 hover:scale-[1.02]"
          >
            <Phone size={16} />
            Gọi ngay
          </Link>
        )}

        <Link
          href={mapUrl}
          target="_blank"
          className={cn(
            "inline-flex items-center justify-center gap-2 rounded-2xl border py-3.5 text-center text-sm font-semibold transition duration-300",
            phoneLink
              ? "w-1/2 border-blue-200 bg-gradient-to-r from-blue-50 to-sky-50 text-blue-700"
              : "w-full bg-white border border-slate-200 text-slate-700 shadow-sm hover:bg-slate-50"
          )}
        >
          <MapPin size={16} className="text-red-500" />
          Chỉ đường
        </Link>
      </div>
    </div>

    {/* accordion */}
    <button
      onClick={() => setOpen(!open)}
      className="flex w-full items-center justify-between border-t border-orange-200 bg-orange-50 px-6 py-5 text-sm font-semibold text-orange-700 transition hover:bg-orange-100"
    >
      Xem thêm health insight

      <ChevronDown
        size={18}
        className={cn(
          "transition-transform duration-300",
          open && "rotate-180"
        )}
      />
    </button>

    {open && (
    <div className="space-y-5 bg-slate-50 px-6 pb-24 pt-5">
      {notes.length > 0 && (
        <div className="rounded-[28px] border border-emerald-100 bg-gradient-to-br from-emerald-50 via-white to-emerald-50/60 p-5 shadow-sm">
          {/* header */}
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-green-500 shadow-md shadow-emerald-200">
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                ✓
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-slate-900">
                Các lưu ý dành cho bạn
              </h4>

              <p className="text-xs text-slate-500">
                Một vài gợi ý sức khỏe giúp bạn
                lựa chọn món ăn phù hợp hơn
              </p>
            </div>
          </div>

          {/* notes */}
          <div className="space-y-3">
            {notes.map((note, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-2xl border border-emerald-100 bg-white/80 p-4 shadow-sm transition hover:shadow-md"
              >
                <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700">
                  {i + 1}
                </div>

                <p className="text-sm leading-6 text-slate-700">
                  {note}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )}
  </div>
);  
}
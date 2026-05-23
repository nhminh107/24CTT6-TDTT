"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { MapPin, Phone, Star, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

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

const normalizeImageUrl = (url: string) => url.replace(/\\\//g, "/");

// export default function RestaurantCard({ restaurant }: RestaurantCardProps) {
//   const [open, setOpen] = useState(false);
//   const phone = useMemo(() => formatPhoneNumber(restaurant.phone), [restaurant.phone]);
//   const phoneLink = useMemo(
//     () => phone.replace(/[^\d+]/g, ""),
//     [phone]
//   );
//   const imageUrl = useMemo(
//     () => normalizeImageUrl(restaurant.imageUrl),
//     [restaurant.imageUrl]
//   );

//   console.log(restaurant);

//   return (
//     <div className="glass overflow-hidden rounded-3xl shadow-soft">
//       <div className="grid gap-4 p-4 md:grid-cols-[1fr_2fr]">
//         <div className="overflow-hidden rounded-2xl">
//           <img
//             src={imageUrl}
//             alt={restaurant.name}
//             className="h-40 w-full object-cover"
//           />
//         </div>
//         <div className="flex flex-col justify-between gap-4">
//           <div className="space-y-2">
//             <h3 className="font-display text-xl font-semibold text-slate-900">
//               {restaurant.name}
//             </h3>
//             <div className="flex items-center gap-2 text-sm text-slate-600">
//               <MapPin size={16} className="text-brand-coral" />
//               <span>{restaurant.address}</span>
//             </div>
//             <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
//               <div className="inline-flex items-center gap-1">
//                 <Star size={16} className="text-amber-500" />
//                 <span>{restaurant.rating.toFixed(1)}</span>
//               </div>
//               <div className="rounded-full border border-slate-200/60 bg-white/70 px-3 py-1 text-xs font-semibold text-slate-700">
//                 {typeof restaurant.price === "number"
//                   ? `${restaurant.price.toLocaleString("vi-VN")}đ`
//                   : restaurant.price}
//               </div>
//             </div>
//           </div>

//           <div className="flex flex-wrap items-center gap-3 text-sm">
//             {phoneLink ? (
//               <Link
//                 href={`tel:${phoneLink}`}
//                 className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-4 py-2 text-xs font-semibold text-white shadow-glow"
//               >
//                 <Phone size={14} />
//                 Gọi điện
//               </Link>
//             ) : null}
//             <Link
//               href={restaurant.mapUrl}
//               target="_blank"
//               rel="noreferrer"
//               className="text-xs font-semibold text-brand-lagoon transition hover:text-brand-teal"
//             >
//               Xem trên Google Maps
//             </Link>
//           </div>
//         </div>
//       </div>

//       <button
//         type="button"
//         onClick={() => setOpen((value) => !value)}
//         className="flex w-full items-center justify-between border-t border-white/70 px-5 py-4 text-sm font-semibold text-slate-700"
//       >
//         Món ăn & Mô tả
//         <ChevronDown
//           size={18}
//           className={cn("transition", open && "rotate-180")}
//         />
//       </button>
//       {open && (
//   <div className="space-y-4 px-5 pb-5 text-sm text-slate-600">
//     <div>{restaurant.semanticText}</div>

//     {restaurant.meals && restaurant.meals.length > 0 && (
//       <div>
//         <span className="font-medium text-slate-800">
//           Phục vụ:
//         </span>{" "}
//         {restaurant.meals.join(", ")}
//       </div>
//     )}

//     {/* Warnings */}
//     {restaurant.warnings &&
//       restaurant.warnings.length > 0 && (
//         <div className="space-y-2">
//           <h4 className="font-semibold text-red-600">
//             Cảnh báo sức khỏe
//           </h4>

//           <div className="flex flex-wrap gap-2">
//             {restaurant.warnings.map(
//               (warning, index) => (
//                 <span
//                   key={`${warning}-${index}`}
//                   className="rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-700"
//                 >
//                   {warning}
//                 </span>
//               )
//             )}
//           </div>
//         </div>
//       )}

//     {/* Notes */}
//     {restaurant.notes &&
//       restaurant.notes.length > 0 && (
//         <div className="space-y-2">
//           <h4 className="font-semibold text-emerald-600">
//             Gợi ý / Lưu ý
//           </h4>

//           <div className="flex flex-wrap gap-2">
//             {restaurant.notes.map((note, index) => (
//               <span
//                 key={`${note}-${index}`}
//                 className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700"
//               >
//                 {note}
//               </span>
//             ))}
//           </div>
//         </div>
//       )}
//   </div>
// )}
//     </div>
//   );
// }




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
          {restaurant.name}
        </h2>

        {/* unified badges */}
        <div className="mt-4 flex flex-wrap items-center gap-3">
          {/* rating */}
          <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white backdrop-blur-md shadow-lg">
            <Star
              size={15}
              className="fill-yellow-400 text-yellow-400"
            />
            <span>{restaurant.rating.toFixed(1)}</span>
          </div>

          {/* price */}
          <div className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white backdrop-blur-md shadow-lg">
            {typeof restaurant.price === "number"
              ? `${restaurant.price.toLocaleString(
                  "vi-VN"
                )}đ`
              : restaurant.price}
          </div>

          {/* meal time */}
          {!!restaurant.meals?.length && (
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
            {restaurant.address}
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

        {warnings.length ? (
          <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
            <div className="text-xs font-semibold tracking-wide text-amber-700">
              Cần lưu ý
            </div>

            <p className="mt-2 text-sm leading-6 text-amber-900">
              {warnings[0]}
            </p>
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
            {restaurant.semanticText}
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
          href={restaurant.mapUrl}
          target="_blank"
          className={cn(
            "inline-flex items-center justify-center gap-2 rounded-2xl border py-3.5 text-center text-sm font-semibold transition duration-300",
            phoneLink
              ? "w-1/2 border-blue-200 bg-gradient-to-r from-blue-50 to-sky-50 text-blue-700"
              : "w-full border-slate-200 bg-white text-slate-900"
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
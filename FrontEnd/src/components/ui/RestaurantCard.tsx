"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { MapPin, Phone, Star, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

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

export default function RestaurantCard({ restaurant }: RestaurantCardProps) {
  const [open, setOpen] = useState(false);
  const phone = useMemo(() => formatPhoneNumber(restaurant.phone), [restaurant.phone]);
  const phoneLink = useMemo(
    () => phone.replace(/[^\d+]/g, ""),
    [phone]
  );
  const imageUrl = useMemo(
    () => normalizeImageUrl(restaurant.imageUrl),
    [restaurant.imageUrl]
  );

  return (
    <div className="glass overflow-hidden rounded-3xl shadow-soft">
      <div className="grid gap-4 p-4 md:grid-cols-[1fr_2fr]">
        <div className="overflow-hidden rounded-2xl">
          <img
            src={imageUrl}
            alt={restaurant.name}
            className="h-full w-full object-cover"
          />
        </div>
        <div className="flex flex-col justify-between gap-4">
          <div className="space-y-2">
            <h3 className="font-display text-xl font-semibold text-slate-900">
              {restaurant.name}
            </h3>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <MapPin size={16} className="text-brand-coral" />
              <span>{restaurant.address}</span>
            </div>
            <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600">
              <div className="inline-flex items-center gap-1">
                <Star size={16} className="text-amber-500" />
                <span>{restaurant.rating.toFixed(1)}</span>
              </div>
              <div className="rounded-full border border-slate-200/60 bg-white/70 px-3 py-1 text-xs font-semibold text-slate-700">
                {typeof restaurant.price === "number"
                  ? `${restaurant.price.toLocaleString("vi-VN")}đ`
                  : restaurant.price}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm">
            {phoneLink ? (
              <Link
                href={`tel:${phoneLink}`}
                className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-4 py-2 text-xs font-semibold text-white shadow-glow"
              >
                <Phone size={14} />
                Gọi điện
              </Link>
            ) : null}
            <Link
              href={restaurant.mapUrl}
              className="text-xs font-semibold text-brand-lagoon transition hover:text-brand-teal"
            >
              Xem trên Google Maps
            </Link>
          </div>
        </div>
      </div>

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between border-t border-white/70 px-5 py-4 text-sm font-semibold text-slate-700"
      >
        Món ăn & Mô tả
        <ChevronDown
          size={18}
          className={cn("transition", open && "rotate-180")}
        />
      </button>
      {open && (
        <div className="space-y-3 px-5 pb-5 text-sm text-slate-600">
          <div>{restaurant.semanticText}</div>
          {restaurant.meals && restaurant.meals.length > 0 && (
            <div>
              Phục vụ: {restaurant.meals.join(", ")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

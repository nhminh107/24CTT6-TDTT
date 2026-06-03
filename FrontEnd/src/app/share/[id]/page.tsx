"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { MapPin, Star, Calendar, ArrowLeft, Utensils, Compass } from "lucide-react";
import { itineraryApi } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function SharedItineraryPage() {
  const { id } = useParams();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSharedData = async () => {
      if (!id) return;
      try {
        const res = await itineraryApi.getPublic(id as string);
        if (res.status === "success") {
          setData(res.data);
        } else {
          setError("Không tìm thấy lộ trình này.");
        }
      } catch (err) {
        setError("Đã có lỗi xảy ra khi tải dữ liệu.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchSharedData();
  }, [id]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-brand-coral border-t-transparent"></div>
        <p className="mt-4 text-sm font-medium text-slate-500">Đang tải lộ trình ẩm thực...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center">
        <div className="rounded-full bg-rose-50 p-6 text-rose-500">
          <Compass size={48} />
        </div>
        <h1 className="mt-6 text-2xl font-bold text-slate-900">Oops! Không tìm thấy lộ trình</h1>
        <p className="mt-2 text-slate-500">{error || "Đường dẫn không hợp lệ hoặc đã hết hạn."}</p>
        <button
          onClick={() => router.push("/")}
          className="mt-8 rounded-2xl bg-brand-coral px-8 py-3 font-bold text-white shadow-glow transition hover:opacity-90"
        >
          Về trang chủ BMI
        </button>
      </div>
    );
  }

  const itinerary = data.itinerary || [];
  const totalBudget = itinerary.reduce((sum: number, item: any) => sum + (item.avg_price || 0), 0);

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-white/20 bg-white/70 px-4 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-2xl items-center justify-between">
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-2 text-sm font-bold text-slate-600 transition hover:text-brand-coral"
          >
            <ArrowLeft size={18} />
            <span>Trang chủ BMI</span>
          </button>
          <div className="flex flex-col items-end">
            <span className="text-xs font-bold uppercase tracking-widest text-brand-flame">Shared Pass</span>
            <span className="text-[10px] text-slate-400">ID: {id?.toString().substring(0, 8).toUpperCase()}</span>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-2xl px-4 pt-8">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-[32px] bg-[#0B3C5D] p-8 text-white shadow-2xl">
          <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-[#C5A059]/10 blur-3xl"></div>
          <div className="relative">
            <div className="flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-[#C5A059] backdrop-blur-md">
                <Utensils size={24} />
              </span>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Lộ trình ẩm thực của bạn</h1>
                <p className="text-sm text-[#C5A059]/80">Tối ưu bởi trợ lý AI thông minh BMI</p>
              </div>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-4 border-t border-white/10 pt-6">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-[#C5A059]/60">Tổng ngân sách</p>
                <p className="mt-1 text-xl font-bold">{totalBudget.toLocaleString("vi-VN")} VNĐ</p>
              </div>
              <div className="text-right">
                <p className="text-[10px] font-bold uppercase tracking-widest text-[#C5A059]/60">Ngày tạo</p>
                <p className="mt-1 text-sm font-bold">
                  {new Date(data.created_at).toLocaleDateString("vi-VN")}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Itinerary List */}
        <div className="mt-10 space-y-6">
          <h2 className="flex items-center gap-2 text-lg font-bold text-slate-800">
            <Calendar size={20} className="text-brand-coral" />
            <span>Chi tiết lộ trình</span>
          </h2>

          <div className="space-y-4">
            {itinerary.map((stop: any, index: number) => (
              <div
                key={index}
                className="group relative flex gap-4 rounded-3xl border border-white bg-white/80 p-4 shadow-sm transition-all hover:shadow-md"
              >
                {/* Time Indicator */}
                <div className="flex w-16 shrink-0 flex-col items-center justify-center rounded-2xl bg-slate-50 font-bold text-slate-400 transition-colors group-hover:bg-brand-coral group-hover:text-white">
                  <span className="text-[10px] uppercase tracking-tighter">{stop.meal}</span>
                </div>

                {/* Content */}
                <div className="min-w-0 flex-1">
                  <h3 className="text-base font-bold text-slate-900 truncate">{stop.name}</h3>
                  <div className="mt-1 flex items-center text-xs text-slate-500">
                    <MapPin size={12} className="mr-1 text-slate-400" />
                    <span className="truncate">{stop.address}</span>
                  </div>
                  <div className="mt-3 flex items-center gap-3">
                    <div className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-700">
                      <Star size={12} className="fill-amber-500 text-amber-500" />
                      <span>{stop.star}</span>
                    </div>
                    <span className="text-[11px] font-bold text-brand-teal">
                      {stop.avg_price?.toLocaleString("vi-VN")}đ
                    </span>
                  </div>
                </div>

                {/* Image (Mini) */}
                {stop.image_url && (
                  <div className="h-20 w-20 shrink-0 overflow-hidden rounded-2xl bg-slate-100">
                    <img
                      src={stop.image_url.replace(/\\\//g, "/")}
                      alt={stop.name}
                      className="h-full w-full object-cover"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-12 rounded-[32px] border border-dashed border-slate-300 p-8 text-center">
          <p className="text-sm font-medium text-slate-500">
            Bạn cũng muốn có một lộ trình ẩm thực tuyệt vời như thế này?
          </p>
          <button
            onClick={() => router.push("/")}
            className="mt-4 inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-brand-coral to-brand-flame px-6 py-3 font-bold text-white shadow-glow transition hover:scale-105"
          >
            <Compass size={18} />
            Thử ngay BMI Smart App
          </button>
        </div>
      </div>
    </div>
  );
}

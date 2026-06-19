"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Sparkles } from "lucide-react";

import { useAuth } from "@/context/AuthContext";

export default function Hero() {
  const { user } = useAuth();
  
  return (
    <section className="section-spacing !pb-10 !pt-8 lg:!pt-10" id="about">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:gap-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          viewport={{ once: true, amount: 0.4 }}
          className="space-y-5 lg:space-y-6"
        >
          <motion.div
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="inline-flex items-center gap-2 rounded-2xl border border-brand-coral/20 bg-white px-3.5 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-brand-flame shadow-sm sm:text-xs lg:rounded-full lg:bg-white/70 lg:px-4 lg:tracking-[0.2em] lg:shadow-soft"
          >
            <Sparkles size={14} />
            AI hành trình ẩm thực
          </motion.div>
          <h1 className="font-display text-3xl font-semibold leading-tight text-slate-950 sm:text-4xl md:text-5xl">
            Khám phá lộ trình ẩm thực
            <span className="text-gradient"> tối ưu</span> bằng
            <span className="text-gradient"> AI</span>
          </h1>
          <p className="max-w-xl text-base leading-relaxed text-slate-600 md:text-lg">
            Không cần đau đầu suy nghĩ "Hôm nay ăn gì?". Nhập sở thích,
            ngân sách và vị trí của bạn. Trí tuệ nhân tạo sẽ phân tích hàng
            ngàn địa điểm để vẽ ra luồng di chuyển hoàn hảo cho các bữa ăn
            trong ngày.
          </p>
          <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:gap-4">
            <Link
              href="/app"
              className="inline-flex min-h-12 items-center justify-center rounded-2xl bg-gradient-to-r from-brand-coral to-brand-flame px-5 py-3 text-center text-sm font-semibold text-white shadow-[0_14px_30px_rgba(255,106,61,0.24)] transition hover:-translate-y-0.5 sm:w-auto lg:rounded-full lg:px-6 lg:shadow-glow"
            >
              Bắt đầu lên lịch trình - Miễn phí
            </Link>
            <div className="text-center text-sm text-slate-500 sm:text-left">
              Gợi ý hơn 1.200 tuyến ăn uống mỗi ngày
            </div>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, ease: "easeOut" }}
          viewport={{ once: true, amount: 0.4 }}
          className="relative"
        >
          <div className="glass relative overflow-hidden rounded-2xl p-4 shadow-sm lg:rounded-3xl lg:p-6 lg:shadow-soft">
            <div className="absolute inset-0 hidden bg-tech-glow opacity-70 lg:block" />
            <div className="relative space-y-3 lg:space-y-4">
              <div className="rounded-2xl bg-white p-4 shadow-sm lg:bg-white/90 lg:shadow">
                <div className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                  Lộ trình hôm nay
                </div>
                <div className="mt-2 text-lg font-semibold text-slate-900">
                  Ẩm thực ven biển - Đà Nẵng
                </div>
                <div className="mt-3 grid gap-3 text-sm text-slate-600">
                  <div className="flex items-center justify-between">
                    <span>07:30 - Brunch Hải sản</span>
                    <span className="text-brand-coral">2.3 km</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>12:45 - Cà phê view biển</span>
                    <span className="text-brand-coral">1.1 km</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>19:00 - Fine Dining</span>
                    <span className="text-brand-coral">3.8 km</span>
                  </div>
                </div>
              </div>
              <div className="rounded-2xl border border-slate-200/70 bg-slate-50 p-4 text-sm text-slate-600 lg:border-white/60 lg:bg-white/50">
                AI đang cân bằng khoảng cách &amp; ngân sách tối ưu.
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Sparkles } from "lucide-react";

import { useAuth } from "@/context/AuthContext";

export default function Hero() {
  const { user } = useAuth();
  
  return (
    <section className="section-spacing !pb-10" id="about">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          viewport={{ once: true, amount: 0.4 }}
          className="space-y-6"
        >
          <motion.div
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="inline-flex items-center gap-2 rounded-full border border-brand-coral/30 bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-flame shadow-soft"
          >
            <Sparkles size={14} />
            AI hành trình ẩm thực
          </motion.div>
          <h1 className="font-display text-4xl font-semibold leading-tight text-slate-900 md:text-5xl">
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
          <div className="flex flex-wrap items-center gap-4">
            <Link
              href={user ? "/app" : "/login?redirect=/app"}
              className="rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-6 py-3 text-sm font-semibold text-white shadow-glow transition hover:-translate-y-0.5"
            >
              Bắt đầu lên lịch trình - Miễn phí
            </Link>
            <div className="text-sm text-slate-500">
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
          <div className="glass relative overflow-hidden rounded-3xl p-6 shadow-soft">
            <div className="absolute inset-0 bg-tech-glow opacity-70" />
            <div className="relative space-y-4">
              <div className="rounded-2xl bg-white/90 p-4 shadow">
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
              <div className="rounded-2xl border border-white/60 bg-white/50 p-4 text-sm text-slate-600">
                AI đang cân bằng khoảng cách &amp; ngân sách tối ưu.
              </div>
            </div>
          </div>
          <div className="absolute -bottom-6 -left-6 h-24 w-24 rounded-full bg-brand-teal/20 blur-2xl" />
          <div className="absolute -top-6 -right-4 h-32 w-32 rounded-full bg-brand-coral/30 blur-2xl" />
        </motion.div>
      </div>
    </section>
  );
}

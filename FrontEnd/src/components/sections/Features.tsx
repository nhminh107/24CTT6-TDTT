"use client";

import { motion } from "framer-motion";
import { Brain, Route, Map } from "lucide-react";

const features = [
  {
    title: "AI Hiểu Ngôn Ngữ",
    description:
      "\"Thèm một quán lãng mạn view biển?\" Hệ thống hiểu chính xác nhu cầu bằng ngôn ngữ tự nhiên.",
    icon: Brain
  },
  {
    title: "Thuật toán Đa Tiêu Chí",
    description:
      "Chấm điểm và cân bằng giữa giá cả, độ ngon và khoảng cách di chuyển.",
    icon: Route
  },
  {
    title: "Bản Đồ Trực Quan",
    description:
      "Tích hợp hệ thống bản đồ thông minh, xem trước tuyến đường thực tế.",
    icon: Map
  }
];

export default function Features() {
  return (
    <section className="section-spacing" id="features">
      <div className="mx-auto w-full max-w-6xl space-y-10">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          viewport={{ once: true, amount: 0.3 }}
          className="max-w-2xl space-y-3"
        >
          <div className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-lagoon">
            Tính năng nổi bật
          </div>
          <h2 className="font-display text-3xl font-semibold text-slate-900 md:text-4xl">
            Điều khiển mọi hành trình bằng dữ liệu.
          </h2>
        </motion.div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true, amount: 0.2 }}
                className="glass group rounded-3xl p-6 shadow-soft transition hover:-translate-y-2 hover:shadow-glow"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-teal to-brand-lagoon text-white">
                  <Icon size={22} />
                </div>
                <h3 className="mt-6 font-display text-xl font-semibold text-slate-900">
                  {feature.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

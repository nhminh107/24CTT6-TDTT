"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, Home } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const members = [
  {
    name: "Ngọc Anh",
    role: "Product & UX",
    image:
      "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=1200&q=80",
    bio: "Thiết kế trải nghiệm mạch lạc, chuyển hóa dữ liệu thành hành trình trực quan cho người dùng."
  },
  {
    name: "Minh Quân",
    role: "AI Engineer",
    image:
      "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=1200&q=80",
    bio: "Tối ưu mô hình gợi ý, đảm bảo hiểu prompt và đề xuất lộ trình phù hợp ngân sách."
  },
  {
    name: "Thanh Huy",
    role: "Full-stack",
    image:
      "https://images.unsplash.com/photo-1525134479668-1bee5c7c6845?auto=format&fit=crop&w=1200&q=80",
    bio: "Kết nối dữ liệu bản đồ và API, đảm bảo trải nghiệm realtime mượt mà."
  }
];

export default function AboutPage() {
  const [index, setIndex] = useState(0);
  const current = members[index];
  const total = members.length;

  const slideKey = useMemo(() => `${current.name}-${index}`, [current.name, index]);

  return (
    <div className="min-h-screen bg-white/70">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-10">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-lagoon">
              Về chúng tôi
            </div>
            <h1 className="font-display text-3xl font-semibold text-slate-900 md:text-4xl">
              Đội ngũ đứng sau BMI
            </h1>
            <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
              Bite Mapping Intelligent
            </div>
          </div>
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-full border border-slate-200/60 bg-white/80 px-4 py-2 text-xs font-semibold text-slate-600 shadow-soft transition hover:text-slate-900"
          >
            <Home size={14} />
            Home
          </Link>
        </div>

        <div className="glass relative overflow-hidden rounded-3xl p-6 shadow-soft">
          <AnimatePresence mode="wait">
            <motion.div
              key={slideKey}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -40 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]"
            >
              <div className="relative overflow-hidden rounded-3xl">
                <img
                  src={current.image}
                  alt={current.name}
                  className="h-[360px] w-full object-cover md:h-[420px]"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/40 via-transparent to-transparent" />
              </div>
              <div className="flex flex-col justify-center gap-4">
                <div className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-flame">
                  {current.role}
                </div>
                <h2 className="font-display text-3xl font-semibold text-slate-900">
                  {current.name}
                </h2>
                <p className="text-sm leading-relaxed text-slate-600 md:text-base">
                  {current.bio}
                </p>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span>
                    {index + 1} / {total}
                  </span>
                  <div className="h-[2px] w-20 rounded-full bg-gradient-to-r from-brand-coral to-brand-flame" />
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          <div className="absolute inset-y-0 left-4 flex items-center">
            <button
              type="button"
              onClick={() => setIndex((prev) => (prev - 1 + total) % total)}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-white/80 text-slate-600 shadow-soft transition hover:text-slate-900"
            >
              <ChevronLeft size={18} />
            </button>
          </div>
          <div className="absolute inset-y-0 right-4 flex items-center">
            <button
              type="button"
              onClick={() => setIndex((prev) => (prev + 1) % total)}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-white/80 text-slate-600 shadow-soft transition hover:text-slate-900"
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {members.map((member, idx) => (
            <button
              key={member.name}
              type="button"
              onClick={() => setIndex(idx)}
              className={`glass rounded-2xl px-4 py-3 text-left text-sm shadow-soft transition ${
                idx === index
                  ? "border border-brand-coral/50"
                  : "border border-white/70"
              }`}
            >
              <div className="font-semibold text-slate-900">{member.name}</div>
              <div className="text-xs text-slate-500">{member.role}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

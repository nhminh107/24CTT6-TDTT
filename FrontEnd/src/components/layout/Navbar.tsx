"use client";

import Link from "next/link";
import { MapPin, LogOut, User as UserIcon } from "lucide-react";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";

const links = [
  { label: "Trang chủ", href: "/" },
  { label: "Về chúng tôi", href: "/about" },
  { label: "Tính năng", href: "/#features" },
  { label: "Hướng dẫn", href: "/guide" }
];

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <motion.nav
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="sticky top-0 z-50 w-full border-b border-slate-200/60 bg-white/70 backdrop-blur"
    >
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-coral to-brand-flame text-white shadow-glow">
            <MapPin size={20} />
          </span>
          <div className="flex flex-col leading-tight">
            <span className="font-display text-xl font-semibold tracking-tight text-slate-900">
              BMI
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-500">
              Bite Mapping Intelligent
            </span>
          </div>
        </Link>
        <div className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="transition hover:text-slate-900"
            >
              {link.label}
            </Link>
          ))}
        </div>
        
        <div className="flex items-center gap-4">
          {user ? (
            <div className="flex items-center gap-3">
              <div className="hidden flex-col items-end md:flex">
                <span className="text-xs font-semibold text-slate-900">{user.displayName || "Người dùng"}</span>
                <span className="text-[10px] text-slate-500">{user.email}</span>
              </div>
              <button
                onClick={() => logout()}
                className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 hover:text-brand-coral"
                title="Đăng xuất"
              >
                <LogOut size={18} />
              </button>
              <Link
                href="/app"
                className="rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-5 py-2 text-sm font-semibold text-white shadow-glow transition hover:-translate-y-0.5"
              >
                Vào ứng dụng
              </Link>
            </div>
          ) : (
            <Link
              href="/login?redirect=/app"
              className="rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-5 py-2 text-sm font-semibold text-white shadow-glow transition hover:-translate-y-0.5"
            >
              Dùng ngay
            </Link>
          )}
        </div>
      </div>
    </motion.nav>
  );
}

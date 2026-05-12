"use client";

import Link from "next/link";
import { MapPin } from "lucide-react";
import { motion } from "framer-motion";

const links = [
  { label: "Trang chủ", href: "/" },
  { label: "Về chúng tôi", href: "/about" },
  { label: "Tính năng", href: "/#features" },
  { label: "Hướng dẫn", href: "/guide" }
];

export default function Navbar() {
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
          <span className="font-display text-xl font-semibold tracking-tight text-slate-900">
            RouteAI
          </span>
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
        <Link
          href="/app"
          className="rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-5 py-2 text-sm font-semibold text-white shadow-glow transition hover:-translate-y-0.5"
        >
          Dùng ngay
        </Link>
      </div>
    </motion.nav>
  );
}

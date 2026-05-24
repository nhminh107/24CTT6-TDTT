"use client";

import { useState } from "react";
import Link from "next/link";
import { MapPin, LogOut, HeartPulse } from "lucide-react";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { useEffect } from "react";
import HealthProfileModal, { HealthProfile } from "@/components/ui/HealthProfileModal";

const links = [
  { label: "Trang chủ", href: "/" },
  { label: "Về chúng tôi", href: "/about" },
  { label: "Tính năng", href: "/#features" },
  { label: "Hướng dẫn", href: "/guide" },
];

// Default profile — export để dùng ở chỗ khác nếu cần
export const DEFAULT_HEALTH_PROFILE: HealthProfile = {
  selected_conditions: [],
  selected_allergies: [],
  diet_mode: "casual",
  more_descriptions: "",
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const [healthOpen, setHealthOpen] = useState(false);
  const [healthProfile, setHealthProfile] = useState<HealthProfile>(DEFAULT_HEALTH_PROFILE);

  const hasProfile =
    healthProfile.selected_conditions.length > 0 ||
    healthProfile.selected_allergies.length > 0 ||
    !!healthProfile.more_descriptions;


const fetchHealthProfile = async () => {
    if (!user?.uid) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/user/health-profile/${user.uid}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch profile");
      }

      const data = await response.json();

      setHealthProfile({
        selected_conditions:
          data.raw_selections?.selected_conditions || [],
        selected_allergies:
          data.raw_selections?.selected_allergies || [],
        diet_mode: data.diet_mode || "casual",
        more_descriptions: data.more_description || "",
      });
    } catch (error) {
      console.error(error);
    }
  };

const handleSaveHealthProfile = async (profile: HealthProfile) => {
  if (!user?.uid) return;

  try {
    // update UI trước
    setHealthProfile(profile);

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/user/health-profile/${user.uid}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: user.uid,
          diet_mode: profile.diet_mode,
          selected_conditions: profile.selected_conditions,
          selected_allergies: profile.selected_allergies,
          more_descriptions: profile.more_descriptions,
        }),
      }
    );

    if (!response.ok) {
      throw new Error("Failed to save profile");
    }

    const data = await response.json();

    console.log("Saved profile:", data);
  } catch (error) {
    console.error(error);
  }
};


  useEffect(() => {
    if (user?.uid) {
      fetchHealthProfile();
    }
  }, [user]);

  return (
    <>
      <motion.nav
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="sticky top-0 z-50 w-full border-b border-slate-200/60 bg-white/70 backdrop-blur"
      >
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          {/* Logo */}
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

          {/* Nav links */}
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

          {/* Right side */}
          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3">
                {/* User info */}
                <div className="hidden flex-col items-end md:flex">
                  <span className="text-xs font-semibold text-slate-900">
                    {user.displayName || "Người dùng"}
                  </span>
                  <span className="text-[10px] text-slate-500">{user.email}</span>
                </div>

                {/* Health profile button */}
                <button
                  type="button"
                  onClick={() => setHealthOpen(true)}
                  title="Hồ sơ sức khỏe"
                  className="relative flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:bg-orange-50 hover:border-orange-300 hover:text-orange-500"
                >
                  <HeartPulse size={18} />
                  {/* dot indicator nếu đã có profile */}
                  {hasProfile && (
                    <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-orange-500" />
                  )}
                </button>

                {/* Logout */}
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

      {/* Health Profile Modal */}
      <HealthProfileModal
        open={healthOpen}
        onClose={() => setHealthOpen(false)}
        profile={healthProfile}
        onChange={handleSaveHealthProfile}
      />
    </>
  );
}



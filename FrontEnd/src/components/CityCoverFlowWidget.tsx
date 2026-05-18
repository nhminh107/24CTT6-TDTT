"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import dalat from "@/assets/images/DaLat.png";
import hanoi from "@/assets/images/HaNoi.png";
import hcm from "@/assets/images/HoChiMinh.png";
import danang from "@/assets/images/DaNang.png";
import vungtau from "@/assets/images/VungTau.png";

const cities = [
  {
    id: "dalat",
    name: "Đà Lạt",
    subtitle: "Cao nguyên mờ sương",
    image: dalat,
    baseZ: 10,
    baseScale: 0.9,
    rotateY: -16
  },
  {
    id: "hanoi",
    name: "Hà Nội",
    subtitle: "Phố cổ & ẩm thực",
    image: hanoi,
    baseZ: 20,
    baseScale: 0.95,
    rotateY: -8
  },
  {
    id: "hcm",
    name: "TP Hồ Chí Minh",
    subtitle: "Nhịp sống sôi động",
    image: hcm,
    baseZ: 30,
    baseScale: 1,
    rotateY: 0
  },
  {
    id: "danang",
    name: "Đà Nẵng",
    subtitle: "Biển xanh & cầu vàng",
    image: danang,
    baseZ: 20,
    baseScale: 0.95,
    rotateY: 8
  },
  {
    id: "vungtau",
    name: "Vũng Tàu",
    subtitle: "Hải sản & hoàng hôn",
    image: vungtau,
    baseZ: 10,
    baseScale: 0.9,
    rotateY: 16
  }
];

export default function CityCoverFlowWidget() {
  const [hoveredCity, setHoveredCity] = useState<string | null>(null);

  const centerId = useMemo(() => "hcm", []);

  return (
    <section className="px-6 pb-20 pt-4">
      <div className="mx-auto w-full max-w-6xl space-y-8">
        <div className="space-y-3">
          <div className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-flame">
            Khám phá địa điểm
          </div>
          <h2 className="font-display text-3xl font-semibold text-slate-900 md:text-4xl">
            Những thành phố được săn đón nhất.
          </h2>
        </div>

        <div className="hidden md:flex" style={{ perspective: "1400px" }}>
          <div className="mx-auto flex items-center">
            {cities.map((city, index) => {
              const isHovered = hoveredCity === city.id;
              const isCenter = city.id === centerId;
              const isDimmed = hoveredCity
                ? hoveredCity !== city.id
                : !isCenter;
              return (
                <motion.div
                  key={city.id}
                  onMouseEnter={() => setHoveredCity(city.id)}
                  onMouseLeave={() => setHoveredCity(null)}
                  animate={{
                    scale: isHovered ? 1.12 : city.baseScale,
                    rotateY: isHovered ? 0 : city.rotateY,
                    zIndex: isHovered ? 50 : city.baseZ
                  }}
                  transition={{ type: "spring", stiffness: 110, damping: 16 }}
                  className={cn(
                    "relative h-[360px] w-[264px] overflow-hidden rounded-3xl border border-white/70",
                    "-ml-6 first:ml-0",
                    isCenter
                      ? "shadow-[0_20px_50px_rgba(0,0,0,0.3)]"
                      : "shadow-soft"
                  )}
                  style={{
                    backgroundImage: `url(${city.image.src})`,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                    transformStyle: "preserve-3d"
                  }}
                >
                  <div
                    className={cn(
                      "absolute inset-0 transition duration-300",
                      isCenter ? "bg-black/0" : "bg-black/40"
                    )}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/25 to-transparent" />
                  <div className="absolute bottom-5 left-5 text-left text-white">
                    <div className="text-lg font-semibold drop-shadow">
                      {city.name}
                    </div>
                    <div className="text-xs text-white/85 drop-shadow">
                      {city.subtitle}
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        <div className="md:hidden">
          <div className="flex gap-4 overflow-x-auto pb-2" style={{ scrollSnapType: "x mandatory" }}>
            {cities.map((city) => (
              <div
                key={city.id}
                className="relative h-[260px] w-[264px] shrink-0 overflow-hidden rounded-3xl border border-white/70 shadow-soft"
                style={{
                  backgroundImage: `url(${city.image.src})`,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                  scrollSnapAlign: "center"
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/25 to-transparent" />
                <div className="absolute bottom-4 left-4 text-left text-white">
                  <div className="text-base font-semibold drop-shadow">
                    {city.name}
                  </div>
                  <div className="text-xs text-white/80 drop-shadow">
                    {city.subtitle}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

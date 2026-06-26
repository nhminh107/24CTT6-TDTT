"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { MapPin, Sparkles } from "lucide-react";
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
    description: "Quán nướng, cà phê vườn và những bữa tối se lạnh.",
    accent: "from-emerald-400 to-teal-300",
    count: "128 địa điểm",
    image: dalat,
  },
  {
    id: "hanoi",
    name: "Hà Nội",
    subtitle: "Phố cổ & ẩm thực",
    description: "Bún chả, phở đêm và hàng quán lâu đời trong phố nhỏ.",
    accent: "from-amber-300 to-orange-400",
    count: "156 địa điểm",
    image: hanoi,
  },
  {
    id: "hcm",
    name: "TP Hồ Chí Minh",
    subtitle: "Nhịp sống sôi động",
    description: "Bistro, street food và quán mở muộn cho mọi lịch trình.",
    accent: "from-brand-coral to-brand-flame",
    count: "214 địa điểm",
    image: hcm,
  },
  {
    id: "danang",
    name: "Đà Nẵng",
    subtitle: "Biển xanh & cầu vàng",
    description: "Hải sản ven biển, mì Quảng và những điểm ăn gần trung tâm.",
    accent: "from-sky-300 to-cyan-400",
    count: "142 địa điểm",
    image: danang,
  },
  {
    id: "vungtau",
    name: "Vũng Tàu",
    subtitle: "Hải sản & hoàng hôn",
    description: "Bữa trưa hải sản, quán view biển và điểm dừng cuối tuần.",
    accent: "from-rose-300 to-orange-300",
    count: "96 địa điểm",
    image: vungtau,
  }
];

export default function CityCoverFlowWidget() {
  const [activeCityId, setActiveCityId] = useState("hcm");
  const activeCity = cities.find((city) => city.id === activeCityId) || cities[2];

  return (
    <section className="relative overflow-hidden px-4 pb-20 pt-8 sm:px-6">
      <div className="mx-auto w-full max-w-6xl">
        <div className="mb-8 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-brand-coral/15 bg-brand-coral/5 px-3 py-1 text-xs font-bold uppercase tracking-[0.24em] text-brand-flame">
              <Sparkles size={14} />
              Khám phá địa điểm
            </div>
            <h2 className="font-display text-3xl font-semibold leading-tight text-slate-950 md:text-5xl">
              Những thành phố được săn đón nhất.
            </h2>
            <p className="max-w-xl text-sm leading-6 text-slate-600 md:text-base">
              Chọn một thành phố để xem nhanh phong vị, số lượng địa điểm nổi bật và cảm hứng cho lịch trình ẩm thực tiếp theo.
            </p>
          </div>

          <div className="hidden min-w-[220px] rounded-2xl border border-slate-200 bg-white p-4 shadow-soft md:block">
            <div className="text-[10px] font-bold uppercase tracking-[0.24em] text-slate-400">
              Đang nổi bật
            </div>
            <div className="mt-2 flex items-center gap-2 text-slate-900">
              <MapPin size={17} className="text-brand-coral" />
              <span className="text-lg font-bold">{activeCity.name}</span>
            </div>
            <div className="mt-1 text-sm text-slate-500">{activeCity.count}</div>
          </div>
        </div>

        <div className="hidden h-[430px] gap-4 md:flex">
          {cities.map((city) => {
            const isActive = activeCityId === city.id;
            return (
              <motion.div
                key={city.id}
                animate={{ flex: isActive ? 1.7 : 0.78 }}
                transition={{ type: "spring", stiffness: 120, damping: 20 }}
                className="min-w-0"
              >
                <button
                  type="button"
                  onMouseEnter={() => setActiveCityId(city.id)}
                  onFocus={() => setActiveCityId(city.id)}
                  onClick={() => setActiveCityId(city.id)}
                  className={cn(
                    "group relative h-full w-full overflow-hidden rounded-[28px] border text-left shadow-soft outline-none transition duration-300",
                    isActive
                      ? "border-white shadow-[0_24px_70px_rgba(15,23,42,0.24)]"
                      : "border-white/70 hover:border-white hover:shadow-[0_18px_45px_rgba(15,23,42,0.18)]"
                  )}
                >
                  <img
                    src={city.image.src}
                    alt={city.name}
                    className={cn(
                      "h-full w-full object-cover transition duration-700",
                      isActive ? "scale-100" : "scale-105 group-hover:scale-100"
                    )}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/20 to-transparent" />
                  <div
                    className={cn(
                      "absolute inset-x-0 top-0 h-24 bg-gradient-to-b opacity-70",
                      city.accent
                    )}
                  />
                  <div className="absolute left-4 top-4 flex items-center gap-2 rounded-full bg-white/90 px-3 py-1.5 text-xs font-bold text-slate-800 shadow-sm backdrop-blur">
                    <MapPin size={13} className="text-brand-coral" />
                    {city.count}
                  </div>
                  <div className="absolute inset-x-0 bottom-0 p-5 text-white">
                    <div
                      className={cn(
                        "mb-4 h-1.5 rounded-full bg-gradient-to-r transition-all duration-300",
                        city.accent,
                        isActive ? "w-20" : "w-10"
                      )}
                    />
                    <div
                      className={cn(
                        "font-display font-semibold leading-tight",
                        isActive ? "text-3xl" : "text-xl"
                      )}
                    >
                      {city.name}
                    </div>
                    <div className="mt-1 text-sm font-semibold text-white/85">{city.subtitle}</div>
                    <div
                      className={cn(
                        "grid transition-all duration-300",
                        isActive ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                      )}
                    >
                      <p className="mt-4 min-h-0 overflow-hidden text-sm leading-6 text-white/78">
                        {city.description}
                      </p>
                    </div>
                  </div>
                </button>
              </motion.div>
            );
          })}
        </div>

        <div className="md:hidden">
          <div className="flex gap-4 overflow-x-auto pb-3" style={{ scrollSnapType: "x mandatory" }}>
            {cities.map((city) => (
              <button
                key={city.id}
                type="button"
                onClick={() => setActiveCityId(city.id)}
                className="relative h-[300px] w-[78vw] max-w-[310px] shrink-0 overflow-hidden rounded-[28px] border border-white/70 text-left shadow-soft"
                style={{
                  scrollSnapAlign: "center"
                }}
              >
                <img src={city.image.src} alt={city.name} className="h-full w-full object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/25 to-transparent" />
                <div className="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1.5 text-xs font-bold text-slate-800 shadow-sm">
                  {city.count}
                </div>
                <div className="absolute bottom-4 left-4 right-4 text-white">
                  <div className={cn("mb-3 h-1.5 w-14 rounded-full bg-gradient-to-r", city.accent)} />
                  <div className="font-display text-2xl font-semibold drop-shadow">
                    {city.name}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-white/85 drop-shadow">
                    {city.subtitle}
                  </div>
                  <p className="mt-3 text-sm leading-6 text-white/78">{city.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

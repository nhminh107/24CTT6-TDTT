"use client";

import { useEffect, useMemo, useState } from "react";
import { Wallet, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "@/components/layout/Navbar";
import LocationSearch from "@/components/ui/LocationSearch";
import ChatInterface from "@/components/sections/ChatInterface";
import { cn } from "@/lib/utils";
import BoardingPass from "@/components/ui/BoardingPass";
import { useAuth } from "@/context/AuthContext";

type ApiRestaurant = {
  id?: string;
  name?: string;
  address?: string;
  star?: number;
  avg_price?: number;
  phone_num?: string | number;
  image_url?: string;
  semantic_text?: string;
  meals?: string[];
  assigned_meal?: string;
  main_tag?: string[];
  potential_tag?: string[];
  warnings?: string[];
  notes?: string[];
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export default function AppPage() {
  const [location, setLocation] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [budget, setBudget] = useState("");
  const [promptInput, setPromptInput] = useState("");
  const [isCompact, setIsCompact] = useState(false);
  const [showBoardingPass, setShowBoardingPass] = useState(false);
  const [currentItinerary, setCurrentItinerary] = useState<ApiRestaurant[]>([]);
  const { user } = useAuth();

  // Load itinerary on mount
  useEffect(() => {
    if (user?.uid) {
      fetch(`${API_BASE_URL}/api/v1/itinerary/${user.uid}`)
        .then(res => res.json())
        .then(data => {
          if (data.status === "success") {
            setCurrentItinerary(data.itinerary || []);
          }
        })
        .catch(err => console.error("Failed to fetch itinerary:", err));
    }
  }, [user?.uid]);

  const [meals, setMeals] = useState([
    // ... rest of meals
    {
      label: "STOP 01",
      name: "Chưa có dữ liệu",
      time: "12p",
      price: "Chưa cập nhật",
      type: "Cafe",
      rating: 0
    },
    {
      label: "STOP 02",
      name: "Chưa có dữ liệu",
      time: "15p",
      price: "Chưa cập nhật",
      type: "Bistro",
      rating: 0
    },
    {
      label: "STOP 03",
      name: "Chưa có dữ liệu",
      time: "18p",
      price: "Chưa cập nhật",
      type: "Fine Dining",
      rating: 0
    }
  ]);

  const mealTimes = ["07:30", "12:15", "19:30", "21:00"];
  const mealTypes = ["Cafe", "Bistro", "Fine Dining", "Street Food"];

  const getTravelTime = () => `${Math.floor(10 + Math.random() * 11)}p`;

  const buildMealStops = (restaurants: { name: string; price: string | number; meals?: string[]; rating?: number }[]) =>
    restaurants.slice(0, 3).map((restaurant, index) => {
      const label = `STOP ${String(index + 1).padStart(2, "0")}`;
      const priceText =
        typeof restaurant.price === "number"
          ? `${restaurant.price.toLocaleString("vi-VN")}đ`
          : restaurant.price || "Chưa cập nhật";
      const type = restaurant.meals?.[0]?.trim() || mealTypes[index] || "Cafe";
      return {
        label,
        name: restaurant.name || "Chưa có dữ liệu",
        time: getTravelTime(),
        price: priceText,
        type,
        rating: restaurant.rating ?? 0
      };
    });
  const filters = useMemo(
    () => ["Lãng mạn", "Cay", "Hải sản", "View biển", "Chay", "Gia đình"],
    []
  );

  useEffect(() => {
    const upperThreshold = 640;
    const lowerThreshold = 320;
    const handleScroll = () => {
      setIsCompact((prev) => {
        if (prev) {
          return window.scrollY < lowerThreshold ? false : prev;
        }
        return window.scrollY > upperThreshold ? true : prev;
      });
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const budgetPhrase = useMemo(() => {
    const amount = Number(budget);
    if (!amount || Number.isNaN(amount)) {
      return "";
    }
    return `Với ngân sách là ${amount.toLocaleString("vi-VN")} cho 1 người`;
  }, [budget]);

  const budgetDisplay = useMemo(() => {
    const amount = Number(budget);
    if (!amount || Number.isNaN(amount)) {
      return "Chưa nhập";
    }
    return `${amount.toLocaleString("vi-VN")} VNĐ`;
  }, [budget]);

  const applyBudgetToPrompt = (value: string, current: string) => {
    const amount = Number(value);
    const phrase =
      !amount || Number.isNaN(amount)
        ? ""
        : `Với ngân sách là ${amount.toLocaleString("vi-VN")} cho 1 người`;
    const cleaned = current
      .replace(/Với ngân sách là[^.]*cho 1 người\.?/i, "")
      .replace(/\s{2,}/g, " ")
      .replace(/^[\s,.-]+|[\s,.-]+$/g, "")
      .trim();
    if (!phrase) {
      return cleaned;
    }
    if (!cleaned) {
      return phrase;
    }
    return `${phrase}. ${cleaned}`;
  };

  return (
    <div className="min-h-screen bg-white/70 pb-24">
      <Navbar />
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-10">
        <div className="flex flex-col gap-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand-coral/20 bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-flame shadow-soft">
            Ứng dụng BMI
          </div>
          <div className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
            Bite Mapping Intelligent
          </div>
          <h1 className="font-display text-3xl font-semibold text-slate-900 md:text-4xl">
            Tối ưu lộ trình ẩm thực theo phong cách của bạn.
          </h1>
          <p className="max-w-2xl text-sm text-slate-600 md:text-base">
            Cung cấp vị trí, ngân sách và mong muốn để AI đề xuất tuyến đường ăn uống hợp lý nhất.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-10 items-start px-4">
          {/* CỘT BÊN TRÁI: Tìm kiếm, Bộ lọc & Lịch trình */}
          <aside className="space-y-8 -mx-10 px-10 pb-10">
            <div className="space-y-6">
              <LocationSearch
                value={location}
                onChange={setLocation}
                onSelect={(option) => {
                  setLocation(option.name);
                  setPlaceId(option.id);
                }}
              />

              <div>
                <label className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-lagoon pl-2">
                  Ngân sách tổng
                </label>
                <div className="glass mt-3 flex items-center gap-3 rounded-2xl px-4 py-3 shadow-soft">
                  <Wallet className="text-brand-teal" size={18} />
                  <input
                    type="number"
                    value={budget}
                    onBlur={(event) => {
                      const nextValue = event.target.value;
                      setPromptInput((prev) =>
                        applyBudgetToPrompt(nextValue, prev)
                      );
                    }}
                    onChange={(event) => setBudget(event.target.value)}
                    placeholder="Nhập ngân sách"
                    className="w-full min-w-0 bg-transparent text-sm text-slate-700 outline-none"
                  />
                  <span className="text-xs font-semibold text-slate-500">VNĐ</span>
                </div>
              </div>

              <div className="glass rounded-[32px] border border-white/60 p-6 text-sm text-slate-600 shadow-soft">
                <div className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-flame mb-4 pl-1">
                  Bộ lọc nhanh
                </div>
                <div className="flex flex-wrap gap-2.5">
                  {filters.map((filter) => (
                    <button
                      key={filter}
                      type="button"
                      onClick={() => {
                        setPromptInput((prev) => {
                          if (prev.toLowerCase().includes(filter.toLowerCase())) {
                            return prev;
                          }
                          const next = prev ? `${prev}, ${filter}` : filter;
                          return next;
                        });
                      }}
                      className="rounded-full border border-slate-200/50 bg-white/80 px-4 py-2 text-[11px] font-bold text-slate-600 transition-all hover:border-brand-coral/40 hover:text-brand-coral"
                    >
                      {filter}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Lịch trình đã chốt (Hiện lên khi có quán được chọn) - CHỈ PHẦN NÀY LÀ STICKY */}
            {currentItinerary.length > 0 && (
              <div className="sticky top-24 pb-20">
                <div className="rounded-[32px] border border-white/60 bg-white/40 p-6 shadow-glow backdrop-blur-xl">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-brand-coral animate-pulse" />
                      <h3 className="text-sm font-bold uppercase tracking-widest text-slate-800">Lịch trình của bạn</h3>
                    </div>
                    <button 
                      onClick={async () => {
                        if (confirm("Xóa toàn bộ lịch trình và bắt đầu lại?")) {
                          await fetch(`${API_BASE_URL}/api/v1/itinerary/${user?.uid}`, { method: "DELETE" });
                          setCurrentItinerary([]);
                        }
                      }}
                      className="text-[10px] font-bold uppercase tracking-tight text-rose-500 hover:text-rose-600 transition-colors"
                    >
                      Xóa sạch
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    {currentItinerary.map((item, idx) => (
                      <motion.div 
                        key={idx}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="group relative flex gap-4 rounded-2xl bg-white/60 p-3 shadow-soft hover:shadow-md transition-all border border-white/40"
                      >
                        <div className="absolute -left-2 -top-2 h-6 w-6 rounded-full bg-brand-coral flex items-center justify-center text-[10px] font-bold text-white shadow-sm z-10">
                          {idx + 1}
                        </div>
                        <img 
                          src={item.image_url?.replace(/\\\//g, "/")} 
                          alt={item.name} 
                          className="h-14 w-14 rounded-xl object-cover shadow-sm"
                        />
                        <div className="flex-1 min-w-0">
                          <div className="text-[9px] font-black uppercase tracking-tighter text-brand-flame mb-0.5">{item.meal}</div>
                          <div className="text-xs font-bold text-slate-900 truncate">{item.name}</div>
                          <div className="text-[10px] text-slate-500 truncate">{item.address}</div>
                        </div>

                        <button
                          onClick={async () => {
                            if (item.meal) {
                              try {
                                const response = await fetch(`${API_BASE_URL}/api/v1/itinerary/${user?.uid}/${item.meal}`, { method: "DELETE" });
                                const data = await response.json();
                                if (data.status === "success") {
                                  setCurrentItinerary(prev => prev.filter(it => it.meal !== item.meal));
                                }
                              } catch (err) {
                                console.error("Failed to delete itinerary item:", err);
                              }
                            }
                          }}
                          className="opacity-0 group-hover:opacity-100 absolute -right-1 -top-1 h-5 w-5 rounded-full bg-slate-900 text-white flex items-center justify-center transition-all hover:bg-rose-500"
                        >
                          <X size={10} strokeWidth={3} />
                        </button>
                      </motion.div>
                    ))}
                  </div>

                  <div className="mt-8">
                    <button
                      onClick={() => {
                        const mapped = currentItinerary.map(it => ({
                          name: it.name || "",
                          price: it.avg_price || "Chưa cập nhật",
                          meals: it.meals || [],
                          rating: it.star || 0
                        }));
                        setMeals(buildMealStops(mapped));
                        setShowBoardingPass(true);
                      }}
                      className="w-full py-3 rounded-2xl bg-gradient-to-r from-brand-coral to-brand-flame text-white text-xs font-bold uppercase tracking-widest shadow-glow hover:opacity-90 transition-all"
                    >
                      Xuất vé ẩm thực
                    </button>
                  </div>
                </div>
              </div>
            )}
          </aside>

          {/* CỘT BÊN PHẢI: Chat Interface */}
          <main className="min-h-[800px]">
            <ChatInterface
              placeId={placeId}
              input={promptInput}
              onInputChange={setPromptInput}
              currentItinerary={currentItinerary}
              setCurrentItinerary={setCurrentItinerary}
              onPreviewPass={(restaurants) => {
                if (restaurants.length) {
                  setMeals(buildMealStops(restaurants));
                  setShowBoardingPass(true);
                }
              }}
            />
          </main>
        </div>
      </div>

      <motion.div
        initial={false}
        animate={
          isCompact
            ? { opacity: 1, y: 0, scale: 1 }
            : { opacity: 0, y: 36, scale: 0.94 }
        }
        transition={{ duration: 0.9, ease: "easeOut" }}
        className={cn(
          "fixed right-6 bottom-24 z-40 w-[240px] rounded-2xl border border-white/60 bg-white/80 p-4 text-sm text-slate-600 shadow-soft backdrop-blur",
          isCompact ? "pointer-events-auto" : "pointer-events-none"
        )}
      >
        <div className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-flame">
          Tóm tắt phiên
        </div>
        <div className="mt-3 space-y-2">
          <div>
            Vị trí: <span className="font-semibold text-slate-900">{location || "Chưa chọn"}</span>
          </div>
          <div>
            Ngân sách: <span className="font-semibold text-slate-900">{budgetPhrase || "Chưa nhập"}</span>
          </div>
        </div>
      </motion.div>

      <AnimatePresence>
        {showBoardingPass && (
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.96 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4 py-8 backdrop-blur"
          >
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 20, opacity: 0 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="flex w-full max-w-3xl flex-col"
            >
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold uppercase tracking-[0.3em] text-white/80">
                  Xuất vé ẩm thực
                </div>
                <button
                  type="button"
                  onClick={() => setShowBoardingPass(false)}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-white/90 text-slate-600 shadow-soft"
                >
                  <X size={18} />
                </button>
              </div>
              <div className="mt-4 max-h-[75vh] overflow-auto rounded-3xl bg-white/90 p-6 shadow-soft">
                <BoardingPass
                  departure={location}
                  meals={meals}
                  totalAllowance={budgetDisplay}
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

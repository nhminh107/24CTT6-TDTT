"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "@/components/layout/Navbar";
import ChatInterface from "@/components/sections/ChatInterface";
import BoardingPass from "@/components/ui/BoardingPass";

export default function AppPage() {
  const [location, setLocation] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [budget, setBudget] = useState("");
  const [showBoardingPass, setShowBoardingPass] = useState(false);
  const [meals, setMeals] = useState([
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

  const budgetDisplay = budget
    ? `${Number(budget).toLocaleString("vi-VN")} VNĐ`
    : "Chưa nhập";

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

        <div className="w-full">
          <ChatInterface
            placeId={placeId}
            onLocationChange={setLocation}
            onPlaceIdChange={setPlaceId}
            onBudgetChange={setBudget}
            onPreviewPass={(restaurants) => {
              if (restaurants.length) {
                setMeals(buildMealStops(restaurants));
                setShowBoardingPass(true);
              }
            }}
          />
        </div>
      </div>

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
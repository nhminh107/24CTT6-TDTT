"use client";

import { useState } from "react";
import { Wallet } from "lucide-react";
import LocationSearch from "@/components/ui/LocationSearch";
import ChatInterface from "@/components/sections/ChatInterface";

export default function AppPage() {
  const [location, setLocation] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [budget, setBudget] = useState("600000");
  const [promptInput, setPromptInput] = useState("");

  const filters = ["Lãng mạn", "Cay", "Hải sản", "View biển", "Chay", "Gia đình"];

  return (
    <div className="min-h-screen bg-white/70 pb-24">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 py-10">
        <div className="flex flex-col gap-4">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand-coral/20 bg-white/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-flame shadow-soft">
            Ứng dụng RouteAI
          </div>
          <h1 className="font-display text-3xl font-semibold text-slate-900 md:text-4xl">
            Tối ưu lộ trình ẩm thực theo phong cách của bạn.
          </h1>
          <p className="max-w-2xl text-sm text-slate-600 md:text-base">
            Cung cấp vị trí, ngân sách và mong muốn để AI đề xuất tuyến đường ăn uống hợp lý nhất.
          </p>
        </div>

          <div className="grid gap-6 lg:grid-cols-[1.1fr_1.4fr]">
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
              <label className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-lagoon">
                Ngân sách tổng
              </label>
              <div className="glass mt-3 flex items-center gap-3 rounded-2xl px-4 py-3 shadow-soft">
                <Wallet className="text-brand-teal" size={18} />
                <input
                  type="number"
                  value={budget}
                  onChange={(event) => setBudget(event.target.value)}
                  className="w-full min-w-0 bg-transparent text-sm text-slate-700 outline-none"
                />
                <span className="text-xs font-semibold text-slate-500">VNĐ</span>
              </div>
            </div>

            <div className="glass rounded-3xl border border-white/60 p-5 text-sm text-slate-600 shadow-soft">
              <div className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-flame">
                Bộ lọc nhanh
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                {filters.map((filter) => (
                  <button
                    key={filter}
                    type="button"
                    onClick={() => {
                      const next = promptInput
                        ? `${promptInput}, ${filter}`
                        : filter;
                      setPromptInput(next);
                    }}
                    className="rounded-full border border-slate-200/60 bg-white/70 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:text-slate-900"
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <ChatInterface
            placeId={placeId}
            input={promptInput}
            onInputChange={setPromptInput}
          />
        </div>
      </div>
    </div>
  );
}

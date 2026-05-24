"use client";

import { useEffect, useState } from "react";
import { MapPin, Search } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

type LocationOption = {
  id: string;
  name: string;
  subtitle?: string;
};

type ApiSuggestion = {
  description?: string;
  place_id?: string;
};

const API_BASE_URL = "";

type LocationSearchProps = {
  value: string;
  onChange: (value: string) => void;
  onSelect: (option: LocationOption) => void;
};

export default function LocationSearch({
  value,
  onChange,
  onSelect
}: LocationSearchProps) {
  const [options, setOptions] = useState<LocationOption[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedValue, setSelectedValue] = useState("");

  useEffect(() => {
    const trimmed = value.trim();
    if (!trimmed) {
      setOptions([]);
      setOpen(false);
      return;
    }

    if (selectedValue && trimmed === selectedValue) {
      setOptions([]);
      setOpen(false);
      setLoading(false);
      return;
    }

    setLoading(true);
    const controller = new AbortController();
    const handle = setTimeout(async () => {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/maps/suggestions?q=${encodeURIComponent(trimmed)}`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          setOptions([]);
          setOpen(true);
          return;
        }
        const data = (await response.json()) as ApiSuggestion[];
        const mapped = Array.isArray(data)
          ? data
              .filter((item) => item.description)
              .map((item) => ({
                id: item.place_id || item.description || "",
                name: item.description || "",
                subtitle: "Gợi ý từ bản đồ"
              }))
          : [];
        setOptions(mapped);
        setOpen(true);
      } catch {
        setOptions([]);
        setOpen(true);
      } finally {
        setLoading(false);
      }
    }, 350);

    return () => {
      controller.abort();
      clearTimeout(handle);
    };
  }, [value]);

  const handleSelect = (option: LocationOption) => {
    setSelectedValue(option.name);
    onSelect(option);
    setOpen(false);
  };

  const handleChange = (nextValue: string) => {
    if (selectedValue) {
      setSelectedValue("");
    }
    onChange(nextValue);
  };

  return (
    <div className="relative z-30">
      <label className="text-xs font-semibold uppercase tracking-[0.3em] text-brand-lagoon">
        Vị trí hiện tại
      </label>
      <div className="glass mt-3 flex items-center gap-3 rounded-2xl px-4 py-3 shadow-soft">
        <MapPin className="text-brand-coral" size={18} />
        <input
          value={value}
          onChange={(event) => handleChange(event.target.value)}
          placeholder="Nhập khu vực bạn đang ở"
          className="w-full min-w-0 bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
        />
        <Search className="text-slate-400" size={18} />
      </div>

      <AnimatePresence>
        {open && (options.length > 0 || loading) && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="glass absolute left-0 right-0 z-50 mt-3 overflow-hidden rounded-2xl shadow-soft"
          >
            {loading ? (
              <div className="px-4 py-3 text-sm text-slate-500">
                Đang tìm gợi ý phù hợp...
              </div>
            ) : options.length === 0 ? (
              <div className="px-4 py-3 text-sm text-slate-500">
                Không có gợi ý phù hợp.
              </div>
            ) : (
              options.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => handleSelect(option)}
                  className="flex w-full flex-col gap-1 px-4 py-3 text-left text-sm text-slate-700 transition hover:bg-white/70"
                >
                  <span className="font-semibold text-slate-900">
                    {option.name}
                  </span>
                  {option.subtitle && (
                    <span className="text-xs text-slate-500">
                      {option.subtitle}
                    </span>
                  )}
                </button>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import { SendHorizontal, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import RestaurantCard from "@/components/ui/RestaurantCard";
import { useAuth } from "@/context/AuthContext";
type Restaurant = {
  id: string; // 👈 Thêm ID để làm key khi render danh sách
  name: string;
  address: string;
  rating: number;
  price: string | number;
  phone: string | number;
  mapUrl: string;
  imageUrl: string;
  semanticText: string;
  meals?: string[];
  // 👈 Bổ sung vào đây để Component RestaurantCard nhận được dữ liệu
  healthTagsDisplay?: {
    warnings?: string[];
    notes?: string[];
  };
};

type Message = {
  role: "user" | "assistant";
  content: string;
  restaurants?: Restaurant[];
};

const initialMessages: Message[] = [
  {
    role: "assistant",
    content:
      "Chào bạn! Hãy cho BMI biết khẩu vị, ngân sách và phong cách bạn mong muốn."
  }
];
const API_BASE_URL = "";

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
  // Bổ sung cấu trúc chứa cảnh báo và ghi chú từ Backend
    warnings?: string[];
    notes?: string[];
};

type ApiResponse = {
  status?: string;
  message?: string;
  detail?: string;
  result?: ApiRestaurant[]; // ⚠️ LƯU Ý: Đổi từ 'result' thành 'results' cho đúng với JSON mới của bạn
};

type ChatInterfaceProps = {
  placeId: string;
  input: string;
  onInputChange: (value: string) => void;
  onPreviewPass?: (restaurants: Restaurant[]) => void;
};

export default function ChatInterface({
  placeId,
  input,
  onInputChange,
  onPreviewPass
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();
  const suggestions = useMemo(
    () => [
      "Tối nay tôi muốn ăn hải sản view biển, ngân sách 800k.",
      "Tôi cần lộ trình ăn trưa, quán nước, ăn tối. Quán ăn trưa là quán Việt, quán ăn tối phải lãng mạn.",
      "Bữa trưa ăn món Việt, bữa tối fine dining lãng mạn."
    ],
    []
  );

  const buildRestaurants = (items: ApiRestaurant[]): Restaurant[] =>
  items.map((item, index) => {
    const imageUrl = item.image_url
      ? item.image_url.replace(/\\\//g, "/")
      : "";

    const mapQuery = [item.name, item.address]
      .filter(Boolean)
      .join(" ");

    const mapUrl = mapQuery
      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
          mapQuery
        )}`
      : "https://www.google.com/maps";

    const ratingValue =
      typeof item.star === "number"
        ? item.star
        : Number(item.star ?? 0) || 0;

    return {
      id: item.id ?? `${item.name}-${index}`,

      name: item.name || "Nhà hàng",
      address: item.address || "Chưa có địa chỉ",

      rating: ratingValue,
      price: item.avg_price ?? "Chưa cập nhật",
      phone: item.phone_num ?? "",

      mapUrl,
      imageUrl,

      semanticText: item.semantic_text
        ? String(item.semantic_text)
        : "Chưa có mô tả.",

      meals: item.meals ?? [],

      // 👇 QUAN TRỌNG
      warnings: item.warnings ?? [],
      notes: item.notes ?? []
    };
  });

  const buildAssistantMessage = (response: ApiResponse) => {

    console.log("API RESPONSE:", response);


    if (!response || response.status !== "success") {
      return {
        content:
          response?.message || response?.detail || "Lỗi hệ thống. Vui lòng thử lại.",
        restaurants: []
      };
    }
     const results = response.result || []; // <- sửa ở đây
    const count = results.length;
    const content =
      count > 0
        ? `Dạ, mình tìm thấy ${count} nhà hàng nè!`
        : "Không tìm thấy kết quả.";
    return {
      content,
      restaurants: buildRestaurants(results)
    };
  };

  const callRestaurantApi = async (prompt: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          user_id: user?.uid || "guest_user",
          ...(placeId ? { place_id: placeId } : {})
        })
      });
      const data = (await response.json()) as ApiResponse;
      const assistant = buildAssistantMessage(data);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: assistant.content,
          restaurants: assistant.restaurants
        }
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Không thể kết nối tới máy chủ. Vui lòng kiểm tra API và thử lại.",
          restaurants: []
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = () => {
    if (!input.trim()) {
      return;
    }
    if (isLoading) {
      return;
    }
    const prompt = input.trim();
    setMessages((prev) => [...prev, { role: "user", content: prompt }]);
    onInputChange("");
    callRestaurantApi(prompt);
  };

  return (
    <div className="flex h-full flex-col gap-6">
      <div className="rounded-3xl bg-gradient-to-r from-brand-coral via-brand-flame to-brand-lagoon p-[1px] shadow-glow">
        <div className="glass rounded-3xl p-6">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.3em] text-brand-flame">
            <Sparkles size={16} />
            Lời khuyên của AI
          </div>
          <div className="mt-4 text-sm leading-relaxed text-slate-600">
            Hãy mô tả rõ món ăn, không gian và mức ngân sách cho từng bữa. Bạn càng chi tiết, BMI càng tối ưu lộ trình.
          </div>
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-4 pb-32">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className="space-y-4">
            <div
              className={`flex gap-4 ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {message.role === "assistant" && (
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-brand-teal to-brand-lagoon text-white">
                  AI
                </div>
              )}
              <div
                className={`max-w-[520px] rounded-3xl px-5 py-4 text-sm shadow-soft ${
                  message.role === "user"
                    ? "bg-gradient-to-r from-brand-coral to-brand-flame text-white"
                    : "glass text-slate-700"
                }`}
              >
                {message.content}
              </div>
              {message.role === "user" && (
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                  U
                </div>
              )}
            </div>

            {message.role === "assistant" && message.restaurants?.length ? (
              <div className="space-y-4">
                {message.restaurants.map((restaurant, restaurantIndex) => (
                  <motion.div
                    key={`${index}-${restaurant.name}-${restaurantIndex}`}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                  >
                    <RestaurantCard restaurant={restaurant} />
                  </motion.div>
                ))}
                <div className="relative flex">
                  <motion.div
                    animate={{ y: [0, -6, 0], opacity: [0.85, 1, 0.85] }}
                    transition={{ duration: 2.2, repeat: Infinity }}
                    className="absolute -top-11 left-0 rounded-2xl border border-brand-coral/30 bg-white/90 px-3 py-2 text-xs font-semibold text-brand-flame shadow-soft"
                  >
                    Khoe vé sang chảnh ngay
                  </motion.div>
                  <motion.button
                    type="button"
                    onClick={() => onPreviewPass?.(message.restaurants || [])}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.98 }}
                    className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-brand-coral to-brand-flame px-5 py-3 text-sm font-semibold text-white shadow-glow"
                  >
                    <Sparkles size={16} />
                    Khoe lịch trình
                  </motion.button>
                </div>
              </div>
            ) : null}
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-brand-teal to-brand-lagoon text-white">
              AI
            </div>
            <div className="glass rounded-3xl px-5 py-4">
              <div className="flex items-center gap-2">
                <span className="text-slate-600">Đang suy nghĩ</span>
                <span className="flex items-center gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-coral" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-flame [animation-delay:120ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-lagoon [animation-delay:240ms]" />
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="flex flex-wrap gap-3">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => onInputChange(suggestion)}
              className="rounded-full border border-slate-200/60 bg-white/70 px-4 py-2 text-xs font-semibold text-slate-600 transition hover:text-slate-900"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      <div className="fixed bottom-6 left-0 right-0">
        <div className="mx-auto flex w-full max-w-4xl items-center gap-3 rounded-full border border-white/60 bg-white/80 px-4 py-3 shadow-soft backdrop-blur">
          <input
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                handleSend();
              }
            }}
            placeholder="Nhập yêu cầu của bạn..."
            className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={isLoading}
            className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-brand-coral to-brand-flame text-white shadow-glow"
          >
            <SendHorizontal size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

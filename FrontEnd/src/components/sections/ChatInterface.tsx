"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, ImagePlus, SendHorizontal, Sparkles, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import AuthPromptModal from "@/components/ui/AuthPromptModal";
import RestaurantMiniCard from "@/components/ui/RestaurandMiniCard";
import { getApiV1BaseUrl } from "@/lib/apiBase";
import { Restaurant, ApiRestaurant, buildRestaurants } from "@/lib/utils";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  restaurants?: Restaurant[];
  isCompact?: boolean;
  metadata?: {
    restaurants?: Restaurant[];
  };
};

const API_V1_BASE_URL = getApiV1BaseUrl();
const CLOUDINARY_CLOUD_NAME = process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME;
const CLOUDINARY_UPLOAD_PRESET = process.env.NEXT_PUBLIC_CLOUDINARY_UPLOAD_PRESET;
const MAX_MULTIMODAL_IMAGE_SIZE = 5 * 1024 * 1024;

type ApiResponse = {
  status?: string;
  message?: string;
  detail?: string;
  reason?: string;
  suggestions?: string[];
  meta?: {
    cache_hit?: boolean;
  };
  error?: {
    code?: number;
    message?: string;
    status?: string;
  };
  result?: ApiRestaurant[];
};

type ChatInterfaceProps = {
  placeId: string;
  chatId?: string | null;
  messages?: Message[];
  onMessagesChange?: (messages: Message[]) => void;
  onRestaurantsSelect?: (restaurants: Restaurant[]) => void;
  onRestaurantSelect?: (restaurantId: string) => void;
  onRefreshHistory?: () => void;
  onAutoCreateChat?: () => Promise<string | null>;
  currentItinerary?: any[];
  onSelectMeal?: (meal: string, restaurant: Restaurant) => void;
  fetchItinerary?: () => Promise<void>;
  input?: string;
  onInputChange?: (value: string) => void;
};

export default function ChatInterface({
  placeId,
  chatId,
  messages = [],
  onMessagesChange,
  onRestaurantsSelect,
  onRestaurantSelect,
  onRefreshHistory,
  onAutoCreateChat,
  currentItinerary = [],
  onSelectMeal,
  fetchItinerary,
  input: inputProp,
  onInputChange,
}: ChatInterfaceProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState("Đang hiểu yêu cầu của bạn");
  const [showLoginSuggestion, setShowLoginSuggestion] = useState(false);
  const [internalInput, setInternalInput] = useState("");
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [selectedImagePreview, setSelectedImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [errorModal, setErrorModal] = useState({
    open: false,
    code: "",
    message: ""
  });
  const { user } = useAuth();
  const suggestions = useMemo(
    () => [
      "Tối nay tôi muốn ăn hải sản view biển, ngân sách 800k.",
      "Tôi cần lộ trình ăn trưa, quán nước, ăn tối. Quán ăn trưa là quán Việt, quán ăn tối phải lãng mạn.",
      "Bữa trưa ăn món Việt, bữa tối fine dining lãng mạn."
    ],
    []
  );

  const input = inputProp ?? internalInput;

  useEffect(() => {
    return () => {
      if (selectedImagePreview) {
        URL.revokeObjectURL(selectedImagePreview);
      }
    };
  }, [selectedImagePreview]);

  useEffect(() => {
    if (!isLoading) {
      setLoadingStage("Đang hiểu yêu cầu của bạn");
      return;
    }

    const stages = [
      "Đang hiểu yêu cầu của bạn",
      "Đang kiểm tra vị trí và ngân sách",
      "Đang lọc theo hồ sơ sức khỏe",
      "Đang chấm điểm các nhà hàng",
      "Đang hoàn thiện lịch trình phù hợp"
    ];
    let index = 0;
    const interval = window.setInterval(() => {
      index = Math.min(index + 1, stages.length - 1);
      setLoadingStage(stages[index]);
    }, 1800);

    return () => window.clearInterval(interval);
  }, [isLoading]);

  const setInputValue = (value: string) => {
    if (onInputChange) {
      onInputChange(value);
    }
    if (inputProp === undefined) {
      setInternalInput(value);
    }
  };

  const setChatError = (code: string, message: string) => {
    setErrorModal({
      open: true,
      code,
      message
    });
  };

  const clearSelectedImage = () => {
    if (selectedImagePreview) {
      URL.revokeObjectURL(selectedImagePreview);
    }
    setSelectedImageFile(null);
    setSelectedImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleImageSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setChatError("IMAGE_TYPE", "Vui lòng chọn một tệp ảnh hợp lệ.");
      return;
    }

    if (file.size > MAX_MULTIMODAL_IMAGE_SIZE) {
      setChatError("IMAGE_SIZE", "Ảnh gửi kèm không được vượt quá 5MB.");
      return;
    }

    if (selectedImagePreview) {
      URL.revokeObjectURL(selectedImagePreview);
    }
    setSelectedImageFile(file);
    setSelectedImagePreview(URL.createObjectURL(file));
  };

  const uploadMultimodalImage = async (file: File) => {
    if (!CLOUDINARY_CLOUD_NAME || !CLOUDINARY_UPLOAD_PRESET) {
      throw new Error("Chưa cấu hình Cloudinary để tải ảnh lên.");
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("upload_preset", CLOUDINARY_UPLOAD_PRESET);

    const response = await fetch(
      `https://api.cloudinary.com/v1_1/${CLOUDINARY_CLOUD_NAME}/image/upload`,
      {
        method: "POST",
        body: formData,
      }
    );

    const data = await response.json();
    if (!response.ok || !data.secure_url) {
      throw new Error(data.error?.message || "Không thể tải ảnh lên.");
    }

    return data.secure_url as string;
  };

  const transformMultimodalPrompt = async (prompt: string, imageUrl: string) => {
    const response = await fetch(`${API_V1_BASE_URL}/multimodal/transform`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        image_url: imageUrl,
      }),
    });

    const data = await response.json().catch(() => null);
    if (!response.ok || data?.status !== "success" || !data?.transformed_prompt) {
      throw new Error(data?.detail || data?.message || "Không thể phân tích ảnh.");
    }

    return data.transformed_prompt as string;
  };

  const buildAssistantMessage = (response: ApiResponse) => {
    console.log("API RESPONSE:", response);

    if (!response) {
      return {
        content: "Lỗi hệ thống. Vui lòng thử lại.",
        restaurants: []
      };
    }

    if (response.status === "success") {
      const results = response.result || [];
      const count = results.length;
      const content =
        response.meta?.cache_hit && count > 0
          ? `Mình có sẵn ${count} lựa chọn phù hợp từ bộ nhớ tạm nè!`
          : count > 0
          ? `Dạ, mình tìm thấy ${count} nhà hàng nè!`
          : "Không tìm thấy kết quả.";
      return {
        content,
        restaurants: buildRestaurants(results)
      };
    }

    if (response.status === "poor_info") {
      return {
        content: response.message || "Bạn vui lòng cung cấp thêm thông tin để tôi có thể hỗ trợ tìm kiếm tốt hơn nhé.",
        restaurants: []
      };
    }

    if (response.status === "empty") {
      const suggestions = response.suggestions || [];
      const suggestionText =
        suggestions.length > 0
          ? `\n\nBạn có thể thử:\n${suggestions.map((item) => `• ${item}`).join("\n")}`
          : "";
      return {
        content: `${response.message || "Rất tiếc, tôi không tìm thấy quán ăn nào phù hợp với yêu cầu của bạn."}${suggestionText}`,
        restaurants: []
      };
    }

    if (response.status === "out_scope") {
      return {
        content: response.message || "Dạ, câu hỏi này nằm ngoài phạm vi hỗ trợ của tôi. Bạn vui lòng hỏi về ẩm thực, sức khỏe hoặc du lịch nhé!",
        restaurants: []
      };
    }

    if (response.status === "success_qa") {

      return {
        content: response.message || "Hệ thống không thể trả lời câu hỏi của bạn, bạn vui lòng liên hệ admin để được hỗ trợ nhé.",
        restaurants: []
      };
    }

    return {
      content: response.message || response.detail || "Lỗi hệ thống. Vui lòng thử lại.",
      restaurants: []
    };
  };

  const callRestaurantApi = async (prompt: string, activeChatId: string | null, latestMessages: Message[]) => {
    setIsLoading(true);
    setLoadingStage("Đang hiểu yêu cầu của bạn");
    try {
      const response = await fetch(`${API_V1_BASE_URL}/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          user_id: user?.uid || "guest_user",
          chat_id: activeChatId,
          ...(placeId ? { place_id: placeId } : {})
        })
      });
      let data: ApiResponse | null = null;
      try {
        data = (await response.json()) as ApiResponse;
      } catch {
        data = null;
      }

      if (response.status !== 200) {
        const message = "Hệ thống đang quá tải vui lòng thử lại sau.";
        const detailedMessage =
          data?.message ||
          data?.detail ||
          data?.error?.message ||
          (data ? JSON.stringify(data) : "Đã có lỗi xảy ra.");
        const errorCode = data?.error?.code ?? response.status;
        setErrorModal({
          open: true,
          code: String(errorCode),
          message
        });
        const messageId = Date.now().toString();
        onMessagesChange?.([
          ...latestMessages,
          {
            id: messageId,
            role: "assistant",
            content: detailedMessage,
            restaurants: []
          }
        ]);
        return;
      }

      if (!data) {
        const message = "Hệ thống đang quá tải vui lòng thử lại sau.";
        setErrorModal({
          open: true,
          code: String(response.status),
          message
        });
        const messageId = Date.now().toString();
        onMessagesChange?.([
          ...latestMessages,
          {
            id: messageId,
            role: "assistant",
            content: message,
            restaurants: []
          }
        ]);
        return;
      }

      const assistant = buildAssistantMessage(data);
      const messageId = Date.now().toString();
      
      // Update parent messages
      const finalMessages: Message[] = [
        ...latestMessages.map((msg) => ({
          ...msg,
          isCompact: true 
        })),
        {
          id: messageId,
          role: "assistant",
          content: assistant.content,
          restaurants: assistant.restaurants,
          isCompact: false
        }
      ];
      onMessagesChange?.(finalMessages);

      // Call callback to update dashboard state
      if (assistant.restaurants.length > 0) {
        onRestaurantsSelect?.(assistant.restaurants);
        // Suggest login if guest user
        if (!user) {
          setTimeout(() => setShowLoginSuggestion(true), 1500);
        }
      }
      
      // Refresh chat history to update titles/timestamps
      if (activeChatId) {
        onRefreshHistory?.();
      }

      // Sync itinerary from backend (since it's now updated automatically)
      if (user && fetchItinerary) {
        window.setTimeout(() => {
          fetchItinerary();
        }, 700);
      }
    } catch {
      const message = "Hệ thống đang quá tải vui lòng thử lại sau.";
      setErrorModal({
        open: true,
        code: "NETWORK",
        message
      });
      const messageId = Date.now().toString();
      onMessagesChange?.([
        ...latestMessages,
        {
          id: messageId,
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

  const handleSend = async () => {
    if (!input.trim() || isLoading) {
      return;
    }
    const originalPrompt = input.trim();
    let prompt = originalPrompt;
    const messageId = Date.now().toString();

    let activeChatId = chatId;
    
    // Nếu chưa có chatId (đang ở trạng thái chào mới) và người dùng bắt đầu chat
    if (!activeChatId && user && onAutoCreateChat) {
      activeChatId = await onAutoCreateChat();
    }
    
    const newUserMessage: Message = {
      id: messageId,
      role: "user",
      content: selectedImageFile
        ? `${originalPrompt}\n\n[Đã đính kèm ảnh - tính năng beta, OCR có thể sai]`
        : originalPrompt,
      isCompact: false
    };

    // Tạo danh sách tin nhắn mới nhất bao gồm tin nhắn vừa nhập
    const nextMessages: Message[] = [
      ...messages.map((msg) => ({ ...msg, isCompact: true })),
      newUserMessage
    ];
    
    // Cập nhật lên parent ngay lập tức (optimistic update)
    onMessagesChange?.(nextMessages);
    
    setInputValue("");

    try {
      if (selectedImageFile) {
        setIsLoading(true);
        setLoadingStage("Đang tải ảnh và đọc nội dung beta");
        const imageUrl = await uploadMultimodalImage(selectedImageFile);
        setLoadingStage("Đang chuyển ảnh thành yêu cầu tìm kiếm");
        prompt = await transformMultimodalPrompt(originalPrompt, imageUrl);
        clearSelectedImage();
      }

      // Truyền danh sách mới nhất vào hàm API để tránh bị mất tin nhắn khi AI trả lời
      callRestaurantApi(prompt, activeChatId ?? null, nextMessages);
    } catch (error: any) {
      setIsLoading(false);
      setChatError("MULTIMODAL", error?.message || "Không thể xử lý ảnh gửi kèm.");
      onMessagesChange?.([
        ...nextMessages,
        {
          id: `${messageId}-error`,
          role: "assistant",
          content: "Mình chưa xử lý được ảnh này. Bạn có thể thử ảnh rõ hơn hoặc gửi yêu cầu bằng chữ trước nhé.",
          restaurants: [],
          isCompact: false
        }
      ]);
    }
  };

  return (
    <div className="flex h-full flex-col gap-4 p-4 md:p-6">
      {/* Error Modal */}
      <AnimatePresence>
        {errorModal.open && (
          <motion.div
            key="error-backdrop"
            initial={false}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4 backdrop-blur-sm"
            onClick={(event) => {
              if (event.target === event.currentTarget) {
                setErrorModal((prev) => ({ ...prev, open: false }));
              }
            }}
          >
            <motion.div
              key="error-modal"
              initial={{ opacity: 0, y: 24, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 24, scale: 0.96 }}
              transition={{ duration: 0.28, ease: "easeOut" }}
              className="relative w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl"
            >
              <div className="flex items-start gap-4 px-6 py-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500 to-orange-500 shadow-md shadow-rose-200">
                  <AlertTriangle size={22} className="text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="text-base font-bold text-slate-900">
                    Có lỗi xảy ra
                  </h3>
                  <p className="mt-1 text-sm text-slate-600">
                    {errorModal.message}
                  </p>
                  <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-rose-200/70 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-600">
                    Mã lỗi: {errorModal.code}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setErrorModal((prev) => ({ ...prev, open: false }))
                  }
                  className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-100"
                >
                  <X size={16} />
                </button>
              </div>
              <div className="border-t border-slate-100 px-6 py-4">
                <button
                  type="button"
                  onClick={() =>
                    setErrorModal((prev) => ({ ...prev, open: false }))
                  }
                  className="w-full rounded-2xl bg-gradient-to-r from-brand-coral to-brand-flame py-3 text-sm font-semibold text-white shadow-glow transition hover:opacity-90"
                >
                  Đóng thông báo
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Login Prompt Modal */}
      <AuthPromptModal
        open={showLoginSuggestion}
        onClose={() => setShowLoginSuggestion(false)}
        title="Trải nghiệm tốt hơn khi đăng nhập"
        description="Đăng nhập để AI có thể tối ưu lộ trình theo sức khỏe của bạn, lưu lại các lịch trình yêu thích và nhiều đặc quyền khác!"
      />

      {/* AI Tips Card */}
      <div className="w-full rounded-2xl bg-gradient-to-r from-brand-coral via-brand-flame to-brand-lagoon p-[1px] shadow-glow">
        <div className="glass rounded-2xl px-4 py-2 flex flex-col sm:flex-row sm:items-center gap-2"> 
          {/* Dùng py-2 để giảm chiều cao, flex-row để đưa lên cùng một dòng trên màn hình máy tính */}
          
          <div className="flex shrink-0 items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-brand-flame">
            <Sparkles size={14} />
            <span>Lời khuyên của AI:</span>
          </div>
          
          <div className="text-xs text-slate-600 sm:truncate"> 
            {/* sm:truncate sẽ giúp chữ không bị xuống dòng trên màn hình lớn nếu bạn muốn cực kì gọn */}
            Càng chi tiết về món ăn, không gian & ngân sách, lộ trình BMI càng tối ưu.
          </div>
        </div>
      </div>

      {/* Chat Messages Container */}
      <div className="flex-1 overflow-y-auto space-y-3 md:space-y-4 pb-4">
        <AnimatePresence>
          {messages.length === 0 && !isLoading && (
            <motion.div
              key="welcome-message"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3 justify-start"
            >
              <div className="relative h-8 w-8 flex-shrink-0">
                <img
                  src="/assets/images/AI.png"
                  alt="AI Avatar"
                  className="h-full w-full rounded-full object-cover shadow-sm"
                  onError={(e) => {
                    e.currentTarget.classList.add('hidden');
                    e.currentTarget.nextElementSibling?.classList.remove('hidden');
                  }}
                />
                <div className="hidden h-full w-full flex items-center justify-center rounded-full bg-gradient-to-br from-brand-teal to-brand-lagoon text-[10px] font-bold text-white">
                  AI
                </div>
              </div>
              <div className="max-w-xs md:max-w-sm rounded-2xl px-4 py-3 text-xs md:text-sm shadow-soft glass text-slate-700">
                Chào bạn! Hãy cho BMI biết khẩu vị, ngân sách và phong cách bạn mong muốn.
              </div>
            </motion.div>
          )}

          {messages.map((message, index) => (
            <motion.div
              key={message.id || `msg-${index}`}
              layout
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -12, scale: 0.98 }}
              transition={{ duration: 0.3 }}
              className="space-y-2"
            >
              <div
                className={`flex gap-3 ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="relative h-8 w-8 flex-shrink-0">
                    <img
                      src="/assets/images/AI.png"
                      alt="AI Avatar"
                      className="h-full w-full rounded-full object-cover shadow-sm"
                      onError={(e) => {
                        e.currentTarget.classList.add('hidden');
                        e.currentTarget.nextElementSibling?.classList.remove('hidden');
                      }}
                    />
                    <div className="hidden h-full w-full flex items-center justify-center rounded-full bg-gradient-to-br from-brand-teal to-brand-lagoon text-[10px] font-bold text-white">
                      AI
                    </div>
                  </div>
                )}

                <motion.div
                  initial={{ scale: 1, opacity: 1 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.3 }}
                  className={`max-w-xs md:max-w-sm whitespace-pre-line rounded-2xl px-4 py-3 text-xs md:text-sm shadow-soft origin-bottom-left ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-brand-coral to-brand-flame text-white"
                      : "glass text-slate-700"
                  }`}
                >
                  {message.content}
                </motion.div>

                {message.role === "user" && (
                  <img
                    src={user?.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.displayName || "U")}&background=0f172a&color=fff`}
                    alt="User"
                    className="h-8 w-8 flex-shrink-0 rounded-full object-cover shadow-sm ring-1 ring-slate-100"
                  />
                )}
              </div>

              {/* Restaurant Names List */}
              {message.role === "assistant" &&
                message.restaurants &&
                message.restaurants.length > 0 && (
                  <motion.div
                    className="ml-11 flex flex-col gap-4 origin-top"
                    initial={{ scale: 1, opacity: 1 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.35 }}
                    style={{
                      transformOrigin: "top left",
                    }}
                  >
                    {message.restaurants.map((restaurant, restaurantIndex) => {
                      const itineraryItem = currentItinerary.find(item => item.id === restaurant.id);

                      return (
                        <motion.div
                          key={`${message.id}-${restaurant.id}-${restaurantIndex}`}
                          initial={{ opacity: 0, y: 12 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{
                            duration: 0.4,
                            delay: message.isCompact ? 0 : restaurantIndex * 0.1
                          }}
                          className="space-y-3"
                        >
                          <RestaurantMiniCard
                            restaurant={restaurant}
                            isInItinerary={Boolean(itineraryItem)}
                            currentMeal={itineraryItem?.meal}
                            occupiedMeals={currentItinerary.map(item => item.meal).filter(Boolean)}
                            onSelect={(id) => {
                              onRestaurantsSelect?.(message.restaurants || []);
                              onRestaurantSelect?.(id);
                            }}
                            onSelectMeal={onSelectMeal}
                          />
                        </motion.div>
                      );
                    })}
                  </motion.div>
                )}
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 text-xs md:text-sm text-slate-500"
          >
            <div className="relative h-8 w-8 flex-shrink-0">
              <img
                src="/assets/images/AI.png"
                alt="AI Avatar"
                className="h-full w-full rounded-full object-cover shadow-sm"
                onError={(e) => {
                  e.currentTarget.classList.add('hidden');
                  e.currentTarget.nextElementSibling?.classList.remove('hidden');
                }}
              />
              <div className="hidden h-full w-full flex items-center justify-center rounded-full bg-gradient-to-br from-brand-teal to-brand-lagoon text-[10px] font-bold text-white">
                AI
              </div>
            </div>
            <div className="glass min-w-0 max-w-[calc(100vw-5.5rem)] rounded-2xl px-4 py-3">
              <div className="flex min-w-0 items-center gap-2">
                <span className="min-w-0 truncate text-slate-600">{loadingStage}</span>
                <span className="flex shrink-0 items-center gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-coral" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-flame [animation-delay:120ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-lagoon [animation-delay:240ms]" />
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Suggestions */}
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => setInputValue(suggestion)}
              className="rounded-full border border-slate-200/60 bg-white/70 px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:text-slate-900"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {selectedImagePreview && (
        <div className="flex items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50/80 p-3 text-xs text-amber-800">
          <div className="h-14 w-14 shrink-0 overflow-hidden rounded-xl bg-white">
            <img
              src={selectedImagePreview}
              alt="Ảnh gửi kèm"
              className="h-full w-full object-cover"
            />
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-bold">Ảnh sẽ được phân tích ở chế độ beta</p>
            <p className="mt-0.5 text-amber-700">
              OCR/nhận diện món có thể sai nếu ảnh mờ hoặc menu khó đọc. Bạn vẫn cần nhập mô tả bằng chữ.
            </p>
          </div>
          <button
            type="button"
            onClick={clearSelectedImage}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-amber-700 shadow-sm transition hover:text-rose-600"
            disabled={isLoading}
          >
            <X size={15} />
          </button>
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-center gap-2 rounded-full border border-white/60 bg-white/80 px-3 py-2.5 shadow-soft backdrop-blur">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) handleImageSelect(file);
          }}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
          title="Đính kèm ảnh menu hoặc món ăn"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 transition hover:border-brand-coral hover:text-brand-coral disabled:cursor-not-allowed disabled:opacity-50"
        >
          <ImagePlus size={16} />
        </button>
        <input
          type="text"
          value={input}
          onChange={(event) => setInputValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleSend();
            }
          }}
          placeholder="Nhập yêu cầu của bạn..."
          className="flex-1 bg-transparent text-xs md:text-sm text-slate-700 outline-none placeholder:text-slate-400"
          disabled={isLoading}
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-r from-brand-coral to-brand-flame text-white shadow-glow disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          <SendHorizontal size={16} />
        </button>
      </div>
    </div>
  );
}

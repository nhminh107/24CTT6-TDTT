"use client";

import { useState } from "react";
import Link from "next/link";
import { Home, Plus, MessageSquare, LogOut, HeartPulse, User, Trash2, Compass } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { DashboardState } from "./MainDashboard";
import ConfirmModal from "@/components/ui/ConfirmModal";
import Toast, { ToastType } from "@/components/ui/Toast";

type ChatSession = {
  id: string;
  title: string;
  updated_at: string;
};

type SidebarNavProps = {
  state: DashboardState;
  onStateChange: (state: DashboardState) => void;
  availableFilters: string[];
  onOpenHealthProfile: () => void;
  onOpenProfileSettings: () => void;
  onOpenLocationPrompt?: () => void;
  onTabChange?: (tab: "itinerary" | "detail") => void;
  chatHistory?: ChatSession[];
  currentChatId?: string | null;
  onNewChat?: () => void;
  onChatSelect?: (id: string) => void;
  onDeleteChat?: (id: string) => void;
};

export default function SidebarNav({
  state,
  onStateChange,
  availableFilters,
  onOpenHealthProfile,
  onOpenProfileSettings,
  onOpenLocationPrompt,
  onTabChange,
  chatHistory = [],
  currentChatId,
  onNewChat,
  onChatSelect,
  onDeleteChat
}: SidebarNavProps) {
  const { user, logout } = useAuth();
  
  // Custom UI State
  const [deleteConfirm, setDeleteConfirm] = useState<{ isOpen: boolean; chatId: string }>({
    isOpen: false,
    chatId: ""
  });
  const [toast, setToast] = useState<{ show: boolean; type: ToastType; message: string }>({
    show: false,
    type: "success",
    message: ""
  });

  const handleDeleteClick = (e: React.MouseEvent, chatId: string) => {
    e.stopPropagation();
    setDeleteConfirm({ isOpen: true, chatId });
  };

  const handleConfirmDelete = () => {
    onDeleteChat?.(deleteConfirm.chatId);
    setToast({
      show: true,
      type: "success",
      message: "Đã xóa cuộc trò chuyện thành công"
    });
  };

  return (
    <>
      <div className="flex h-full flex-1 flex-col p-5">

        {/* ── 1. Action Buttons ─────────────────────────────── */}
        <button
          type="button"
          onClick={onNewChat}
          className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-coral to-brand-flame px-4 py-3 text-sm font-semibold text-white shadow-soft transition hover:opacity-90 hover:shadow-glow active:scale-[0.98]"
        >
          <Plus size={16} />
          Cuộc trò chuyện mới
        </button>

        <Link
          href="/"
          className="mt-3 flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white/80 px-4 py-2.5 text-xs font-semibold text-slate-600 shadow-sm transition hover:border-slate-300 hover:bg-white hover:text-slate-800 md:hidden"
        >
          <Home size={14} />
          Về trang chủ
        </Link>

        <Link
          href="/explore"
          className="mt-3 flex items-center justify-center gap-2 rounded-xl border border-brand-coral/20 bg-brand-coral/5 px-4 py-3 text-sm font-bold text-brand-coral shadow-sm transition hover:bg-brand-coral/10 hover:shadow-md active:scale-[0.98]"
        >
          <Compass size={16} />
          Bản đồ khám phá
        </Link>

        {/* ── 2. User & Location ───────────────────────────────── */}
        <div className="mt-4">
          <div className="rounded-2xl border border-slate-200/60 bg-white/60 p-4 shadow-sm backdrop-blur-sm">
            {user ? (
              <>
                <div className="flex items-center gap-3">
                  <img
                    src={
                      user.photoURL ||
                      `https://ui-avatars.com/api/?name=${encodeURIComponent(
                        user.displayName || "U"
                      )}&background=ff6b4a&color=fff`
                    }
                    alt="Avatar"
                    className="h-10 w-10 shrink-0 rounded-full object-cover ring-2 ring-brand-coral/25"
                    onError={(e) =>
                      (e.currentTarget.src =
                        "https://ui-avatars.com/api/?name=U&background=ff6b4a&color=fff")
                    }
                  />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-slate-800">
                      {user.displayName || "Người dùng"}
                    </p>
                    <p className="truncate text-[11px] text-slate-400">{user.email}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => logout()}
                    title="Đăng xuất"
                    className="rounded-lg p-1.5 text-slate-300 transition hover:bg-red-50 hover:text-red-400"
                  >
                    <LogOut size={15} />
                  </button>
                </div>

                <div className="mt-3 h-px bg-slate-100" />

                <button
                  type="button"
                  onClick={onOpenHealthProfile}
                  className="mt-3 flex w-full items-center gap-2.5 rounded-xl border border-slate-100 bg-slate-50/80 px-3 py-2.5 text-xs font-semibold text-slate-500 transition hover:border-orange-200 hover:bg-orange-50 hover:text-orange-500"
                >
                  <HeartPulse size={14} />
                  Hồ sơ sức khỏe
                  <span className="ml-auto text-slate-300">›</span>
                </button>

                <button
                  type="button"
                  onClick={onOpenProfileSettings}
                  className="mt-3 flex w-full items-center gap-2.5 rounded-xl border border-slate-100 bg-white px-3 py-2.5 text-xs font-semibold text-slate-500 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-700"
                >
                  <User size={14} />
                  Cài đặt hồ sơ
                  <span className="ml-auto text-slate-300">›</span>
                </button>
              </>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100">
                    <User size={17} className="text-slate-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-700">Chưa đăng nhập</p>
                    <p className="text-[11px] leading-relaxed text-slate-400">
                      Lưu hồ sơ sức khỏe &amp; lịch sử chat
                    </p>
                  </div>
                </div>

                <a
                  href="/login"
                  className="mt-3 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-coral to-brand-flame px-3 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:opacity-90 hover:shadow-glow"
                >
                  Đăng nhập ngay
                </a>
              </>
            )}

            <div className="mt-3">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                  Vị trí xuất phát
                </span>
                <button
                  type="button"
                  onClick={() => onOpenLocationPrompt?.()}
                  className="text-[10px] font-bold uppercase tracking-[0.1em] text-brand-coral transition-colors hover:text-brand-flame hover:underline"
                >
                  Thay đổi
                </button>
              </div>
              <p className="truncate text-sm font-semibold text-slate-700">
                {state.location || "Chưa xác định"}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-5 h-px bg-slate-200/50" />

        {/* ── 4. Chat History ───────────────────────────────── */}
        {user && (
          <div className="mt-4 flex min-h-0 flex-1 flex-col">
            <p className="mb-2.5 text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
              Lịch sử chat
            </p>
            <div className="flex-1 space-y-1 overflow-y-auto">
              {chatHistory.length === 0 ? (
                <p className="py-6 text-center text-xs text-slate-300">Chưa có cuộc trò chuyện nào</p>
              ) : (
                chatHistory.map((chat) => (
                  <button
                    key={chat.id}
                    type="button"
                    onClick={() => onChatSelect?.(chat.id)}
                    className={`group flex w-full items-start gap-2.5 rounded-xl border px-3 py-2.5 text-left transition ${
                      currentChatId === chat.id
                        ? "border-brand-coral/20 bg-brand-coral/5"
                        : "border-transparent hover:border-slate-200/60 hover:bg-white/70"
                    }`}
                  >
                    <MessageSquare
                      size={13}
                      className={`mt-0.5 shrink-0 transition ${
                        currentChatId === chat.id ? "text-brand-coral" : "text-slate-300 group-hover:text-brand-coral"
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className={`truncate text-xs font-medium transition ${
                          currentChatId === chat.id ? "text-brand-coral" : "text-slate-600 group-hover:text-slate-800"
                        }`}>
                          {chat.title}
                        </p>
                        <button
                          onClick={(e) => handleDeleteClick(e, chat.id)}
                          className={`shrink-0 rounded-md p-1 transition-colors hover:bg-red-50 hover:text-red-500 ${
                            currentChatId === chat.id ? "text-slate-400" : "text-transparent group-hover:text-slate-300"
                          }`}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                      <p className="mt-0.5 text-[10px] text-slate-300">
                        {new Date(chat.updated_at).toLocaleDateString("vi-VN")}
                      </p>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        )}

      </div>

      <ConfirmModal 
        isOpen={deleteConfirm.isOpen}
        title="Xác nhận xóa?"
        message="Bạn sẽ không thể khôi phục lại cuộc trò chuyện này sau khi xóa."
        confirmText="Xóa vĩnh viễn"
        cancelText="Để sau"
        onConfirm={handleConfirmDelete}
        onClose={() => setDeleteConfirm({ isOpen: false, chatId: "" })}
      />

      <Toast 
        show={toast.show}
        type={toast.type}
        message={toast.message}
        position="bottom-left"
        onClose={() => setToast(prev => ({ ...prev, show: false }))}
      />
    </>
  );
}

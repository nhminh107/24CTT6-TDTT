"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, AlertCircle, Info, Loader2, X } from "lucide-react";

export type ToastType = "success" | "error" | "info" | "loading";

interface ToastProps {
  show: boolean;
  type: ToastType;
  message: string;
  duration?: number;
  onClose: () => void;
  position?: "bottom" | "center" | "top" | "bottom-left";
}

export default function Toast({ show, type, message, duration = 3000, onClose, position = "top" }: ToastProps) {
  useEffect(() => {
    if (show && type !== "loading" && duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [show, type, duration, onClose]);

  const icons = {
    success: <CheckCircle2 className="text-emerald-500" size={20} />,
    error: <AlertCircle className="text-rose-500" size={20} />,
    info: <Info className="text-brand-lagoon" size={20} />,
    loading: <Loader2 className="animate-spin text-brand-flame" size={20} />,
  };

  const backgrounds = {
    success: "bg-white/95 border-emerald-100",
    error: "bg-white/95 border-rose-100",
    info: "bg-white/95 border-blue-100",
    loading: "bg-white/95 border-slate-100",
  };

  const getPositionClasses = () => {
    switch (position) {
      case "center": return "items-center justify-center";
      case "bottom": return "items-end justify-center pb-12";
      case "bottom-left": return "items-end justify-start pl-8 pb-8";
      case "top": return "items-start justify-center pt-24";
      default: return "items-start justify-center pt-24";
    }
  };

  return (
    <AnimatePresence>
      {show && (
        <div className={`fixed inset-0 z-[300] flex ${getPositionClasses()} pointer-events-none`}>
          <motion.div
            initial={{ 
              opacity: 0, 
              scale: 0.9, 
              y: (position === 'top' || position === 'bottom-left') ? -20 : 20 
            }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ 
              opacity: 0, 
              scale: 0.9, 
              y: (position === 'top' || position === 'bottom-left') ? -20 : 20 
            }}
            className={`pointer-events-auto flex items-center gap-3 rounded-[24px] border px-6 py-4 shadow-2xl backdrop-blur-xl ${backgrounds[type]}`}
          >
            <div className="flex-shrink-0">{icons[type]}</div>
            <p className="text-sm font-bold text-slate-800 whitespace-nowrap">
              {message}
            </p>
            {type !== "loading" && (
              <button
                onClick={onClose}
                className="ml-2 rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
              >
                <X size={16} />
              </button>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

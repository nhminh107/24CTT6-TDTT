"use client";

import { useState } from "react";
import { X, MapPin, LocateFixed, Loader2, ArrowRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import LocationSearch from "./LocationSearch";
import Swal from "sweetalert2";

type InitialLocationModalProps = {
  isOpen: boolean;
  onClose: (location?: string, placeId?: string) => void;
};

export default function InitialLocationModal({ isOpen, onClose }: InitialLocationModalProps) {
  const [location, setLocation] = useState("");
  const [placeId, setPlaceId] = useState("");
  const [isLocating, setIsLocating] = useState(false);

  const handleGetCurrentLocation = (isAutomatic = false) => {
    if (!navigator.geolocation) {
      if (!isAutomatic) {
        Swal.fire({
          icon: 'error',
          title: 'Lỗi',
          text: 'Trình duyệt không hỗ trợ định vị.',
        });
      }
      onClose();
      return;
    }

    setIsLocating(true);

    // Thông báo nếu là tự động lấy vị trí
    let autoSwal: any = null;
    if (isAutomatic) {
      autoSwal = Swal.fire({
        title: 'Đang lấy vị trí...',
        text: 'Vui lòng chờ trong giây lát',
        allowOutsideClick: false,
        didOpen: () => {
          Swal.showLoading();
        }
      });
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const displayName = "Vị trí hiện tại";
          const id = `geo_${latitude}_${longitude}`;

          if (autoSwal) {
            Swal.close();
            await Swal.fire({
              icon: 'success',
              title: 'Đã lấy vị trí hiện tại',
              text: `Đã xác định vị trí của bạn qua GPS`,
              timer: 1500,
              showConfirmButton: false
            });
          } else {
            Swal.fire({
              icon: 'success',
              title: 'Thành công',
              text: `Đã xác định vị trí của bạn qua GPS`,
              timer: 1500,
              showConfirmButton: false
            });
          }

          onClose(displayName, id);
        } catch (error) {

          if (autoSwal) Swal.close();
          onClose();
        } finally {
          setIsLocating(false);
        }
      },
      (err) => {
        setIsLocating(false);
        if (autoSwal) {
          Swal.close();
          Swal.fire({
            icon: 'info',
            title: 'Không lấy được vị trí',
            text: 'Bạn có thể tự nhập vị trí sau trên thanh tìm kiếm.',
            timer: 2000,
            showConfirmButton: false
          });
        } else {
          Swal.fire({
            icon: 'error',
            title: 'Lỗi định vị',
            text: 'Không thể lấy vị trí hiện tại của bạn. Vui lòng kiểm tra quyền truy cập vị trí.',
          });
        }
        onClose();
      },
      { timeout: 8000 }
    );
  };

  const handleContinue = () => {
    if (location) {
      onClose(location, placeId);
    } else {
      handleGetCurrentLocation(true);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative w-full max-w-lg rounded-[32px] bg-white p-8 shadow-2xl"
        >
          <button
            onClick={() => handleContinue()}
            disabled={isLocating}
            className="absolute right-6 top-6 rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600 disabled:opacity-30"
          >
            <X size={20} />
          </button>

          <div className="mb-8 flex flex-col items-center text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-coral/10 text-brand-coral shadow-inner">
              <MapPin size={32} />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">Bắt đầu hành trình</h2>
            <p className="mt-2 text-slate-500">
              Bạn muốn khám phá ẩm thực ở khu vực nào hôm nay?
            </p>
          </div>

          <div className="space-y-6">
            <div className="relative">
              <label className="mb-2 block text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                Nhập địa điểm hoặc thành phố
              </label>
              <LocationSearch
                value={location}
                onChange={(val) => setLocation(val)}
                onSelect={(opt) => {
                  setLocation(opt.name);
                  setPlaceId(opt.id);
                }}
              />
            </div>

            <div className="flex flex-col gap-3">
              {location ? (
                <button
                  onClick={handleContinue}
                  disabled={isLocating}
                  className="group flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-coral to-brand-flame py-4 font-bold text-white shadow-glow transition hover:opacity-95 active:scale-[0.98] disabled:opacity-50"
                >
                  {isLocating ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      Tiếp tục
                      <ArrowRight size={20} className="transition-transform group-hover:translate-x-1" />
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={() => handleGetCurrentLocation(false)}
                  disabled={isLocating}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-coral to-brand-flame py-4 font-bold text-white shadow-glow transition hover:opacity-95 active:scale-[0.98] disabled:opacity-50"
                >
                  {isLocating ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      Đang xử lý...
                    </>
                  ) : (
                    <>
                      <LocateFixed size={18} />
                      Sử dụng vị trí hiện tại
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
          
          <p className="mt-8 text-center text-[11px] leading-relaxed text-slate-400">
            * Chúng tôi sử dụng vị trí để gợi ý các quán ăn gần bạn nhất.<br/>
            Bạn có thể thay đổi vị trí này bất cứ lúc nào ở thanh bên.
          </p>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

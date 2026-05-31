import React, { useState, useCallback } from "react";
// 1. Nhớ import STEPS và Step type từ file AdaptiveInputBar của bạn
import AdaptiveInputBar, { STEPS, Step } from "./AdaptiveInputBar";

export function AdaptiveInputBarDemo() {
  const [step, setStep] = useState<Step>(STEPS.STEP_LOCATION);
  // data sẽ lưu trữ toàn bộ thông tin thu thập được từ các bước
  const [data, setData] = useState<Record<string, any>>({});

  // Chuyển object STEPS thành mảng để tính toán thứ tự next step
  const stepOrder = Object.values(STEPS) as Step[];

  // Cập nhật dữ liệu từ các component con
  const handleUpdate = useCallback((update: Record<string, any>) => {
    setData(prev => ({ ...prev, ...update }));
  }, []);

  // Chuyển bước logic
  const handleNext = useCallback((targetStep?: Step) => {
    if (targetStep) {
      setStep(targetStep);
    } else {
      setStep(prev => {
        const idx = stepOrder.indexOf(prev);
        // Nếu là bước cuối cùng (CHAT_FREE) thì giữ nguyên, không loop lại
        if (idx === stepOrder.length - 1) return prev;
        return stepOrder[idx + 1];
      });
    }
  }, [stepOrder]);

  return (
    <div className="min-h-screen bg-slate-50 p-8 flex flex-col items-center gap-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-800">Demo Adaptive Input Bar</h1>
        <p className="text-slate-500 text-sm">Kiểm tra luồng thu thập dữ liệu JSON</p>
      </div>

      {/* 2. Phần xem trước dữ liệu (Debug Preview) */}
      <div className="w-full max-w-2xl bg-slate-900 rounded-2xl p-4 shadow-xl">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-orange-400 uppercase tracking-widest">Current Session JSON</span>
          <span className="text-xs text-slate-500">Step: {step}</span>
        </div>
        <pre className="text-green-400 font-mono text-sm overflow-auto max-h-40 p-2">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>

      {/* 3. Component chính cần test */}
      <div className="w-full max-w-2xl mt-4">
        <AdaptiveInputBar 
          currentStep={step} 
          onUpdate={handleUpdate} 
          onNext={handleNext} 
        />
      </div>

      {/* Nút Reset để test lại từ đầu */}
      <button 
        onClick={() => { setStep(STEPS.STEP_LOCATION); setData({}); }}
        className="mt-4 text-sm text-slate-400 hover:text-orange-500 underline underline-offset-4"
      >
        Làm mới quá trình nhập (Reset)
      </button>
    </div>
  );
}
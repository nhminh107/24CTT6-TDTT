"use client";

import { useState } from "react";
import { auth } from "@/lib/firebase";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup,
  updateProfile,
} from "firebase/auth";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { MapPin, Mail, Lock, User, ArrowRight, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isLogin) {
        await signInWithEmailAndPassword(auth, email, password);
      } else {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(userCredential.user, { displayName: name });
      }
      router.push("/app");
    } catch (error: any) {
      alert("Lỗi: " + (error.code === 'auth/user-not-found' ? 'Tài khoản không tồn tại' : error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    const provider = new GoogleAuthProvider();
    setLoading(true);
    try {
      await signInWithPopup(auth, provider);
      router.push("/app");
    } catch (error: any) {
      alert("Lỗi Google Auth: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center justify-center text-center">
          <Link href="/" className="mb-4 flex items-center gap-2">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-coral to-brand-flame text-white shadow-glow">
              <MapPin size={24} />
            </span>
            <div className="flex flex-col text-left leading-tight">
              <span className="font-display text-2xl font-bold tracking-tight text-slate-900">
                BMI
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                Bite Mapping Intelligent
              </span>
            </div>
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">
            {isLogin ? "Chào mừng trở lại" : "Tạo tài khoản mới"}
          </h1>
          <p className="mt-2 text-slate-500">
            {isLogin 
              ? "Đăng nhập để tiếp tục tối ưu hành trình của bạn" 
              : "Bắt đầu khám phá những trải nghiệm ẩm thực tuyệt vời"}
          </p>
        </div>

        <div className="rounded-2xl bg-white p-8 shadow-xl shadow-slate-200/50">
          <form className="space-y-4" onSubmit={handleAuth}>
            {!isLogin && (
              <div className="space-y-1">
                <label className="text-sm font-medium text-slate-700">Họ và tên</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                  <input
                    type="text"
                    placeholder="Nguyễn Văn A"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 transition focus:border-brand-coral focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-coral/10"
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="email"
                  placeholder="name@example.com"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 transition focus:border-brand-coral focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-coral/10"
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-slate-700">Mật khẩu</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input
                  type="password"
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-4 transition focus:border-brand-coral focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-coral/10"
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button 
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-coral to-brand-flame py-3 font-semibold text-white shadow-glow transition hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-70"
            >
              {loading ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <>
                  {isLogin ? "Đăng nhập" : "Đăng ký"}
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          <div className="relative my-8 flex items-center">
            <div className="flex-grow border-t border-slate-100"></div>
            <span className="mx-4 flex-shrink text-xs font-medium uppercase tracking-wider text-slate-400">Hoặc</span>
            <div className="flex-grow border-t border-slate-100"></div>
          </div>

          <button 
            onClick={handleGoogleLogin}
            disabled={loading}
            className="flex w-full items-center justify-center gap-3 rounded-xl border border-slate-200 bg-white py-3 font-medium text-slate-700 transition hover:bg-slate-50 active:bg-slate-100 disabled:opacity-70"
          >
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width={20} alt="Google" />
            Đăng nhập bằng Google
          </button>
        </div>

        <p className="mt-8 text-center text-sm text-slate-600">
          {isLogin ? "Chưa có tài khoản?" : "Đã có tài khoản?"}{" "}
          <button 
            onClick={() => setIsLogin(!isLogin)}
            className="font-semibold text-brand-coral hover:text-brand-flame transition"
          >
            {isLogin ? "Đăng ký ngay" : "Đăng nhập ngay"}
          </button>
        </p>
      </motion.div>
    </div>
  );
}

"use client";

import { useAuth } from "@/context/AuthContext";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";

export default function AuthWrapper({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Nếu không loading và không có user, chuyển hướng về login
    // Chỉ áp dụng cho các route bảo mật (ví dụ /app)
    if (!loading && !user && pathname.startsWith("/app")) {
      router.push(`/login?redirect=${pathname}`);
    }
  }, [user, loading, router, pathname]);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-coral border-t-transparent"></div>
      </div>
    );
  }

  // Nếu là route /app và chưa login, không render children để tránh flash nội dung
  if (!user && pathname.startsWith("/app")) {
    return null;
  }

  return <>{children}</>;
}

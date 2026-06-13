import "./globals.css";
import type { Metadata } from "next";
import { AuthProvider } from "@/context/AuthContext";
import AuthWrapper from "@/components/layout/AuthWrapper";

export const metadata: Metadata = {
  title: "BMI | Tối ưu hóa lịch trình ẩm thực",
  description:
    "Bite Mapping Intelligent - Nền tảng AI giúp tối ưu lộ trình ẩm thực theo vị trí, ngân sách và khẩu vị của bạn.",
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body className="font-sans antialiased">
        <AuthProvider>
          <AuthWrapper>
            {children}
          </AuthWrapper>
        </AuthProvider>
      </body>
    </html>
  );
}

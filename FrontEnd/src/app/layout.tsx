import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "RouteAI | Tối ưu hóa lịch trình ẩm thực",
  description:
    "Nền tảng AI giúp tối ưu lộ trình ẩm thực theo vị trí, ngân sách và khẩu vị của bạn.",
  icons: [{ rel: "icon", url: "/favicon.ico" }]
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}

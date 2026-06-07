import MapExplore from "@/components/ui/MapExplore";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Khám phá bản đồ | Trợ lý du lịch thông minh",
  description: "Xem toàn bộ các quán ăn trên bản đồ số sử dụng Goong Maps.",
};

export default function ExplorePage() {
  return (
    <main className="w-full h-screen overflow-hidden">
      <MapExplore />
    </main>
  );
}

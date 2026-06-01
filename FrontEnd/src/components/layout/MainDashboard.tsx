"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ArrowLeft, CalendarCheck, Menu, X } from "lucide-react";
import SidebarNav from "./SidebarNav";
import ChatInterface from "@/components/sections/ChatInterface";
import ProfileSettings from "@/components/sections/ProfileSettings";
import HealthProfileModal, { HealthProfile } from "@/components/ui/HealthProfileModal";
import ItineraryPanel from "./ItineraryPanel";
import RestaurantCard from "@/components/ui/RestaurantCard";

type Restaurant = {
  id: string;
  name: string;
  address: string;
  rating: number;
  price: string | number;
  phone: string | number;
  mapUrl: string;
  imageUrl: string;
  semanticText: string;
  meals?: string[];
  healthTagsDisplay?: {
    warnings?: string[];
    notes?: string[];
  };
};

export type DashboardState = {
  location: string;
  placeId: string;
  budget: string;
  filters: string[];
  selectedRestaurants: Restaurant[];
};

const filters = ["Lãng mạn", "Cay", "Hải sản", "View biển", "Chay", "Gia đình"];

const DEFAULT_HEALTH_PROFILE: HealthProfile = {
  selected_conditions: [],
  selected_allergies: [],
  diet_mode: "casual",
  more_descriptions: ""
};

export default function MainDashboard() {
  const { user } = useAuth();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [mobileItineraryOpen, setMobileItineraryOpen] = useState(false);
  const [restaurantModalOpen, setRestaurantModalOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    location: "",
    placeId: "",
    budget: "",
    filters: [],
    selectedRestaurants: []
  });
  const [healthOpen, setHealthOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [selectedRestaurantId, setSelectedRestaurantId] = useState<string | null>(null);
  const [itineraryTab, setItineraryTab] = useState<"itinerary" | "detail">("itinerary");
  const [healthProfile, setHealthProfile] = useState<HealthProfile>(DEFAULT_HEALTH_PROFILE);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mediaQuery = window.matchMedia("(max-width: 767px)");
    const handleChange = (event: MediaQueryListEvent) => {
      setIsMobile(event.matches);
    };
    setIsMobile(mediaQuery.matches);
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const budgetDisplay = useMemo(() => {
    const amount = Number(dashboardState.budget);
    if (!amount || Number.isNaN(amount)) {
      return "Chưa nhập";
    }
    return `${amount.toLocaleString("vi-VN")} VNĐ`;
  }, [dashboardState.budget]);

  const mealTimes = ["07:30", "12:15", "19:30", "21:00"];
  const mealTypes = ["Cafe", "Bistro", "Fine Dining", "Street Food"];

  const getTravelTime = () => `${Math.floor(10 + Math.random() * 11)}p`;

  const buildMealStops = (restaurants: Restaurant[]) =>
    restaurants.slice(0, 3).map((restaurant, index) => {
      const label = `STOP ${String(index + 1).padStart(2, "0")}`;
      const priceText =
        typeof restaurant.price === "number"
          ? `${restaurant.price.toLocaleString("vi-VN")}đ`
          : restaurant.price || "Chưa cập nhật";
      const type = restaurant.meals?.[0]?.trim() || mealTypes[index] || "Cafe";
      return {
        label,
        name: restaurant.name || "Chưa có dữ liệu",
        time: getTravelTime(),
        price: priceText,
        type,
        rating: restaurant.rating ?? 0
      };
    });

  const mealStops = useMemo(
    () => buildMealStops(dashboardState.selectedRestaurants),
    [dashboardState.selectedRestaurants]
  );

  const selectedRestaurant = useMemo(
    () =>
      dashboardState.selectedRestaurants.find((restaurant) => restaurant.id === selectedRestaurantId) ||
      null,
    [dashboardState.selectedRestaurants, selectedRestaurantId]
  );

  const itineraryCount = dashboardState.selectedRestaurants.length;

  const handleSidebarToggle = () => {
    if (isMobile) {
      setMobileSidebarOpen((prev) => !prev);
      return;
    }
    setSidebarOpen((prev) => !prev);
  };

  const handleRestaurantSelect = (restaurantId: string) => {
    setSelectedRestaurantId(restaurantId);
    setItineraryTab("detail");
    if (isMobile) {
      setRestaurantModalOpen(true);
      setMobileItineraryOpen(false);
    }
  };

  const handleCloseDetail = () => {
    setSelectedRestaurantId(null);
    setItineraryTab("itinerary");
    setRestaurantModalOpen(false);
  };

  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000";

  const fetchHealthProfile = async () => {
    if (!user?.uid) return;
    try {
      const response = await fetch(`${API_BASE_URL}/api/user/health-profile/${user.uid}`);
      if (!response.ok) throw new Error("Failed to fetch profile");
      const data = await response.json();
      setHealthProfile({
        selected_conditions: data.raw_selections?.selected_conditions || [],
        selected_allergies: data.raw_selections?.selected_allergies || [],
        diet_mode: data.diet_mode || "casual",
        more_descriptions: data.more_description || ""
      });
    } catch (error) {
      console.error(error);
    }
  };

  const handleHealthOpen = async () => {
    if (!user?.uid) {
      router.push("/login");
      return;
    }
    await fetchHealthProfile();
    setHealthOpen(true);
  };

  const handleProfileOpen = () => {
    if (!user?.uid) {
      router.push("/login");
      return;
    }
    setProfileOpen(true);
  };

  const handleHealthProfileSave = async (profile: HealthProfile) => {
    if (!user?.uid) return;
    setHealthProfile(profile);
    try {
      const response = await fetch(`${API_BASE_URL}/api/user/health-profile/${user.uid}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.uid,
          diet_mode: profile.diet_mode,
          selected_conditions: profile.selected_conditions,
          selected_allergies: profile.selected_allergies,
          more_descriptions: profile.more_descriptions
        })
      });
      if (!response.ok) throw new Error("Failed to save profile");
    } catch (error) {
      console.error(error);
      throw error;
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-white">
      {/* Top Navigation */}
      <nav className="relative flex items-center justify-between border-b border-slate-200/60 bg-white/70 px-6 py-3 backdrop-blur">
      {/* Khối bên trái: Nút Menu và Quay lại */}
      <div className="z-10 flex items-center gap-4">
        <button
          type="button"
          onClick={handleSidebarToggle}
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition hover:bg-slate-100"
        >
          {(isMobile ? mobileSidebarOpen : sidebarOpen) ? <X size={20} /> : <Menu size={20} />}
        </button>
        <Link
          href="/"
          className="hidden items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 md:flex"
        >
          <ArrowLeft size={16} />
          Quay lại trang chính
        </Link>
      </div>

      {/* Khối ở giữa: Logo BMI (Căn giữa tuyệt đối dựa trên toàn bộ chiều rộng nav) */}
      <div className="absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center leading-tight text-center pointer-events-none">
        <span className="text-lg font-semibold text-slate-900">BMI</span>
        <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500 whitespace-nowrap">
          Bite Mapping Intelligent
        </span>
      </div>

      {/* Khối bên phải: Để trống nhưng giữ z-10 nếu sau này bạn có thêm nút Avatar/User */}
      <div className="z-10 w-10 md:w-40" /> 
    </nav>

      {/* Main Content Container */}
      <div className="flex h-[calc(100vh-73px)] w-full overflow-hidden">
        {/* Left Sidebar */}
        <aside
          className={
            isMobile
              ? `fixed inset-0 z-40 w-full overflow-y-auto bg-white/95 backdrop-blur transition-transform duration-300 ease-out ${
                  mobileSidebarOpen ? "translate-x-0" : "-translate-x-full"
                }`
              : `${
                  sidebarOpen ? "w-90" : "w-0"
                } overflow-y-auto border-r border-slate-200/60 bg-white/70 backdrop-blur transition-all duration-300 ease-out`
          }
        >
          {isMobile && (
            <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200/60 bg-white/90 px-5 py-4 backdrop-blur md:hidden">
              <span className="text-sm font-semibold text-slate-900">Menu</span>
              <button
                type="button"
                onClick={() => setMobileSidebarOpen(false)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={18} />
              </button>
            </div>
          )}
          <SidebarNav
            state={dashboardState}
            onStateChange={setDashboardState}
            availableFilters={filters}
            onOpenHealthProfile={handleHealthOpen}
            onOpenProfileSettings={handleProfileOpen}
          />
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 overflow-y-auto bg-white/70">
          <ChatInterface
            placeId={dashboardState.placeId}
            onRestaurantsSelect={(restaurants) => {
              setDashboardState((prev) => ({
                ...prev,
                selectedRestaurants: restaurants
              }));
            }}
            onRestaurantSelect={handleRestaurantSelect}
          />
        </main>

        {/* Right Itinerary Panel */}
        <aside 
          className={`hidden overflow-y-auto border-l border-slate-200/60 bg-white/70 backdrop-blur lg:block transition-all duration-300
            ${selectedRestaurantId ? 'w-[450px]' : 'w-80'}`}
        >
          <ItineraryPanel
            location={dashboardState.location}
            budget={budgetDisplay}
            mealStops={mealStops}
            restaurants={dashboardState.selectedRestaurants}
            selectedRestaurantId={selectedRestaurantId}
            currentTab={itineraryTab}
            onSelectRestaurant={handleRestaurantSelect}
            onTabChange={setItineraryTab}
            onCloseDetail={handleCloseDetail}
          />
        </aside>
      </div>

      {!mobileItineraryOpen && (
        <button
          type="button"
          onClick={() => {
            setItineraryTab("itinerary");
            setMobileItineraryOpen(true);
          }}
          className="fixed bottom-24 right-4 z-30 inline-flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-brand-teal to-brand-lagoon text-white shadow-glow transition hover:scale-105 md:hidden"
        >
          <span className="relative">
            <CalendarCheck size={20} />
            {itineraryCount > 0 && (
              <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-brand-coral text-[10px] font-semibold text-white shadow">
                {itineraryCount > 9 ? "9+" : itineraryCount}
              </span>
            )}
          </span>
        </button>
      )}

      {mobileItineraryOpen && (
        <div className="fixed inset-0 z-40 flex flex-col bg-white/95 backdrop-blur md:hidden">
          <div className="flex items-center justify-between border-b border-slate-200/60 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-slate-900">Lịch trình</p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-400">
                Tổng hợp
              </p>
            </div>
            <button
              type="button"
              onClick={() => setMobileItineraryOpen(false)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
            >
              <X size={18} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <ItineraryPanel
              location={dashboardState.location}
              budget={budgetDisplay}
              mealStops={mealStops}
              restaurants={dashboardState.selectedRestaurants}
              selectedRestaurantId={selectedRestaurantId}
              currentTab={itineraryTab}
              onSelectRestaurant={handleRestaurantSelect}
              onTabChange={setItineraryTab}
              onCloseDetail={handleCloseDetail}
            />
          </div>
        </div>
      )}

      <HealthProfileModal
        open={healthOpen}
        onClose={() => setHealthOpen(false)}
        profile={healthProfile}
        onChange={handleHealthProfileSave}
      />

      {restaurantModalOpen && selectedRestaurant && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-3 backdrop-blur-sm md:hidden">
          <div className="relative w-full max-w-md overflow-hidden rounded-[28px] bg-white shadow-2xl">
            <button
              type="button"
              onClick={handleCloseDetail}
              className="absolute right-3 top-3 z-10 inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/90 text-slate-500 shadow-sm transition hover:bg-slate-100 hover:text-slate-900"
            >
              <X size={16} />
            </button>
            <div className="max-h-[85vh] overflow-y-auto p-3">
              <RestaurantCard restaurant={selectedRestaurant} />
            </div>
          </div>
        </div>
      )}

      {profileOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 backdrop-blur-sm">
          <div className="relative w-full max-w-4xl h-full overflow-y-auto rounded-[32px] bg-white shadow-2xl sm:h-[90vh]">
            <button
              type="button"
              onClick={() => setProfileOpen(false)}
              className="absolute right-4 top-4 z-10 inline-flex h-10 w-10 items-center justify-center rounded-full bg-white text-slate-500 shadow-sm transition hover:bg-slate-100 hover:text-slate-900"
            >
              <X size={20} />
            </button>
            <div className="min-h-full px-4 py-6 sm:px-6 sm:py-8">
              <ProfileSettings />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

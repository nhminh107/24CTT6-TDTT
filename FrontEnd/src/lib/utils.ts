export function cn(...classes: Array<string | undefined | false | null>) {
  return classes.filter(Boolean).join(" ");
}

export type Restaurant = {
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
  meal?: string; // Added to support itinerary display
  assignedMeal?: string;
  lat?: number;
  lng?: number;
  healthTagsDisplay?: {
    warnings?: string[];
    notes?: string[];
  };
  warnings?: string[];
  notes?: string[];
  source?: "user" | "ai";
};

export type ApiRestaurant = {
  id?: string;
  name?: string;
  address?: string;
  star?: number;
  avg_price?: number;
  phone_num?: string | number;
  image_url?: string;
  semantic_text?: string;
  meals?: string[];
  meal?: string;
  assigned_meal?: string;
  main_tag?: string[];
  potential_tag?: string[];
  warnings?: string[];
  notes?: string[];
  type?: string[];
  lat?: number;
  lng?: number;
};

export function convertToGeoJSON(restaurants: ApiRestaurant[]) {
  const getStyle = (res: ApiRestaurant) => {
    const name = (res.name || "").toLowerCase();
    const typeStr = (res.type || []).join(" ").toLowerCase();

    // 1. Check Name first (very specific)
    if (name.includes("phở") || name.includes("bún") || name.includes("mỳ") || name.includes("mì") || name.includes("hủ tiếu") || name.includes("bánh canh")) {
      return { icon: "soup", color: "#EA4335" }; // Đỏ (Món sợi Việt)
    }
    if (name.includes("hải sản") || name.includes("ốc") || name.includes("seafood") || name.includes("ghẹ") || name.includes("tôm") || name.includes("cua") || name.includes("cá") || name.includes("snails") || name.includes("sò") || name.includes("hàu") || name.includes("mực")) {
      return { icon: "fish", color: "#00BCD4" }; // Xanh biển (Hải sản)
    }
    if (name.includes("cơm") || name.includes("rice")) {
      return { icon: "utensils", color: "#FF9800" }; // Cam (Cơm)
    }
    if (name.includes("lẩu") || name.includes("hotpot") || name.includes("canh")) {
      return { icon: "soup", color: "#E91E63" }; // Hồng (Lẩu/Canh)
    }
    if (name.includes("nướng") || name.includes("bbq") || name.includes("steak") || name.includes("steakhouse") || name.includes("sườn")) {
      return { icon: "flame", color: "#D32F2F" }; // Đỏ sẫm (Nướng)
    }
    if (name.includes("bánh mì") || name.includes("banh mi")) {
      return { icon: "utensils", color: "#FFB300" }; // Vàng (Bánh mì)
    }
    if (name.includes("pizza")) {
      return { icon: "pizza", color: "#FF9800" }; // Cam (Pizza)
    }
    if (name.includes("sushi") || name.includes("sashimi")) {
      return { icon: "fish", color: "#FF9800" }; // Cam (Sushi/Nhật)
    }
    if (name.includes("chè") || name.includes("kem") || name.includes("ice cream") || name.includes("gelato")) {
      return { icon: "cake", color: "#EC407A" }; // Hồng nhạt (Tráng miệng)
    }
    if (name.includes("trà sữa") || name.includes("milktea") || name.includes("bubble")) {
      return { icon: "coffee", color: "#00BCD4" }; // Xanh ngọc (Trà sữa)
    }

    // 2. Fallback to Types
    if (typeStr.includes("chay")) return { icon: "salad", color: "#2E7D32" };  // Xanh lá đậm (Chay)
    if (typeStr.includes("nhật")) return { icon: "fish", color: "#FF9800" };  // Cam (Nhật)
    if (typeStr.includes("thái")) return { icon: "soup", color: "#E91E63" };  // Hồng (Thái)
    if (typeStr.includes("ấn")) return { icon: "utensils", color: "#FF5722" };   // Cam đậm (Ấn)
    if (typeStr.includes("âu")) return { icon: "utensils", color: "#9C27B0" };    // Tím (Âu)
    if (typeStr.includes("việt")) return { icon: "soup", color: "#EA4335" };  // Đỏ (Việt)
    if (typeStr.includes("cà phê") || name.includes("cafe") || name.includes("coffee")) {
      return { icon: "coffee", color: "#795548" }; // Nâu (Cà phê)
    }
    if (typeStr.includes("nước") || name.includes("nước") || name.includes("tea") || name.includes("trà")) {
      return { icon: "coffee", color: "#00BCD4" }; // Xanh ngọc (Nước giải khát)
    }
    if (typeStr.includes("bánh")) return { icon: "cake", color: "#EC407A" };  // Hồng nhạt (Bánh)
    if (typeStr.includes("nhanh")) return { icon: "utensils", color: "#795548" }; // Nâu (Fastfood)

    // General fallback
    return { icon: "utensils", color: "#757575" }; // Xám
  };

  return {
    type: "FeatureCollection",
    features: restaurants.map((res) => {
      const style = getStyle(res);
      return {
        type: "Feature",
        geometry: {
          type: "Point",
          coordinates: [res.lng ?? 0, res.lat ?? 0],
        },
        properties: {
          ...res,
          mapIcon: style.icon,
          mapColor: style.color,
        },
      };
    }),
  };
}

export const buildRestaurants = (items: any[]): Restaurant[] =>
  items.map((item, index) => {
    // Handle both snake_case (backend) and camelCase (frontend)
    const rawImageUrl = item.image_url || item.imageUrl || "";
    const imageUrl = rawImageUrl ? rawImageUrl.replace(/\\\//g, "/") : "";

    const name = item.name || "Nhà hàng";
    const address = item.address || "Chưa có địa chỉ";

    const mapQuery = [name, address]
      .filter(Boolean)
      .join(" ");

    const mapUrl = item.mapUrl || (mapQuery
      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
          mapQuery
        )}`
      : "https://www.google.com/maps");

    const star = item.star !== undefined ? item.star : item.rating;
    const ratingValue =
      typeof star === "number"
        ? star
        : Number(star ?? 0) || 0;

    const priceValue = item.avg_price !== undefined ? item.avg_price : item.price;

    return {
      id: item.id ?? `${name}-${index}`,

      name,
      address,

      rating: ratingValue,
      price: priceValue ?? "Chưa cập nhật",
      phone: item.phone_num || item.phone || "",

      mapUrl,
      imageUrl,

      semanticText: item.semantic_text || item.semanticText || "Chưa có mô tả.",

      meals: item.meals ?? [],
      meal: item.meal || item.assigned_meal || item.assignedMeal,
      assignedMeal: item.meal || item.assigned_meal || item.assignedMeal,

      warnings: item.warnings ?? [],
      notes: item.notes ?? [],
      source: item.source || (item.isCustom ? "user" : "ai"),
      lat: item.lat,
      lng: item.lng
    };
  });

/**
 * Infer a meal slot (Bữa sáng/Trưa/Tối/Phụ) for a restaurant based on
 * the restaurant `meals` field and a reference time (defaults to now).
 * Returns one of the strings used in the UI: "Bữa sáng", "Bữa trưa",
 * "Bữa tối", "Bữa phụ" or null if no suitable mapping.
 */
export function inferMealFromRestaurant(item: ApiRestaurant, refDate?: Date): string | null {
  const now = refDate || new Date();
  const hour = now.getHours();

  // Preferred meal by hour (local time)
  let preferred = "Bữa phụ";
  if (hour >= 5 && hour < 10) preferred = "Bữa sáng";
  else if (hour >= 10 && hour < 14) preferred = "Bữa trưa";
  else if ((hour >= 17 && hour < 23) || (hour >= 14 && hour < 17)) preferred = "Bữa tối";

  const available = (item.meals || []).map((m) => String(m || "").trim().toLowerCase());

  const mapToMealLabel = (m: string) => {
    if (!m) return null;
    m = m.toLowerCase();
    if (m.includes("sáng")) return "Bữa sáng";
    if (m.includes("trưa")) return "Bữa trưa";
    if (m.includes("tối") || m.includes("tối")) return "Bữa tối";
    if (m.includes("khuya")) return "Bữa phụ";
    return null;
  };

  // If restaurant explicitly supports preferred meal, return it
  for (const raw of available) {
    const label = mapToMealLabel(raw);
    if (label === preferred) return preferred;
  }

  // Otherwise, try a sensible fallback order: trưa -> tối -> sáng -> phụ
  const fallbackOrder = ["Bữa trưa", "Bữa tối", "Bữa sáng", "Bữa phụ"];
  for (const f of fallbackOrder) {
    for (const raw of available) {
      const label = mapToMealLabel(raw);
      if (label === f) return f;
    }
  }

  return null;
}

/**
 * Format meal names for UI display (e.g., 'xế' -> 'Bữa phụ')
 */
export function formatMealDisplay(meal: string | undefined | null): string {
  if (!meal) return "";
  const m = meal.trim().toLowerCase();
  if (m === "xế") return "Bữa phụ";
  // Capitalize first letter, rest lowercase
  return meal.charAt(0).toUpperCase() + meal.slice(1).toLowerCase();
}

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
  assignedMeal?: string;
  healthTagsDisplay?: {
    warnings?: string[];
    notes?: string[];
  };
  warnings?: string[];
  notes?: string[];
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
  lat?: number;
  lng?: number;
};

export function convertToGeoJSON(restaurants: ApiRestaurant[]) {
  const getStyle = (types?: string[]) => {
    const typeStr = types?.join(" ") || "";
    if (typeStr.includes("Việt")) return { icon: "🍜", color: "#EA4335" }; // Đỏ Google
    if (typeStr.includes("Nhật")) return { icon: "🍣", color: "#FF9800" }; // Cam
    if (typeStr.includes("Thái")) return { icon: "🌶️", color: "#E91E63" }; // Hồng
    if (typeStr.includes("Âu")) return { icon: "🍕", color: "#9C27B0" };   // Tím
    if (typeStr.includes("Chay")) return { icon: "🥦", color: "#4CAF50" };  // Xanh lá
    if (typeStr.includes("nước")) return { icon: "☕", color: "#03A9F4" }; // Xanh dương
    if (typeStr.includes("bánh")) return { icon: "🍰", color: "#EC407A" }; // Hồng nhạt
    if (typeStr.includes("nhanh")) return { icon: "🍔", color: "#795548" }; // Nâu
    return { icon: "📍", color: "#757575" }; // Xám
  };

  return {
    type: "FeatureCollection",
    features: restaurants.map((res) => {
      const style = getStyle(res.type);
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

export const buildRestaurants = (items: ApiRestaurant[]): Restaurant[] =>
  items.map((item, index) => {
    const imageUrl = item.image_url
      ? item.image_url.replace(/\\\//g, "/")
      : "";

    const mapQuery = [item.name, item.address]
      .filter(Boolean)
      .join(" ");

    const mapUrl = mapQuery
      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
          mapQuery
        )}`
      : "https://www.google.com/maps";

    const ratingValue =
      typeof item.star === "number"
        ? item.star
        : Number(item.star ?? 0) || 0;

    return {
      id: item.id ?? `${item.name}-${index}`,

      name: item.name || "Nhà hàng",
      address: item.address || "Chưa có địa chỉ",

      rating: ratingValue,
      price: item.avg_price ?? "Chưa cập nhật",
      phone: item.phone_num ?? "",

      mapUrl,
      imageUrl,

      semanticText: item.semantic_text
        ? String(item.semantic_text)
        : "Chưa có mô tả.",

      meals: item.meals ?? [],
      assignedMeal: item.meal || item.assigned_meal,

      // 👇 QUAN TRỌNG
      warnings: item.warnings ?? [],
      notes: item.notes ?? []
    };
  });

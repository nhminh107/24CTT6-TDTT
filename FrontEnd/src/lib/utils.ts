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
  assigned_meal?: string;
  main_tag?: string[];
  potential_tag?: string[];
  warnings?: string[];
  notes?: string[];
};

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

      // 👇 QUAN TRỌNG
      warnings: item.warnings ?? [],
      notes: item.notes ?? []
    };
  });

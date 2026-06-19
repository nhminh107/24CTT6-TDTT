import { authStorage } from "@/lib/auth";
import { getApiOrigin } from "@/lib/apiBase";

export const apiFetch = async (input: RequestInfo, init: RequestInit = {}) => {
  const headers = new Headers(init.headers || {});
  const googleUid = authStorage.getGoogleUid();
  const idToken = authStorage.getIdToken();

  if (googleUid) {
    headers.set("x-user-id", googleUid);
  }
  
  if (idToken) {
    headers.set("Authorization", `Bearer ${idToken}`);
  }

  return fetch(input, {
    ...init,
    headers
  });
};

const API_BASE_URL = getApiOrigin();

export const itineraryApi = {
  get: async (userId: string) => {
    const res = await apiFetch(`${API_BASE_URL}/api/v1/itinerary/${userId}`);
    return res.json();
  },
  select: async (userId: string, meal: string, restaurantData: any) => {
    const res = await apiFetch(`${API_BASE_URL}/api/v1/itinerary/select`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, meal, restaurant_data: restaurantData }),
    });
    return res.json();
  },
  deleteMeal: async (userId: string, itemId: string) => {
    const res = await apiFetch(`${API_BASE_URL}/api/v1/itinerary/${userId}/${itemId}`, {
      method: "DELETE",
    });
    return res.json();
  },
  reset: async (userId: string) => {
    const res = await apiFetch(`${API_BASE_URL}/api/v1/itinerary/${userId}`, {
      method: "DELETE",
    });
    return res.json();
  },
  reorder: async (userId: string, orderedItems: { id: string, meal: string }[]) => {
    const res = await apiFetch(`${API_BASE_URL}/api/v1/itinerary/reorder`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, ordered_items: orderedItems }),
    });
    return res.json();
  },
  share: async (userId: string, itineraryData: any[]) => {
    const res = await apiFetch(`${API_BASE_URL}/api/v1/itinerary/share`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, itinerary_data: itineraryData }),
    });
    return res.json();
  },
  importShared: async (userId: string, shareId: string) => {
    const res = await apiFetch(`${API_BASE_URL}/api/v1/itinerary/import-shared`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, share_id: shareId }),
    });
    return res.json();
  },
  getPublic: async (shareId: string) => {
    const res = await apiFetch(`${API_BASE_URL}/public/${shareId}`);
    return res.json();
  },
};

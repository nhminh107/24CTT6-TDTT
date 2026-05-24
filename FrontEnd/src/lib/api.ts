import { authStorage } from "@/lib/auth";

export const apiFetch = async (input: RequestInfo, init: RequestInit = {}) => {
  const headers = new Headers(init.headers || {});
  const googleUid = authStorage.getGoogleUid();
  const idToken = authStorage.getIdToken();

  if (googleUid) {
    headers.set("x-user-id", googleUid);
  } else if (idToken) {
    headers.set("Authorization", `Bearer ${idToken}`);
  }

  return fetch(input, {
    ...init,
    headers
  });
};

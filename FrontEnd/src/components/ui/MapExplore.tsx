"use client";

import React, { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { Map, Source, Layer, Popup, NavigationControl, GeolocateControl, Marker, MapRef } from "react-map-gl/maplibre";
import maplibregl from "maplibre-gl";
import 'maplibre-gl/dist/maplibre-gl.css';
import { convertToGeoJSON, ApiRestaurant, Restaurant, buildRestaurants, inferMealFromRestaurant } from "@/lib/utils";
import { Star, MapPin, Navigation, Info, X, MessageSquare, Plus, Check, Loader2, ChevronDown, ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from "lucide-react";
import Link from "next/link";
import RestaurantDetailModal from "./RestaurantDetailModal";
import { itineraryApi } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

// Goong Map configuration constants
const DEFAULT_VIEW_STATE = {
  latitude: 10.7769,
  longitude: 106.7009,
  zoom: 16,
};

const MAP_KEY = process.env.NEXT_PUBLIC_GOONG_MAP_API_KEY;
const GOONG_MAP_STYLE_URL = `https://tiles.goong.io/assets/goong_map_web.json?api_key=${MAP_KEY}`;

const MEAL_OPTIONS = ["Bữa sáng", "Bữa trưa", "Bữa tối", "Bữa phụ"];

type MapExploreProps = {
  userPlaceId?: string;
  userLocationText?: string;
  currentItinerary?: any[];
  onItineraryChange?: () => void;
  onUserLocationChange?: (location: { location: string; placeId: string }) => void;
};

export default function MapExplore({
  userPlaceId,
  userLocationText,
  currentItinerary: propItinerary,
  onItineraryChange,
  onUserLocationChange,
}: MapExploreProps) {
  const { user } = useAuth();
  const mapRef = useRef<MapRef>(null);
  const [restaurants, setRestaurants] = useState<ApiRestaurant[]>([]);
  const [loading, setLoading] = useState(true);
  const [popupInfo, setPopupInfo] = useState<any | null>(null);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [selectedResForModal, setSelectedResForModal] = useState<Restaurant | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [mapStyle, setMapStyle] = useState<any>(null);
  const [zoom, setZoom] = useState(DEFAULT_VIEW_STATE.zoom);
  // Lưu tọa độ cần flyTo, thực hiện sau khi map load xong
  const [pendingFlyTo, setPendingFlyTo] = useState<{ lat: number; lng: number } | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Itinerary local state if not passed from props
  const [localItinerary, setLocalItinerary] = useState<any[]>([]);
  const currentItinerary = propItinerary || localItinerary;

  // Add to itinerary state
  const [addingMeal, setAddingMeal] = useState(false);
  const [showMealPicker, setShowMealPicker] = useState(false);
  const [addSuccess, setAddSuccess] = useState<string | null>(null);
  const [addError, setAddError] = useState<string | null>(null);

  // Fetch itinerary if standalone
  useEffect(() => {
    if (!propItinerary && user?.uid) {
      itineraryApi.get(user.uid).then(data => {
        if (data.status === "success") setLocalItinerary(data.itinerary || []);
      });
    }
  }, [propItinerary, user?.uid]);

  const refreshItinerary = useCallback(() => {
    if (!propItinerary && user?.uid) {
      itineraryApi.get(user.uid).then(data => {
        if (data.status === "success") setLocalItinerary(data.itinerary || []);
      });
    }
    onItineraryChange?.();
  }, [propItinerary, user?.uid, onItineraryChange]);


  const applyUserLocation = (lat: number, lng: number, locationLabel: string, placeId: string) => {
    setUserLocation({ lat, lng });
    setPendingFlyTo({ lat, lng });
    onUserLocationChange?.({ location: locationLabel, placeId });
  };

  // State for off-screen indicators
  const [edgeIndicators, setEdgeIndicators] = useState<any[]>([]);

  // Update edge indicators on map move/zoom
  const updateEdgeIndicators = useCallback(() => {
    if (!mapRef.current || currentItinerary.length === 0) {
      setEdgeIndicators([]);
      return;
    }

    const map = mapRef.current.getMap();
    const canvas = map.getCanvas();
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const padding = 60;

    const indicators: any[] = [];

    currentItinerary.forEach((item) => {
      if (!item.lat || !item.lng) return;

      const pos = map.project([item.lng, item.lat]);
      const isOffScreen = pos.x < 0 || pos.x > width || pos.y < 0 || pos.y > height;

      if (isOffScreen) {
        // Clamp position to edges
        let edgeX = Math.max(padding, Math.min(width - padding, pos.x));
        let edgeY = Math.max(padding, Math.min(height - padding, pos.y));
        
        // Determine arrow direction
        let direction = "up";
        if (pos.x < 0) direction = "left";
        else if (pos.x > width) direction = "right";
        else if (pos.y < 0) direction = "up";
        else if (pos.y > height) direction = "down";

        indicators.push({
          id: item.id,
          name: item.name,
          x: edgeX,
          y: edgeY,
          direction,
          lat: item.lat,
          lng: item.lng
        });
      }
    });

    setEdgeIndicators(indicators);
  }, [currentItinerary]);

  useEffect(() => {
    if (mapLoaded) {
      updateEdgeIndicators();
    }
  }, [mapLoaded, updateEdgeIndicators, zoom]);

  // 1. Fetch and Clean Map Style
  useEffect(() => {
    async function loadStyle() {
      try {
        const response = await fetch(GOONG_MAP_STYLE_URL);
        const style = await response.json();
        if (style.layers) {
          style.layers = style.layers.filter((layer: any) => {
            const id = layer.id.toLowerCase();
            const isPOI = ["poi", "transit", "landmark", "attraction", "business", "food"].some(key => id.includes(key));
            const isSymbol = layer.type === "symbol";
            return !(isPOI && isSymbol);
          });
        }
        setMapStyle(style);
      } catch (error) {
        setMapStyle(GOONG_MAP_STYLE_URL);
      }
    }
    loadStyle();
  }, []);

  // 2. Fetch restaurants
  useEffect(() => {
    async function fetchAll() {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "https://api.bmi-foodtour.io.vn"}/api/v1/restaurants/all`);
        const data = await res.json();
        if (data.status === "success") setRestaurants(data.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    fetchAll();
  }, []);

  // 3. Resolve user location từ userPlaceId — chỉ set state tọa độ
  //    flyTo thực hiện sau khi map load xong (xem handleMapLoad)
  useEffect(() => {
    let cancelled = false;

    async function resolveUserLocation() {
      if (userPlaceId) {
        // Trường hợp GPS: "geo_10.76940_106.68350"
        if (userPlaceId.startsWith("geo_")) {
          const raw = userPlaceId.slice(4);
          // Chỉ có đúng 1 dấu "_" ngăn cách lat và lng
          const sepIdx = raw.indexOf("_");
          if (sepIdx > 0) {
            const lat = parseFloat(raw.slice(0, sepIdx));
            const lng = parseFloat(raw.slice(sepIdx + 1));
            if (!isNaN(lat) && !isNaN(lng) && !cancelled) {
                applyUserLocation(lat, lng, "Vị trí hiện tại", userPlaceId);
            }
          }
          return;
        }

        // Trường hợp Goong place_id (nhập địa chỉ tay)
        try {
          const res = await fetch(
            `/api/maps/place-detail?place_id=${encodeURIComponent(userPlaceId)}`
          );
          if (!res.ok || cancelled) return;
          const data = await res.json();
          if (data.status === "success" && data.data?.lat && data.data?.lng) {
            const { lat, lng } = data.data;
            if (!cancelled) {
              applyUserLocation(lat, lng, userLocationText?.trim() || "Vị trí được chọn", userPlaceId);
            }
          }
        } catch (e) {
          console.warn("Geocode placeId failed:", e);
        }
        return;
      }

      const query = userLocationText?.trim();
      if (!query) return;

      try {
        const suggestionRes = await fetch(
          `/api/maps/suggestions?q=${encodeURIComponent(query)}`
        );
        if (!suggestionRes.ok || cancelled) return;

        const suggestions = await suggestionRes.json();
        const firstPlaceId = Array.isArray(suggestions)
          ? suggestions.find((item: any) => item?.place_id)?.place_id
          : null;

        if (!firstPlaceId || cancelled) return;

        const detailRes = await fetch(
          `/api/maps/place-detail?place_id=${encodeURIComponent(firstPlaceId)}`
        );
        if (!detailRes.ok || cancelled) return;

        const data = await detailRes.json();
        if (data.status === "success" && data.data?.lat && data.data?.lng && !cancelled) {
          const { lat, lng } = data.data;
          applyUserLocation(lat, lng, query, firstPlaceId);
        }
      } catch (e) {
        console.warn("Geocode fallback failed:", e);
      }
    }

    resolveUserLocation();

    return () => {
      cancelled = true;
    };
  }, [userPlaceId, userLocationText]);

  // 4. Thực hiện flyTo SAU KHI map đã load và có tọa độ
  useEffect(() => {
    if (mapLoaded && pendingFlyTo && mapRef.current) {
      mapRef.current.flyTo({ center: [pendingFlyTo.lng, pendingFlyTo.lat], zoom: 16 });
      setPendingFlyTo(null);
    }
  }, [mapLoaded, pendingFlyTo]);

  const geoJsonData = useMemo(() => convertToGeoJSON(restaurants), [restaurants]);

  const clusterLayer: any = {
    id: "clusters",
    type: "circle",
    source: "restaurants",
    filter: ["has", "point_count"],
    paint: {
      "circle-color": ["step", ["get", "point_count"], "#51bbd6", 100, "#f1f075", 750, "#f28cb1"],
      "circle-radius": ["step", ["get", "point_count"], 20, 100, 30, 750, 40],
      "circle-stroke-width": 2,
      "circle-stroke-color": "#fff",
    },
  };

  const clusterCountLayer: any = {
    id: "cluster-count",
    type: "symbol",
    source: "restaurants",
    filter: ["has", "point_count"],
    layout: {
      "text-field": "{point_count_abbreviated}",
      "text-font": ["Noto Sans Regular"],
      "text-size": 12,
    },
  };

  const onMapClick = (event: any) => {
    const feature = event.features?.[0];
    if (feature && feature.layer.id === "clusters") {
      const clusterId = feature.properties.cluster_id;
      const mapSource: any = mapRef.current?.getSource("restaurants");
      mapSource.getClusterExpansionZoom(clusterId, (err: any, zoom: number) => {
        if (!err) mapRef.current?.easeTo({ center: feature.geometry.coordinates, zoom });
      });
    }
  };

  const handleOpenModal = (resProps: any) => {
    const formatted = buildRestaurants([resProps])[0];
    setSelectedResForModal(formatted);
    setIsModalOpen(true);
  };

  // ── Thêm vào lịch trình ────────────────────────────────────────────────────
  const handleAddToItinerary = useCallback(async (meal: string) => {
    if (!user?.uid || !popupInfo) return;


    setAddingMeal(true);
    setShowMealPicker(false);
    setAddError(null);

    try {
      const rawItem = { ...popupInfo };

      rawItem.source = "user";

      const restaurantData = buildRestaurants([rawItem])[0];
      const data = await itineraryApi.select(user.uid, meal, restaurantData);
      if (data.status === "success") {
        setAddSuccess(meal);
        refreshItinerary();
        setTimeout(() => setAddSuccess(null), 2500);
      } else {
        setAddError("Không thể thêm vào lịch trình.");
      }
    } catch (e) {
      setAddError("Lỗi kết nối. Vui lòng thử lại.");
    } finally {
      setAddingMeal(false);
    }
  }, [user, popupInfo, refreshItinerary]);

  // Kiểm tra quán đã có trong lịch trình chưa
  const isAlreadyInItinerary = useMemo(() => {
    if (!popupInfo) return false;
    return currentItinerary.some((stop) => stop.id === popupInfo.id || String(stop.id) === String(popupInfo.id) || stop.name === popupInfo.name);
  }, [popupInfo, currentItinerary]);

  // Meal đã dùng (để disable)
  const usedMeals = useMemo(() => {
    return currentItinerary.map((stop) => stop.meal);
  }, [currentItinerary]);

  // Reset meal picker khi đổi popup
  useEffect(() => {
    setShowMealPicker(false);
    setAddSuccess(null);
    setAddError(null);
  }, [popupInfo?.id]);

  if (loading || !mapStyle) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-50">
        <div className="w-12 h-12 border-4 border-rose-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      <Map
        initialViewState={DEFAULT_VIEW_STATE}
        mapStyle={mapStyle}
        mapLib={maplibregl}
        ref={mapRef}
        onClick={onMapClick}
        onZoom={(e) => setZoom(e.viewState.zoom)}
        onMove={updateEdgeIndicators}
        onLoad={() => {
          setMapLoaded(true);
          updateEdgeIndicators();
        }}
        interactiveLayerIds={["clusters"]}
        style={{ width: "100%", height: "100%" }}
      >
        <GeolocateControl
          position="top-right"
          showUserLocation={false}
          onGeolocate={(evt) => {
            const lat = evt.coords.latitude;
            const lng = evt.coords.longitude;
            applyUserLocation(lat, lng, "Vị trí hiện tại", `geo_${lat}_${lng}`);
          }}
          onError={(evt) => {
            console.warn("GeolocateControl error:", evt.message);
          }}
        />
        <NavigationControl position="top-right" />

        <Source
          id="restaurants"
          type="geojson"
          data={geoJsonData as any}
          cluster={true}
          clusterMaxZoom={13}
          clusterRadius={50}
        >
          <Layer {...clusterLayer} />
          <Layer {...clusterCountLayer} />
        </Source>

        {/* MARKERS */}
        {restaurants.map((res: any, idx) => {
          const isSelected = currentItinerary.some((stop) => String(stop.id) === String(res.id) || stop.name === res.name);
          
          // Always show markers for selected restaurants, even when zoomed out
          if (zoom <= 13 && !isSelected) return null;

          return (
            <Marker
              key={`res-${res.id || idx}`}
              longitude={res.lng}
              latitude={res.lat}
              anchor="bottom"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                setPopupInfo(res);
              }}
              style={{ zIndex: isSelected ? 10 : 1 }}
            >
              <div className={`relative flex flex-col items-center group cursor-pointer ${isSelected ? "scale-110" : ""}`}>
                {/* HIỆU ỨNG TỎA SÁNG RỘNG KHI ĐƯỢC CHỌN */}
                {isSelected && (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none -mt-3">
                    <div className="absolute w-12 h-12 rounded-full bg-rose-500 animate-sonar" />
                    <div className="absolute w-12 h-12 rounded-full bg-brand-coral animate-sonar [animation-delay:0.9s]" />
                  </div>
                )}

                <div
                  className={`relative w-9 h-9 rounded-full flex items-center justify-center border-2 shadow-xl transition-all group-hover:scale-125
                    ${isSelected ? "border-rose-500 ring-2 ring-white z-10 bg-brand-coral" : "border-white bg-white"}`}
                  style={{ backgroundColor: isSelected ? undefined : convertToGeoJSON([res]).features[0].properties.mapColor }}
                >
                  <span className={`text-lg ${isSelected ? "animate-pulse" : ""}`}>
                    {isSelected ? "📍" : convertToGeoJSON([res]).features[0].properties.mapIcon}
                  </span>
                </div>
                <div className={`relative z-10 mt-1.5 px-2.5 py-1 rounded-lg shadow-md border transition-colors
                  ${isSelected ? "bg-rose-600 border-rose-500" : "bg-white/95 border-slate-100"}`}>
                  <p className={`text-[11px] font-black whitespace-nowrap ${isSelected ? "text-white" : "text-slate-800"}`}>
                    {isSelected && "🌟 "}{res.name}
                  </p>
                </div>
              </div>
            </Marker>
          );
        })}

        {/* EXTRA ITINERARY MARKERS (For items not in the main list) */}
        {currentItinerary.filter(stop => 
          !restaurants.some(res => String(res.id) === String(stop.id) || res.name === stop.name)
        ).map((stop, idx) => (
          <Marker
            key={`itinerary-${stop.id || idx}`}
            longitude={stop.lng}
            latitude={stop.lat}
            anchor="bottom"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              setPopupInfo(stop);
            }}
            style={{ zIndex: 11 }}
          >
            <div className="relative flex flex-col items-center group cursor-pointer scale-110">
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none -mt-3">
                <div className="absolute w-12 h-12 rounded-full bg-rose-500 animate-sonar" />
                <div className="absolute w-12 h-12 rounded-full bg-brand-coral animate-sonar [animation-delay:0.9s]" />
              </div>
              
              <div className="relative z-10 w-9 h-9 rounded-full flex items-center justify-center border-2 border-rose-500 ring-2 ring-white bg-brand-coral shadow-xl transition-all group-hover:scale-125">
                <span className="text-lg animate-pulse">📍</span>
              </div>
              <div className="relative z-10 mt-1.5 px-2.5 py-1 bg-rose-600 border border-rose-500 rounded-lg shadow-md transition-colors">
                <p className="text-[11px] font-black whitespace-nowrap text-white">🌟 {stop.name}</p>
              </div>
            </div>
          </Marker>
        ))}

        {/* USER LOCATION MARKER */}
        {userLocation && (
          <Marker longitude={userLocation.lng} latitude={userLocation.lat} anchor="center">
            <div className="relative flex items-center justify-center">
              <div className="absolute w-10 h-10 bg-blue-500/20 rounded-full animate-ping" />
              <div className="relative w-5 h-5 bg-blue-600 rounded-full border-2 border-white shadow-2xl" />
            </div>
          </Marker>
        )}

        {/* POPUP */}
        {popupInfo && (
          <Popup
            longitude={popupInfo.lng}
            latitude={popupInfo.lat}
            anchor="bottom"
            offset={40}
            onClose={() => { setPopupInfo(null); setShowMealPicker(false); }}
            closeButton={false}
            className="z-50"
          >
            <div className="p-0 min-w-[260px] overflow-hidden rounded-2xl bg-white shadow-2xl border border-slate-100">
              <img src={popupInfo.image_url || popupInfo.imageUrl || "/assets/images/AI.png"} className="w-full h-32 object-cover" />
              <div className="p-4 space-y-3">
                <div>
                  <h3 className="font-bold text-slate-800 text-base leading-tight line-clamp-2">{popupInfo.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex items-center text-xs font-bold text-yellow-500">
                      <Star className="w-3.5 h-3.5 fill-current mr-0.5" /> {popupInfo.star || popupInfo.rating}
                    </div>
                    <span className="text-xs text-slate-300">|</span>
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                      {Array.isArray(popupInfo.type) ? popupInfo.type[0] : (popupInfo.meals?.[0] || "Nhà hàng")}
                    </span>
                  </div>
                </div>
                <div className="flex items-start text-[11px] text-slate-500 italic">
                  <MapPin className="w-3.5 h-3.5 mr-1.5 shrink-0" />
                  <span>{popupInfo.address}</span>
                </div>

                {/* ── Thêm vào lịch trình ── */}
                {user ? (
                  <div className="space-y-2">
                    {addError && (
                      <p className="text-[11px] text-red-500 font-semibold text-center">{addError}</p>
                    )}

                    {isAlreadyInItinerary && !addSuccess ? (
                      <div className="flex items-center justify-center gap-1.5 w-full py-2 bg-green-50 border border-green-200 text-green-600 text-xs font-bold rounded-xl">
                        <Check className="w-3.5 h-3.5" />
                        Đã có trong lịch trình
                      </div>
                    ) : addSuccess ? (
                      <div className="flex items-center justify-center gap-1.5 w-full py-2 bg-green-50 border border-green-200 text-green-600 text-xs font-bold rounded-xl animate-pulse">
                        <Check className="w-3.5 h-3.5" />
                        Đã thêm vào {addSuccess}!
                      </div>
                    ) : (
                      <div className="relative">
                        <button
                          onClick={() => setShowMealPicker((v) => !v)}
                          disabled={addingMeal}
                          className="w-full py-2.5 bg-gradient-to-r from-brand-coral to-brand-flame hover:opacity-90 text-white text-xs font-bold rounded-xl shadow transition-all active:scale-95 flex items-center justify-center gap-2 disabled:opacity-60"
                        >
                          {addingMeal ? (
                            <><Loader2 className="w-4 h-4 animate-spin" /> Đang thêm...</>
                          ) : (
                            <><Plus className="w-4 h-4" /> Thêm vào lịch trình <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showMealPicker ? "rotate-180" : ""}`} /></>
                          )}
                        </button>

                        {/* Meal picker dropdown */}
                        {showMealPicker && (
                          <div className="absolute bottom-full left-0 right-0 mb-1.5 bg-white rounded-xl border border-slate-100 shadow-xl overflow-hidden z-10">
                            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 px-3 pt-2.5 pb-1">Chọn bữa ăn</p>
                            <button
                              onClick={() => {
                                const suggested = inferMealFromRestaurant(popupInfo);
                                if (suggested) {
                                  handleAddToItinerary(suggested);
                                } else {
                                  setAddError("Không thể gợi ý bữa ăn tự động.");
                                }
                              }}
                              className={`w-full text-left px-3 py-2.5 text-xs font-semibold transition-colors flex items-center justify-between text-slate-700 hover:bg-orange-50 hover:text-brand-coral`}
                            >
                              Tự động (gợi ý)
                              <span className="text-[10px] font-normal text-slate-400">Gợi ý theo giờ mở</span>
                            </button>

                            {MEAL_OPTIONS.map((meal) => {
                              const isUsed = usedMeals.includes(meal);
                              return (
                                <button
                                  key={meal}
                                  onClick={() => !isUsed && handleAddToItinerary(meal)}
                                  disabled={isUsed}
                                  className={`w-full text-left px-3 py-2.5 text-xs font-semibold transition-colors flex items-center justify-between
                                    ${isUsed
                                      ? "text-slate-300 cursor-not-allowed bg-slate-50"
                                      : "text-slate-700 hover:bg-orange-50 hover:text-brand-coral"
                                    }`}
                                >
                                  {meal}
                                  {isUsed && <span className="text-[10px] font-normal text-slate-300">Đã có</span>}
                                </button>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : (
                  <Link
                    href="/login"
                    className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-bold rounded-xl transition flex items-center justify-center gap-2"
                  >
                    Đăng nhập để thêm lịch trình
                  </Link>
                )}

                <button
                  onClick={() => handleOpenModal(popupInfo)}
                  className="w-full py-2 border border-slate-200 hover:border-brand-coral text-slate-600 hover:text-brand-coral text-xs font-bold rounded-xl transition-all active:scale-95 flex items-center justify-center gap-2"
                >
                  <Info className="w-3.5 h-3.5" /> Xem chi tiết nhà hàng
                </button>
              </div>
            </div>
          </Popup>
        )}
      </Map>

      {/* EDGE INDICATORS (Arrows) */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {edgeIndicators.map((ind) => (
          <div
            key={ind.id}
            className="absolute flex flex-col items-center gap-1 transition-all duration-300 ease-out"
            style={{
              left: ind.x,
              top: ind.y,
              transform: "translate(-50%, -50%)",
            }}
          >
            <button
              onClick={() => {
                if (mapRef.current) {
                  mapRef.current.flyTo({ center: [ind.lng, ind.lat], zoom: 16 });
                  // Tìm quán trong list hoặc itinerary để hiện popup
                  const res = currentItinerary.find(item => String(item.id) === String(ind.id)) || 
                             restaurants.find(item => String(item.id) === String(ind.id));
                  if (res) setPopupInfo(res);
                }
              }}
              className="pointer-events-auto flex items-center gap-2 px-3 py-1.5 bg-rose-500 text-white rounded-full shadow-lg border-2 border-white hover:bg-rose-600 transition-colors active:scale-90"
            >
              {ind.direction === "up" && <ArrowUp className="w-3.5 h-3.5 animate-bounce" />}
              {ind.direction === "down" && <ArrowDown className="w-3.5 h-3.5 animate-bounce" />}
              {ind.direction === "left" && <ArrowLeft className="w-3.5 h-3.5 animate-bounce" />}
              {ind.direction === "right" && <ArrowRight className="w-3.5 h-3.5 animate-bounce" />}
              <span className="text-[10px] font-bold whitespace-nowrap max-w-[100px] truncate">{ind.name}</span>
            </button>
          </div>
        ))}
      </div>

      {/* Floating Header UI — chỉ hiện khi fullscreen (/explore), ẩn khi trong panel */}
      {!userPlaceId && (
        <div className="absolute top-8 left-8 z-10 flex flex-col gap-4 pointer-events-none">
          <div className="pointer-events-auto bg-white/80 backdrop-blur-xl p-5 rounded-[24px] shadow-2xl border border-white/40">
            <h1 className="text-2xl font-black text-slate-800 flex items-center gap-3">
              <Navigation className="w-7 h-7 text-rose-500 fill-current" />
              Khám phá Ẩm thực
            </h1>
            <p className="text-xs text-slate-500 font-bold uppercase tracking-[0.2em] mt-1 ml-10">
              Dữ liệu độc quyền • {restaurants.length} địa điểm
            </p>
          </div>

          <Link
            href="/app"
            className="pointer-events-auto flex items-center gap-3 w-fit bg-slate-900 hover:bg-slate-800 text-white px-7 py-4 rounded-[20px] font-bold text-sm shadow-2xl transition-all active:scale-95 group border border-white/10"
          >
            <MessageSquare className="w-5 h-5 text-rose-400 group-hover:scale-110 transition-transform" />
            Quay lại Chat AI
          </Link>
        </div>
      )}

      <RestaurantDetailModal restaurant={selectedResForModal} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}

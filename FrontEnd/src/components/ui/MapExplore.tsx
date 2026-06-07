"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { Map, Source, Layer, Popup, NavigationControl, GeolocateControl, Marker, MapRef } from "react-map-gl/maplibre";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { convertToGeoJSON, ApiRestaurant, Restaurant, buildRestaurants } from "@/lib/utils";
import { Star, MapPin, Navigation, Info, X, MessageSquare } from "lucide-react";
import Link from "next/link";
import RestaurantDetailModal from "./RestaurantDetailModal";

// Goong Map configuration constants
const DEFAULT_VIEW_STATE = {
  latitude: 10.7769,
  longitude: 106.7009,
  zoom: 12,
};

const MAP_KEY = process.env.NEXT_PUBLIC_GOONG_MAP_API_KEY;
const GOONG_MAP_STYLE_URL = `https://tiles.goong.io/assets/goong_map_web.json?api_key=${MAP_KEY}`;

export default function MapExplore() {
  const mapRef = useRef<MapRef>(null);
  const [restaurants, setRestaurants] = useState<ApiRestaurant[]>([]);
  const [loading, setLoading] = useState(true);
  const [popupInfo, setPopupInfo] = useState<any | null>(null);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [selectedResForModal, setSelectedResForModal] = useState<Restaurant | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [mapStyle, setMapStyle] = useState<any>(null);
  const [zoom, setZoom] = useState(DEFAULT_VIEW_STATE.zoom);

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
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/api/v1/restaurants/all`);
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

  // 3. Geolocation (Tự động bay tới vị trí người dùng khi vào trang riêng)
  useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (p) => {
          const { latitude, longitude } = p.coords;
          setUserLocation({ lat: latitude, lng: longitude });
          if (mapRef.current) {
            mapRef.current.flyTo({ center: [longitude, latitude], zoom: 14 });
          }
        },
        (e) => console.warn(e)
      );
    }
  }, []);

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

  if (loading || !mapStyle) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-slate-50">
        <div className="w-12 h-12 border-4 border-rose-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="relative w-full h-screen">
      <Map
        initialViewState={DEFAULT_VIEW_STATE}
        mapStyle={mapStyle}
        mapLib={maplibregl}
        ref={mapRef}
        onClick={onMapClick}
        onZoom={(e) => setZoom(e.viewState.zoom)}
        interactiveLayerIds={["clusters"]}
        style={{ width: "100%", height: "100%" }}
      >
        <GeolocateControl position="top-right" />
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

        {/* GOOGLE MAPS STYLE MARKERS */}
        {zoom > 13 && restaurants.map((res: any, idx) => (
          <Marker
            key={res.id || idx}
            longitude={res.lng}
            latitude={res.lat}
            anchor="bottom"
            onClick={(e) => {
              e.originalEvent.stopPropagation();
              setPopupInfo(res);
            }}
          >
            <div className="flex flex-col items-center group cursor-pointer">
              <div 
                className="w-9 h-9 rounded-full flex items-center justify-center border-2 border-white shadow-xl transition-transform group-hover:scale-125"
                style={{ backgroundColor: convertToGeoJSON([res]).features[0].properties.mapColor }}
              >
                <span className="text-lg">{convertToGeoJSON([res]).features[0].properties.mapIcon}</span>
              </div>
              <div className="mt-1.5 px-2.5 py-1 bg-white/95 backdrop-blur-sm rounded-lg shadow-md border border-slate-100">
                <p className="text-[11px] font-black text-slate-800 whitespace-nowrap">{res.name}</p>
              </div>
            </div>
          </Marker>
        ))}

        {userLocation && (
          <Marker longitude={userLocation.lng} latitude={userLocation.lat} anchor="center">
            <div className="relative flex items-center justify-center">
              <div className="absolute w-10 h-10 bg-blue-500/20 rounded-full animate-ping" />
              <div className="relative w-5 h-5 bg-blue-600 rounded-full border-2 border-white shadow-2xl" />
            </div>
          </Marker>
        )}

        {popupInfo && (
          <Popup
            longitude={popupInfo.lng}
            latitude={popupInfo.lat}
            anchor="bottom"
            offset={40}
            onClose={() => setPopupInfo(null)}
            closeButton={false}
            className="z-50"
          >
            <div className="p-0 min-w-[240px] overflow-hidden rounded-2xl bg-white shadow-2xl border border-slate-100">
              <img src={popupInfo.image_url || "/assets/images/AI.png"} className="w-full h-32 object-cover" />
              <div className="p-4 space-y-3">
                <div>
                  <h3 className="font-bold text-slate-800 text-base leading-tight line-clamp-2">{popupInfo.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                      <div className="flex items-center text-xs font-bold text-yellow-500">
                        <Star className="w-3.5 h-3.5 fill-current mr-0.5" /> {popupInfo.star}
                      </div>
                      <span className="text-xs text-slate-300">|</span>
                      <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{popupInfo.type?.[0]}</span>
                  </div>
                </div>
                <div className="flex items-start text-[11px] text-slate-500 italic">
                  <MapPin className="w-3.5 h-3.5 mr-1.5 shrink-0" />
                  <span>{popupInfo.address}</span>
                </div>
                <button
                  onClick={() => handleOpenModal(popupInfo)}
                  className="w-full py-2.5 bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold rounded-xl shadow-lg transition-all active:scale-95 flex items-center justify-center gap-2"
                >
                  <Info className="w-4 h-4" /> Xem chi tiết nhà hàng
                </button>
              </div>
            </div>
          </Popup>
        )}
      </Map>

      {/* Floating Header UI (Dành cho trang rộng) */}
      <div className="absolute top-8 left-8 z-10 flex flex-col gap-4">
        <div className="bg-white/80 backdrop-blur-xl p-5 rounded-[24px] shadow-2xl border border-white/40">
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
          className="flex items-center gap-3 w-fit bg-slate-900 hover:bg-slate-800 text-white px-7 py-4 rounded-[20px] font-bold text-sm shadow-2xl transition-all active:scale-95 group border border-white/10"
        >
          <MessageSquare className="w-5 h-5 text-rose-400 group-hover:scale-110 transition-transform" />
          Quay lại Chat AI
        </Link>
      </div>

      <RestaurantDetailModal restaurant={selectedResForModal} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}

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
            // Chỉ lọc bỏ các layer nhãn (symbol) của các địa điểm không mong muốn
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

  // 3. Geolocation
  useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (p) => setUserLocation({ lat: p.coords.latitude, lng: p.coords.longitude }),
        (e) => console.warn(e)
      );
    }
  }, []);

  const geoJsonData = useMemo(() => convertToGeoJSON(restaurants), [restaurants]);

  // Cluster Layers (Giữ nguyên cho hiệu năng)
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

  // Hàm xử lý click cụm
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

  // Lấy danh sách các điểm không bị cluster để render Marker thủ công (khi zoom > 13)
  const unclusteredFeatures = geoJsonData.features.filter(f => restaurants.length > 0);

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

        {/* RENDER CUSTOM MARKERS (Google Maps Style with colored emojis) */}
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
              {/* Ô tròn chứa icon */}
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center border-2 border-white shadow-lg transition-transform group-hover:scale-125"
                style={{ backgroundColor: convertToGeoJSON([res]).features[0].properties.mapColor }}
              >
                <span className="text-sm">{convertToGeoJSON([res]).features[0].properties.mapIcon}</span>
              </div>
              {/* Tên quán */}
              <div className="mt-1 px-2 py-0.5 bg-white/90 backdrop-blur-sm rounded shadow-sm border border-slate-100">
                <p className="text-[10px] font-bold text-slate-800 whitespace-nowrap">{res.name}</p>
              </div>
            </div>
          </Marker>
        ))}

        {userLocation && (
          <Marker longitude={userLocation.lng} latitude={userLocation.lat} anchor="center">
            <div className="relative flex items-center justify-center">
              <div className="absolute w-8 h-8 bg-blue-500/20 rounded-full animate-ping" />
              <div className="relative w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-lg" />
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
            <div className="p-0 min-w-[220px] overflow-hidden rounded-2xl bg-white shadow-2xl border border-slate-100">
              <img src={popupInfo.image_url || "/assets/images/AI.png"} className="w-full h-28 object-cover" />
              <div className="p-4 space-y-3">
                <h3 className="font-bold text-slate-800 text-sm leading-tight">{popupInfo.name}</h3>
                <div className="flex items-center gap-1.5">
                  <div className="flex items-center text-xs font-bold text-yellow-500">
                    <Star className="w-3 h-3 fill-current mr-0.5" /> {popupInfo.star}
                  </div>
                  <span className="text-[10px] text-slate-400">•</span>
                  <span className="text-[10px] font-bold text-slate-500">{popupInfo.type?.[0]}</span>
                </div>
                <button
                  onClick={() => handleOpenModal(popupInfo)}
                  className="w-full py-2 bg-rose-500 text-white text-[11px] font-bold rounded-xl shadow-md flex items-center justify-center gap-2"
                >
                  <Info className="w-3.5 h-3.5" /> Chi tiết nhà hàng
                </button>
              </div>
            </div>
          </Popup>
        )}
      </Map>

      {/* Floating Header UI */}
      <div className="absolute top-6 left-6 z-10 flex flex-col gap-3">
        <div className="bg-white/80 backdrop-blur-md p-4 rounded-2xl shadow-xl border border-white/40">
          <h1 className="text-xl font-black text-slate-800 flex items-center gap-2">
            <Navigation className="w-5 h-5 text-rose-500 fill-current" /> Khám phá Ẩm thực
          </h1>
          <p className="text-[11px] text-slate-500 font-bold uppercase tracking-[0.1em]">
            Dữ liệu độc quyền • {restaurants.length} địa điểm
          </p>
        </div>
        <Link href="/app" className="flex items-center gap-2 w-fit bg-slate-900 text-white px-5 py-3.5 rounded-2xl font-bold text-sm shadow-2xl transition-all group border border-white/10">
          <MessageSquare className="w-4 h-4 text-rose-400" /> Quay lại Chat AI
        </Link>
      </div>

      <RestaurantDetailModal restaurant={selectedResForModal} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}

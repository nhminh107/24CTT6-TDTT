import pandas as pd
import numpy as np
import traceback
import logging
import os
import json
from Back_End.Database.database import ChromaDBManager

class RestaurantFilter:
    _menu_db_manager = None
    def __init__(self, df, prompt, user_lat, user_lng, user_health_profie, max_distance=10.0):
        self.data = df
        self.user_prompt = prompt
        self.user_lat = user_lat
        self.user_lng = user_lng
        self.user_health = user_health_profie
        self.max_distance = max_distance
        
        self.warnings = {
            "Spicy": {
                "potential": "Hệ thống ghi nhận xu hướng vị cay nhẹ (Tiềm ẩn): Dữ liệu phân tích từ mô hình cho thấy một số món ăn có khả năng chứa gia vị cay, người dùng có thể tham khảo việc yêu cầu điều chỉnh mức độ phù hợp với dạ dày.",
                "main": "Mô hình ước tính phong cách vị cay nồng (Chủ đạo): Hệ thống nhận diện quán có xu hướng thiên về các món vị cay đậm, người dùng có thể lưu ý trao đổi trước với nhà bếp để hạn chế kích ứng tiêu hóa."
            },
            "DeepFried_Oily": {
                "potential": "Hệ thống ghi nhận dấu hiệu đồ chiên rán (Tiềm ẩn): Cấu trúc thực đơn có thể bao gồm các thành phần chứa dầu mỡ, mô hình gợi ý góc độ tham khảo ưu tiên các món chế biến thanh đạm.",
                "main": "Mô hình ước tính tỷ lệ dầu mỡ cao (Chủ đạo): Dữ liệu cho thấy danh mục chính chủ yếu là các món chiên xào, hệ thống đề xuất việc cân nhắc lựa chọn tùy theo trạng thái tiêu hóa hiện tại."
            },
            "High_Sugar": {
                "potential": "Hệ thống ghi nhận dấu hiệu hàm lượng đường (Tiềm ẩn): Thuật toán ước tính nước sốt hoặc đồ uống đi kèm có khả năng mang vị ngọt, người dùng có thể tham khảo việc lưu ý người bán điều chỉnh lượng đường.",
                "main": "Mô hình ước tính hàm lượng đường cao (Chủ đạo): Theo phân tích văn bản thực đơn, hệ thống nhận diện lượng đường có xu hướng xuất hiện nhiều, gợi ý góc độ tham khảo yêu cầu để riêng nước sốt."
            },
            "Refined_Carbs": {
                "potential": "Hệ thống ghi nhận xu hướng tinh bột tinh chế (Tiềm ẩn): Quán có khả năng sử dụng các nguyên liệu như bún, mì trắng, bánh mì; mô hình gợi ý việc tham khảo các lựa chọn thay thế nếu có.",
                "main": "Mô hình ước tính thành phần tinh bột nhanh (Chủ đạo): Thuật toán nhận diện thực đơn có xu hướng tập trung vào nhóm tinh bột hấp thu nhanh, người dùng có thể lưu ý kết hợp thêm rau xanh để phù hợp với chế độ ăn."
            },
            "High_Sodium": {
                "potential": "Hệ thống ghi nhận dấu hiệu chứa nhiều muối (Tiềm ẩn): Mô hình ước tính một số món ăn có khả năng mang hàm lượng natri/muối đáng kể, người dùng có thể tham khảo tư vấn từ nhân viên.",
                "main": "Mô hình ước tính xu hướng chứa nhiều muối (Chủ đạo): Dựa trên dữ liệu văn bản, phong cách ẩm thực tại đây có khả năng sử dụng lượng muối cao, hệ thống đề xuất góc độ cân nhắc tùy thuộc nhu cầu kiêng cữ cá nhân."
            },
            "Red_Meat": {
                "potential": "Hệ thống ghi nhận khả năng xuất hiện thịt đỏ (Tiềm ẩn): Thuật toán nhận diện tín hiệu món ăn chứa thịt bò hoặc heo, người dùng có thể lưu ý kiểm tra thêm phần nước dùng hoặc nước sốt đi kèm.",
                "main": "Mô hình ước tính danh mục chính chứa thịt đỏ (Chủ đạo): Hệ thống phân tích thấy các món chính thiên về thịt bò hoặc heo, người dùng có thể đối chiếu lại với trạng thái khớp hoặc lộ trình Gout hiện tại."
            },
            "Seafood": {
                "potential": "Hệ thống ghi nhận khả năng chứa hải sản (Tiềm ẩn): Dữ liệu từ mô hình cho thấy một số món ăn hoặc nước dùng có thể có thành phần từ tôm, mực, cá; người dùng có thể tham khảo thông tin từ quán.",
                "main": "Mô hình ước tính chuyên hải sản (Chủ đạo): Hệ thống nhận diện quán tập trung vào nguồn nguyên liệu biển, đề xuất góc độ đối chiếu với tiền sử kích ứng hoặc chỉ số axit uric của cơ thể."
            },
            "Alcohol_Pub": {
                "potential": "Hệ thống ghi nhận không gian có thức uống cồn (Tiềm ẩn): Theo phân tích dữ liệu, địa điểm có phục vụ kèm bia rượu, mô hình gợi ý việc tham khảo danh mục nước ép hoặc trà nếu cần.",
                "main": "Mô hình ước tính không gian chuyên đồ uống cồn (Chủ đạo): Thuật toán phân tích thấy địa điểm thiên về mô hình pub/bia rượu, đề xuất người dùng đối chiếu với lộ trình kiêng chất kích thích cá nhân."
            },
            "Peanuts_Nuts": {
                "potential": "Hệ thống ghi nhận khả năng chứa đậu phộng & hạt (Tiềm ẩn): Nhận diện từ mô hình cho thấy các loại hạt có xu hướng xuất hiện trong nước chấm hoặc món trộn, gợi ý việc lưu ý người bán nếu cần phòng ngừa kích ứng.",
                "main": "Mô hình ước tính thành phần chứa đậu phộng/hạt (Chủ đạo): Dữ liệu văn bản cho thấy nguy cơ trùng khớp cao với các loại hạt, đề xuất người dùng đối chiếu nghiêm ngặt với hồ sơ phản vệ cá nhân."
            },
            "Dairy_Product": {
                "potential": "Hệ thống ghi nhận dấu hiệu chứa sữa & bơ (Tiềm ẩn): Thuật toán ước tính có khả năng sử dụng thành phần từ sữa hoặc phô mai khi chế biến, người dùng có thể lưu ý xác nhận lại để đảm bảo tính phù hợp.",
                "main": "Mô hình ước tính thành phần chủ đạo từ sữa (Chủ đạo): Hệ thống nhận diện xu hướng sử dụng sữa/bơ trong món chính, đề xuất góc độ cân nhắc đối với người dùng có hội chứng nhạy cảm lactose."
            },
            "Gluten_Present": {
                "potential": "Hệ thống ghi nhận khả năng chứa Gluten/Bột mì (Tiềm ẩn): Dữ liệu phân tích cho thấy có xu hướng sử dụng bột mì trong chế biến thực phẩm, mô hình gợi ý việc tham khảo các tùy chọn thay thế.",
                "main": "Mô hình ước tính thành phần chứa Gluten (Chủ đạo): Thuật toán nhận diện món ăn có nguồn gốc từ bột mì/gluten, đề xuất người dùng đối chiếu với mức độ nhạy cảm của hệ tiêu hóa hoặc hội chứng Celiac."
            },
            "Shellfish": {
                "potential": "Hệ thống ghi nhận khả năng chứa hải sản vỏ cứng (Tiềm ẩn): Mô hình ước tính sự xuất hiện của tôm, cua, nghêu, sò trong quy trình hoặc món ăn, người dùng có thể tham khảo việc dặn dò nhà bếp.",
                "main": "Mô hình ước tính thành phần chủ đạo là hải sản vỏ cứng (Chủ đạo): Hệ thống nhận diện danh mục chính tập trung vào tôm, cua, nghêu, sò; đề xuất người dùng chủ động đối chiếu với tiền sử dị ứng cá nhân."
            }
        }
        # Các tag này nếu người dùng chọn ăn xả láng cũng phải loại bỏ
        self.CRITICAL_ALLERGY_TAGS=["Peanuts_Nuts", "Gluten_Present", "Dairy_Product", "Seafood", "Shellfish"] 
        

    def _get_menu_db_manager(self):
        if RestaurantFilter._menu_db_manager is None:
            RestaurantFilter._menu_db_manager = ChromaDBManager()
        return RestaurantFilter._menu_db_manager

    def _normalize_menu_query(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            parts = [str(item).strip() for item in value if str(item).strip()]
            return ", ".join(parts)
        return ""

    def _extract_menu_query(self, meal_info):
        if not isinstance(meal_info, dict):
            return ""
        for key in ("menu_query", "dish_query", "food_query", "menu", "dish", "food"):
            query = self._normalize_menu_query(meal_info.get(key))
            if query:
                return query
        return ""

    def menu_filter(self, meal_df, menu_query):
        if meal_df is None or meal_df.empty:
            return meal_df
        menu_query = self._normalize_menu_query(menu_query).lower()
        if not menu_query:
            return meal_df
        if 'id' not in meal_df.columns:
            return meal_df

        # --- Bước 1: Lọc cứng dựa trên subset tokens ---
        query_tokens = set(menu_query.split())
        matched_ids_subset = set()
        
        if 'menu' in meal_df.columns:
            for _, row in meal_df.iterrows():
                menu_list = row['menu']
                if isinstance(menu_list, list):
                    for item in menu_list:
                        item_lower = str(item).lower()
                        item_tokens = set(item_lower.split())
                        # Kiểm tra subset xuôi hoặc ngược
                        if query_tokens.issubset(item_tokens) or item_tokens.issubset(query_tokens):
                            matched_ids_subset.add(str(row['id']))
                            break
        
        if matched_ids_subset:
            print(f"[MENU_FILTER_DEBUG] Found {len(matched_ids_subset)} matches via SUBSET MATCHING for '{menu_query}'.")
            return meal_df[meal_df['id'].astype(str).isin(matched_ids_subset)]

        # --- Bước 2: Nếu lọc cứng không có kết quả, dùng ChromaDB (Semantic Search) ---
        print(f"[MENU_FILTER_DEBUG] No subset match found for '{menu_query}'. Falling back to ChromaDB.")

        candidate_ids = meal_df['id'].astype(str).dropna().unique().tolist()
        if not candidate_ids:
            return meal_df

        n_results = 20 
        where = {"restaurant_id": {"$in": candidate_ids}}

        try:
            db_manager = self._get_menu_db_manager()
            result = db_manager.search_menu(menu_query, n_results=n_results, where=where)
        except Exception:
            return meal_df

        matched_ids = set()
        metadatas = result.get("metadatas") or []
        distances = result.get("distances") or []
        
        # Ngưỡng khoảng cách: 0.0 là giống hệt, > 1.0 là khác biệt hoàn toàn.
        # Với model MiniLM, ngưỡng 0.4 - 0.5 là mức độ liên quan khá cao.
        DISTANCE_THRESHOLD = 0.8

        for i, meta_list in enumerate(metadatas):
            for j, meta in enumerate(meta_list):
                if not meta: continue
                
                # Kiểm tra độ tương đồng
                dist = distances[i][j] if i < len(distances) and j < len(distances[i]) else 0
                if dist > DISTANCE_THRESHOLD:
                    continue # Bỏ qua các món không thực sự liên quan
                    
                rid = meta.get("restaurant_id")
                if rid:
                    matched_ids.add(str(rid))

        if not matched_ids:
            # Fallback nếu không có metadata nhưng có IDs
            raw_ids = result.get("ids") or []
            raw_dists = result.get("distances") or []
            for i, id_list in enumerate(raw_ids):
                for j, item_id in enumerate(id_list):
                    if not isinstance(item_id, str): continue
                    
                    dist = raw_dists[i][j] if i < len(raw_dists) and j < len(raw_dists[i]) else 0
                    if dist > DISTANCE_THRESHOLD: continue
                    
                    if "__menu__" in item_id:
                        matched_ids.add(item_id.split("__menu__", 1)[0])

        if not matched_ids:
            print(f"[MENU_FILTER_DEBUG] No relevant matches found for '{menu_query}' (Threshold {DISTANCE_THRESHOLD}). Returning empty list.")
            return meal_df.iloc[0:0]

        filtered = meal_df[meal_df['id'].astype(str).isin(matched_ids)]
        print(f"[MENU_FILTER_DEBUG] Found relevant matches for '{menu_query}' via ChromaDB: {len(filtered)} restaurants.")
        return filtered

    def _calculate_distance(self, df):
        """
        Tính khoảng cách Haversine giữa người dùng và tất cả các nhà hàng.
        Đây là cách tối ưu tốc độ nhất khi dùng Pandas.
        """
        # Bán kính Trái Đất (km)
        R = 6371.0 

        # Chuyển đổi sang radian
        lat1, lng1 = np.radians(self.user_lat), np.radians(self.user_lng)
        lat2, lng2 = np.radians(df['lat']), np.radians(df['lng'])

        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        
        return R * c
        
    def _apply_general_filters(self):
        """
        Lọc các tiêu chí chung (áp dụng cho mọi quán) trước khi chia bữa ăn.
        """
        # 0. Lọc sức khỏe trước khi tiến hành lọc những cái khác
        safe_df = self.run_health_conditions_filter(self.data)
        print(f"[FILTER_DEBUG] Candidates after Health Filter: {len(safe_df)}")
        
        if safe_df.empty:
            return safe_df

        filtered_df = safe_df.copy()
        
        # 1. Lọc khoảng cách
        if self.user_lat and self.user_lng:
            filtered_df['distance'] = self._calculate_distance(filtered_df)
            filtered_df = filtered_df[filtered_df['distance'] <= self.max_distance]
            print(f"[FILTER_DEBUG] Candidates after Distance Filter ({self.max_distance}km): {len(filtered_df)}")

        if filtered_df.empty: return filtered_df

        # 2. Lọc ngân sách (Theo feedback: giá > 0.6 * budget là loại)
        if self.user_prompt.get('budget'):
            max_allowed_price = 0.6 * self.user_prompt['budget']
            filtered_df = filtered_df[filtered_df['avg_price'] <= max_allowed_price]
            print(f"[FILTER_DEBUG] Candidates after Budget Filter: {len(filtered_df)}")

        if filtered_df.empty: return filtered_df

        # 3. Lọc độ cay
        user_shu = self.user_prompt.get('shu')
        if user_shu:
            filtered_df = filtered_df[(filtered_df['shu'] >= 1) & (filtered_df['shu'] <= user_shu)]
            print(f"[FILTER_DEBUG] Candidates after Spicy Filter: {len(filtered_df)}")
        
        if filtered_df.empty: return filtered_df

        return filtered_df

    
    # Lọc bỏ những quán mà user phải tránh
    def run_health_codition_first_step(self, raw_data):
        """
        Lọc các quán có tag chính thuộc các tag mà user phải né
        """
        diet_mode = self.user_health.get("diet_mode", "strict")
        forbidden_tags = set(self.user_health.get("forbidden_tags", []))
        
        print(f"\n[HEALTH_FILTER_LOG] STARTING Health Filter First Step")
        print(f"[HEALTH_FILTER_LOG] User Diet Mode: {diet_mode}")
        print(f"[HEALTH_FILTER_LOG] User Forbidden Tags: {list(forbidden_tags)}")
        print(f"[HEALTH_FILTER_LOG] Critical Allergy Tags list: {self.CRITICAL_ALLERGY_TAGS}")
        print(f"[HEALTH_FILTER_LOG] Initial restaurant count: {len(raw_data)}")

        filtered_res = []
        skipped_count = 0
        
        # casual mode: Lọc nhẹ nhàng hơn nhưng vẫn phải loại bỏ các quán nguy hiểm
        if diet_mode == "casual" or diet_mode is None:
            
            for res in raw_data:
                name = res.get("name", "Unknown")
                main_tags = res.get("main_tag", [])
                
                # Chống crash dữ liệu bẩn (NaN) cho cả Casual Mode
                if isinstance(main_tags, float) or main_tags is None:
                    main_tags = []
                else:
                    main_tags = list(main_tags)
                
                # CHÚ Ý: Logic này cực kỳ quan trọng. 
                # Chỉ SKIP nếu quán có tag nằm trong danh sách NGUY HIỂM VÀ user cũng có tag đó trong FORBIDDEN_TAGS
                is_danger = False
                for tag in main_tags:
                    if tag in self.CRITICAL_ALLERGY_TAGS and tag in forbidden_tags:
                        print(f"[HEALTH_FILTER_LOG] [CASUAL] SKIPPING '{name}': User is allergic to CRITICAL tag '{tag}'")
                        is_danger = True
                        break
                
                if is_danger:
                    skipped_count += 1
                    continue
                    
                filtered_res.append(res)
        
        # strict mode: lọc nghiêm ngặt loại bỏ toàn bộ tag mà user dị ứng
        else:
            for res in raw_data:
                name = res.get("name", "Unknown")
                main_tags = res.get("main_tag", [])
                if isinstance(main_tags, float) or main_tags is None:
                    main_tags = []
                else:
                # Đảm bảo nó là list để không bị lỗi nếu lỡ là kiểu dữ liệu lạ khác
                    main_tags = list(main_tags)
                if not main_tags:
                    filtered_res.append(res)
                    continue
                    
                intersect_tags = [tag for tag in main_tags if tag in forbidden_tags]
                
                # Check critical allergies
                critical_intersection = [tag for tag in intersect_tags if tag in self.CRITICAL_ALLERGY_TAGS]
                if critical_intersection:
                    print(f"[HEALTH_FILTER_LOG] [STRICT] SKIPPING '{name}': Matches CRITICAL allergies {critical_intersection}")
                    skipped_count += 1
                    continue
                    
                # Check ratio
                match_ratio = len(intersect_tags) / len(main_tags)
                if match_ratio >= 0.5:
                    print(f"[HEALTH_FILTER_LOG] [STRICT] SKIPPING '{name}': Tag match ratio {match_ratio:.2f} >= 0.5 (Matched: {intersect_tags})")
                    skipped_count += 1
                    continue
                
                filtered_res.append(res)

        print(f"[HEALTH_FILTER_LOG] COMPLETED. Kept: {len(filtered_res)}, Skipped: {skipped_count}")
        return filtered_res
                    
    # Gán điểm phạt và thêm các notes và warnings cho nhà hàng
    def run_health_condition_second_step(self, data):
        for res in data:
            self.calculate_penalty_health_score(res)
            self.generate_notes(res)
            self.generate_warning(res)
        return data
    
         
        
    
    def run_filter_pipeline(self): 
        base_df = self._apply_general_filters()
        print(f"[FILTER_DEBUG] Total candidates in base_df after general filters: {len(base_df)}")
        result_dict = {}
        
        if base_df.empty:
            return result_dict

        meal_name_map = {
            'any': ['sáng', 'trưa', 'xế', 'chiều', 'tối', 'khuya', 'đêm'],
            'sáng': ['sáng'],
            'trưa': ['trưa'],
            'xế': ['xế', 'chiều', 'trưa', 'tối'],
            'tối': ['tối'],
            'khuya': ['khuya']
        }
        
        type_normalization = {
            'quán nước': ['quán cà phê', 'cà phê', 'trà sữa', 'cafe', 'quán nước']
        }
        
        BLACKLIST = ['Quán nước', 'Trà sữa', 'Bar', 'Pub', 'Ăn vặt', 'Tiệm bánh']
        MAIN_MEALS = ['sáng', 'trưa', 'tối']
        
        meals_detail = self.user_prompt.get('meals_detail', [])
        
        for meal_info in meals_detail:
            meal_key_parser = meal_info.get('meal')
            print(f"\n[FILTER_DEBUG] Processing meal: '{meal_key_parser}'")
            try:
                # 1. Kiểm tra meal_name_map
                meal_name_data = meal_name_map.get(meal_key_parser)
                if not meal_name_data:
                    print(f"[FILTER_DEBUG] Warning: meal_key_parser '{meal_key_parser}' not in meal_name_map.")
                    continue

                meal_names = meal_name_data if isinstance(meal_name_data, list) else [meal_name_data]
                meal_names_lower = [m.lower() for m in meal_names]

                # 2. Lọc base_df theo bữa ăn
                try:
                    if 'meals' not in base_df.columns:
                        print(f"[FILTER_DEBUG] Warning: 'meals' column missing in base_df.")
                        meal_df = base_df.copy()
                    else:
                        meal_df = base_df[
                            base_df['meals'].apply(
                                lambda x: any(m in [str(meal).lower() for meal in x] for m in meal_names_lower)
                                if isinstance(x, list) else False
                            )
                        ].copy()
                    print(f"[FILTER_DEBUG] Candidates for '{meal_key_parser}' after meal name filter: {len(meal_df)}")
                except Exception as e:
                    print(f"[FILTER_DEBUG] Lỗi khi lọc base_df cho bữa {meal_key_parser}: {str(e)}")
                    continue

                if meal_df.empty:
                    result_dict[meal_key_parser] = meal_df
                    continue

                # 3. Lấy req_types an toàn
                req_types = meal_info.get('type', [])

                # 4. Logic lọc theo Type
                try:
                    if req_types:
                        expanded_reqs = []
                        for t in req_types:
                            t_lower = t.lower()
                            expanded_reqs.append(t_lower)
                            if t_lower in type_normalization:
                                expanded_reqs.extend(type_normalization[t_lower])
                        
                        if 'type' not in meal_df.columns:
                            print(f"[FILTER_DEBUG] Warning: 'type' column missing in meal_df for meal {meal_key_parser}.")
                        else:
                            meal_df = meal_df[
                                meal_df['type'].apply(
                                    lambda x: any(any(req in str(item).lower() for req in expanded_reqs) for item in x) 
                                    if isinstance(x, list) else False
                                )
                            ]
                            print(f"[FILTER_DEBUG] Candidates for '{meal_key_parser}' after type filter {req_types}: {len(meal_df)}")
                    else:
                        if meal_key_parser in MAIN_MEALS:
                            if 'type' in meal_df.columns:
                                meal_df = meal_df[
                                    meal_df['type'].apply(
                                        lambda x: not any(b.lower() in str(t).lower() for t in x for b in BLACKLIST) 
                                        if isinstance(x, list) else True
                                    )
                                ]
                                print(f"[FILTER_DEBUG] Candidates for '{meal_key_parser}' after Blacklist filter: {len(meal_df)}")
                except Exception as e:
                    print(f"[FILTER_DEBUG] Lỗi logic lọc Type của {meal_key_parser}: {str(e)}")
                    meal_df = meal_df.iloc[0:0]

                menu_query = self._extract_menu_query(meal_info)
                if menu_query and not meal_df.empty:
                    meal_df = self.menu_filter(meal_df, menu_query)
                    print(f"[FILTER_DEBUG] Candidates for '{meal_key_parser}' after Menu Filter ('{menu_query}'): {len(meal_df)}")

                # Lưu kết quả
                result_dict[meal_key_parser] = meal_df

            except Exception as e:
                print(f"[FILTER_DEBUG] Lỗi không xác định tại meal {meal_key_parser}: {traceback.format_exc()}")
                continue

        return result_dict
    
    def calculate_penalty_health_score(self, res):
        """
        Tính toán điểm penalty tích lũy:
        - main_tag vi phạm: Phạt 10 điểm/tag
        - potential_tag vi phạm thuộc nhóm NGUY HIỂM: Phạt 10 điểm/tag
        - potential_tag vi phạm thuộc nhóm THƯỜNG: Phạt 5 điểm/tag
        """
        # 1. Lấy danh sách tag cấm của user
        forbidden_tags = set(self.user_health.get("forbidden_tags", []))
        
        if not forbidden_tags:
            res["penalty_score"] = 0
            return res
            
        # 2. Lấy danh sách tag của nhà hàng
        main_raw = res.get("main_tag", [])
        potential_raw = res.get("potential_tag", [])

        if not isinstance(main_raw, (list, tuple, set)):
            main_raw = []

        if not isinstance(potential_raw, (list, tuple, set)):
            potential_raw = []

        main_tags = set(main_raw)
        potential_tags = set(potential_raw)
        
        # 3. Tìm các tag vi phạm (Trùng giữa quán và user)
        violated_main = main_tags.intersection(forbidden_tags)
        violated_potential = potential_tags.intersection(forbidden_tags)
        
        
        critical_set = set(self.CRITICAL_ALLERGY_TAGS)
        
        violated_potential_critical = violated_potential.intersection(critical_set)
        violated_potential_normal = violated_potential.difference(critical_set)
        

        WEIGHT_MAIN = 10  
        WEIGHT_POTENTIAL_CRITICAL = 10 
        WEIGHT_POTENTIAL_NORMAL = 5   
        # 6. Tính tổng điểm phạt tích lũy
        total_penalty = (
            (len(violated_main) * WEIGHT_MAIN) +
            (len(violated_potential_critical) * WEIGHT_POTENTIAL_CRITICAL) +
            (len(violated_potential_normal) * WEIGHT_POTENTIAL_NORMAL)
        )
        
        # 7. Lưu lại kết quả
        res["penalty_score"] = total_penalty
        
        return res
    
    def generate_notes(self, res):
        """
        Thêm đánh giá tổng quan và lời khuyên dựa vào điểm số penalty tích lũy.
        Tất cả các phát biểu đều mang tính chất tham khảo, chủ quan từ hệ thống.
        """
        penalty = res.get("penalty_score", 0.0)
        notes = []
        
        # MỐC 1: Nguy hiểm tuyệt đối (Dính combo nhiều món chính hoặc nhiều chất gây dị ứng nặng)
        if penalty >= 40.0:
            notes.append(
                "📊 Đánh giá tổng quan: Hệ thống ước tính mức độ tương thích rất thấp. Dữ liệu thực đơn hiện tại của quán cho thấy có xu hướng xuất hiện nhiều thành phần được phân loại là không phù hợp với hồ sơ sức khỏe của bạn."
            )
            notes.append(
                "🚨 Khuyên dùng: Góc độ tham khảo từ ứng dụng đề xuất bạn nên cân nhắc kỹ lưỡng và có thể ưu tiên tìm kiếm các thực đơn khác có chỉ số phù hợp cao hơn."
            )

        # MỐC 2: Rủi ro cực cao (Ví dụ: dính từ 3 món chính hoặc 3 tag potential nguy hiểm trở lên)
        elif penalty >= 30.0:
            notes.append(
                "📊 Đánh giá tổng quan: Hệ thống ghi nhận chỉ số rủi ro cao. Theo phân tích từ mô hình, danh mục món ăn tại đây có khả năng chứa các nhóm chất mà bạn đang cần hạn chế."
            )
            notes.append(
                "💡 Khuyên dùng: Bạn có thể tham khảo ý kiến từ phía nhà hàng về thành phần chi tiết của món ăn trước khi gọi để có thông tin chính xác nhất."
            )

        # MỐC 3: Nguy cơ trung bình - cao (Ví dụ: Dính combo 1 main + 1 potential nguy hiểm = 20đ, cộng thêm tag thường)
        elif penalty >= 20.0:
            notes.append(
                "📊 Đánh giá tổng quan: Ghi nhận dấu hiệu rủi ro đáng kể. Thuật toán ước tính rằng một phần thực đơn hoặc các món phổ biến tại đây có xu hướng thiên về nhóm thực phẩm thuộc diện cần điều chỉnh giảm."
            )
            notes.append(
                "💡 Khuyên dùng: Đề xuất bạn chủ động sàng lọc và có thể trao đổi các tùy chỉnh riêng với nhà bếp để phù hợp hơn với nhu cầu cá nhân."
            )

        # MỐC 4: Nguy cơ trung bình (Ví dụ: Dính 1 main vi phạm hoặc 1 potential nguy hiểm = 10đ)
        elif penalty >= 10.0:
            notes.append(
                "📊 Đánh giá tổng quan: Thuật toán đưa ra lưu ý nhỏ. Hệ thống nhận diện một số món ăn có thể chứa thành phần chưa tối ưu cho chế độ kiêng cữ hoặc hồ sơ sức khỏe được cấu hình."
            )
            notes.append(
                "💡 Khuyên dùng: Bạn có thể ưu tiên xem xét các món ăn có phương thức chế biến đơn giản hoặc các món phụ ít thành phần hỗn hợp."
            )

        # MỐC 5: Nhắc nhở nhẹ (Ví dụ: Chỉ dính 1 tag thường ở món phụ potential = 5đ)
        elif penalty >= 5.0:
            notes.append(
                "📊 Đánh giá tổng quan: Chỉ số rủi ro ở mức thấp. Hệ thống ước tính chỉ có một vài thành phần rải rác ở nhóm món phụ có thể không tối ưu, nhìn chung thực đơn vẫn cung cấp nhiều sự lựa chọn khác."
            )

        # MỐC 6: Rủi ro siêu nhỏ (Trường hợp điểm số lẻ hoặc tính toán tỷ lệ khác)
        elif penalty > 0.0:
            notes.append(
                "📊 Đánh giá tổng quan: Chỉ số an toàn theo mô hình ở mức cao. Ghi nhận tỷ lệ trùng khớp rủi ro rất nhỏ từ một vài thành phần riêng biệt, không đáng kể đối với tổng thể thực đơn."
            )

        # MỐC 7: Hoàn hảo tuyệt đối (Penalty = 0)
        else:
            notes.append(
                "✅ Đánh giá tổng quan: Thực đơn giả định lý tưởng. Dựa trên dữ liệu văn bản hiện có, hệ thống chưa phát hiện thành phần nào trùng khớp với danh mục cần lưu ý trong hồ sơ sức khỏe của bạn."
            )
            
        # --- BỐ SUNG KHUYẾN CÁO Y TẾ KHÉO LÉO CHỐT HẠ ---
        notes.append(
            "💡 Mẹo nhỏ: Tính năng đánh giá sức khỏe hoạt động như một bộ lọc tự động hỗ trợ bạn nhanh chóng nhận diện thành phần món ăn trên phương diện lý thuyết. Tuy nhiên, ứng dụng không đưa ra lời khuyên y tế và không chịu trách nhiệm pháp lý đối với các tình huống sức khỏe phát sinh. Bạn vui lòng luôn dựa trên cảm nhận thực tế của cơ thể và tham khảo ý kiến chuyên gia khi cần thiết nhé!"
        )
            
        # Gán mảng kết quả vào key "notes" của quán
        res["notes"] = notes
        return res

    def generate_warning(self, res):
        """
        Thêm cảnh báo nguy cơ dựa trên cả main_tag và potential_tag (Quét sạch sành sanh mọi tag).
        """
        warnings_set = set()
        forbidden_tags = set(self.user_health.get("forbidden_tags", []))
        
        main_tags = list(res.get("main_tag", [])) if not isinstance(res.get("main_tag"), float) else []
        potential_tags = list(res.get("potential_tag", [])) if not isinstance(res.get("potential_tag"), float) else []

        # 1. Duyệt tất cả các main_tag vi phạm
        for tag in main_tags:
            if tag in forbidden_tags and tag in self.warnings:
                msg = self.warnings[tag].get("main", f"Cảnh báo: Thành phần món chính chứa {tag} không tốt cho bạn.")
                warnings_set.add(msg)

        # 2. Duyệt tất cả các potential_tag vi phạm
        for tag in potential_tags:
            if tag in forbidden_tags and tag in self.warnings:
                main_msg = self.warnings[tag].get("main")
                if main_msg not in warnings_set:
                    msg = self.warnings[tag].get("potential", f"Lưu ý: Quán có nguy cơ chứa {tag} trong món phụ.")
                    warnings_set.add(msg)

        res["warnings"] = list(warnings_set)
        return res
    def run_health_conditions_filter(self,raw_data):
        restaurants_list = raw_data.to_dict(orient='records')
        data_first = self.run_health_codition_first_step(restaurants_list)
        data_second = self.run_health_condition_second_step(data_first)
        df_filtered = pd.DataFrame(data_second)
        return df_filtered
        


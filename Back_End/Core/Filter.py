import pandas as pd
import numpy as np
import traceback
import logging
import os
import json
from Back_End.Database.database import ChromaDBManager

class RestaurantFilter:
    _menu_db_manager = None
    def __init__(self, df, prompt, user_lat, user_lng,user_health_profie):
        self.data = df
        self.user_prompt = prompt
        self.user_lat = user_lat
        self.user_lng = user_lng
        self.user_health=user_health_profie
        
        self.warnings = {
            "Spicy": {
                "potential": "Vị cay nồng (Tiềm ẩn): Món ăn có thể cay. Bạn nên dặn nhân viên làm mức nhẹ nhất hoặc không cay để bảo vệ dạ dày.",
                "main": "Món cay nồng (Chủ đạo): Quán chuyên vị cay đậm. Nên chủ động yêu cầu nhà bếp giảm độ cay để tránh kích ứng dạ dày."
            },
            "DeepFried_Oily": {
                "potential": "Đồ chiên rán (Tiềm ẩn): Thực đơn có thể nhiều dầu mỡ. Bạn nên nhờ đầu bếp giảm dầu hoặc ưu tiên chọn món luộc/hấp.",
                "main": "Nhiều dầu mỡ (Chủ đạo): Các món chủ yếu là chiên xào. Nên cân nhắc đổi sang món thanh đạm để tránh đầy bụng, nóng trong."
            },
            "High_Sugar": {
                "potential": "Hàm lượng đường (Tiềm ẩn): Nước sốt hoặc đồ uống có thể khá ngọt. Hãy nhờ người bán giảm ngọt tối đa khi gọi món.",
                "main": "Hàm lượng đường (Chủ đạo): Thực đơn chứa lượng đường rất cao. Bạn hãy yêu cầu nhân viên để riêng nước sốt hoặc chọn dòng không đường."
            },
            "Refined_Carbs": {
                "potential": "Tinh bột tinh chế (Tiềm ẩn): Quán chủ yếu dùng bún, mì trắng, bánh mì. Hãy hỏi nhân viên xem có thể đổi sang bún lứt hoặc rau không.",
                "main": "Tinh bột nhanh (Chủ đạo): Thực đơn nhiều tinh bột hấp thu nhanh. Bạn nên ăn kèm nhiều rau xanh để tránh làm tăng đường huyết đột ngột."
            },
            "Low_GI_Diet": {
                "potential": "Chế độ Low-GI (Gợi ý): Có sẵn các lựa chọn thực phẩm nguyên cám. Hãy nhờ nhân viên tư vấn các món ít tinh bột hoặc không đường.",
                "main": "Chế độ ăn lành mạnh (Điểm cộng): Thực đơn chuẩn ăn kiêng, rất tốt cho việc ổn định đường huyết và duy trì vóc dáng."
            },
            "Red_Meat": {
                "potential": "Thịt đỏ (Tiềm ẩn): Có thể có món chứa thịt bò, heo. Bạn nên nhờ nhân viên kiểm tra xem nước dùng hoặc món xào có lẫn thịt đỏ không.",
                "main": "Thịt đỏ (Chủ đạo): Thực đơn chính chứa nhiều thịt bò, heo. Không phù hợp nếu bạn đang trong giai đoạn sưng đau Gout."
            },
            "Seafood": {
                "potential": "Hải sản (Tiềm ẩn): Có thể có hải sản. Hãy nhờ nhân viên kiểm tra xem nước dùng hoặc nước sốt có nấu từ tôm, khô mực không.",
                "main": "Chuyên hải sản (Chủ đạo): Nguy cơ cao gây dị ứng hoặc tăng axit uric (Gout). Bạn nên chọn các nhóm món khác thay thế."
            },
            "Alcohol_Pub": {
                "potential": "Thức uống có cồn (Tiềm ẩn): Không gian có phục vụ bia rượu. Bạn nên hỏi menu nước ép hoặc trà lành tính để thay thế.",
                "main": "Quán nước có cồn (Chủ đạo): Đây là không gian pub/bia rượu. Không phù hợp với chế độ kiêng chất kích thích hoặc lộ trình thải độc."
            },
            "Peanuts_Nuts": {
                "potential": "Đậu phộng & Hạt (Tiềm ẩn): Quán có thể dùng hạt trong nước chấm, món trộn. Hãy dặn người bán bỏ qua để phòng dị ứng.",
                "main": "Chứa đậu phộng/Hạt (Chủ đạo): Món ăn thành phần chứa hạt nguy cơ cao. Tuyệt đối không dùng nếu bạn có tiền sử sốc phản vệ."
            },
            "Dairy_Product": {
                "potential": "Sữa & Bơ (Tiềm ẩn): Có thể dùng sữa, phô mai khi chế biến. Hãy nhờ nhân viên xác nhận món không chứa sữa (Dairy-free).",
                "main": "Thành phần từ sữa (Chủ đạo): Món ăn chứa sữa/bơ. Cần cân nhắc kỹ nếu cơ thể bạn có hội chứng bất dung nạp lactose gây đau bụng."
            },
            "Gluten_Present": {
                "potential": "Gluten / Bột mì (Tiềm ẩn): Quán có thể dùng bột mì trong chế biến. Hãy nhờ tư vấn các món thuần túy không gluten để an tâm hơn.",
                "main": "Chứa Gluten (Chủ đạo): Món ăn chứa bột mì/gluten. Không thích hợp cho người có hệ tiêu hóa nhạy cảm hoặc mắc hội chứng Celiac."
            },
            "Shellfish": {
                "potential": "Hải sản vỏ cứng (Tiềm ẩn): Có thể có tôm, cua, nghêu, sò. Hãy dặn người bán tránh dùng chung chảo hoặc dính vụn thức ăn.",
                "main": "Hải sản vỏ cứng (Chủ đạo): Thành phần chứa tôm, cua, nghêu, sò. Cân nhắc kỹ nếu bạn từng có tiền sử dị ứng nghiêm trọng nhóm này."
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
        menu_query = self._normalize_menu_query(menu_query)
        if not menu_query:
            return meal_df
        if 'id' not in meal_df.columns:
            return meal_df

        candidate_ids = meal_df['id'].astype(str).dropna().unique().tolist()
        if not candidate_ids:
            return meal_df

        # Ép trả về số lượng hợp lý: lấy top 15-20 kết quả liên quan nhất thay vì nhân 3
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
        print(f"[MENU_FILTER_DEBUG] Found relevant matches for '{menu_query}': {len(filtered)} restaurants.")
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
        filtered_df = safe_df.copy()
        
        # 1. Lọc khoảng cách không quá 15km
        if self.user_lat and self.user_lng:
            filtered_df['distance'] = self._calculate_distance(filtered_df)
            filtered_df = filtered_df[filtered_df['distance'] <= 15]
            print(f"[FILTER_DEBUG] Candidates after Distance Filter (15km): {len(filtered_df)}")

        # 2. Lọc ngân sách (Theo feedback: giá > 0.6 * budget là loại)
        if self.user_prompt.get('budget'):
            max_allowed_price = 0.6 * self.user_prompt['budget']
            filtered_df = filtered_df[filtered_df['avg_price'] <= max_allowed_price]
            print(f"[FILTER_DEBUG] Candidates after Budget Filter: {len(filtered_df)}")

        # 3. Lọc độ cay
        user_shu = self.user_prompt.get('shu')
        if user_shu:
            filtered_df = filtered_df[(filtered_df['shu'] >= 1) & (filtered_df['shu'] <= user_shu)]
            print(f"[FILTER_DEBUG] Candidates after Spicy Filter: {len(filtered_df)}")
        
        # 4. Lọc theo địa điểm
        if self.user_prompt.get('location_pref'):
            loc = self.user_prompt['location_pref']
            filtered_df = filtered_df[filtered_df['address'].str.contains(loc, case=False, na=False)]
            print(f"[FILTER_DEBUG] Candidates after Location Pref Filter: {len(filtered_df)}")
            
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
        
        # strict mode: Lọc kỹ dựa trên tỷ lệ và các dị ứng nguy hiểm
        if diet_mode == "strict" or diet_mode is None:
            for res in raw_data:
                name = res.get("name", "Unknown")
                main_tags = res.get("main_tag", [])
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
        
        # casual mode: Chỉ né những tag nguy hiểm về tính mạng MÀ USER CÓ DỊ ỨNG
        else:
            for res in raw_data:
                name = res.get("name", "Unknown")
                main_tags = res.get("main_tag", [])
                
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
        
        meal_name_map = {
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
        
        result_dict = {}

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
                            raise KeyError(f"DataFrame thiếu cột 'type'.")

                        meal_df = meal_df[
                            meal_df['type'].apply(
                                lambda x: any(any(req in str(item).lower() for req in expanded_reqs) for item in x) 
                                if isinstance(x, list) else False
                            )
                        ]
                        print(f"[FILTER_DEBUG] Candidates for '{meal_key_parser}' after type filter {req_types}: {len(meal_df)}")
                    else:
                        if meal_key_parser in MAIN_MEALS:
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
                if menu_query:
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
        Tính toán điểm penalty dựa vào các potential_tag
        """
        # 1. Lấy danh sách tag cấm của user (chuyển sang set để tính toán nhanh hơn)
        forbidden_tags = set(self.user_health.get("forbidden_tags", []))
        
        # 2. Lấy danh sách potential_tag của nhà hàng hiện tại
        potential_tags = set(res.get("potential_tag", []))
        
        # 3. Tìm các tag trùng nhau giữa potential_tag và forbidden_tags
        violated_tags = potential_tags.intersection(forbidden_tags)
        
        # 4. Tính toán điểm phạt (Ví dụ: mỗi tag trùng phạt 10 điểm)
        penalty_per_tag = 5 
        total_penalty = len(violated_tags) * penalty_per_tag
        
        # 5. Thêm key mới vào trực tiếp object 'res'
        res["penalty_score"] = total_penalty
        
        return res
    
    def generate_notes(self, res):
        """
        Thêm note dựa vào điểm penalty
        """
        penalty = res.get("penalty_score", 0.0)
        notes = []
        
        if penalty >= 35.0:
            notes.append(
                "📊 Đánh giá tổng quan: Mức độ rủi ro tối đa. Thực đơn của quán hoàn toàn xung đột với hồ sơ sức khỏe hiện tại. Bạn nên cân nhắc đổi quán"
            )

        elif penalty >= 30.0:
            notes.append(
                "📊 Đánh giá tổng quan: Nguy cơ cao. Khả năng tìm được món an toàn tại quán là rất thấp."
            )

        elif penalty >= 25.0:
            notes.append(
                "📊 Đánh giá tổng quan: Nguy cơ trung bình - cao. Cần cực kỳ cẩn trọng nếu bắt buộc phải dùng bữa."
            )

        elif penalty >= 20.0:
            notes.append(
                "📊 Đánh giá tổng quan: Rủi ro đáng kể. Phần lớn thực đơn thiên về nhóm món bạn nên hạn chế."
            )
            notes.append(
                "💡 Khuyên dùng: Hãy sàng lọc món thật kỹ và trao đổi rõ với nhà bếp trước khi gọi."
            )

        elif penalty >= 15.0:
            notes.append(
                "📊 Đánh giá tổng quan: Có khá nhiều món không phù hợp với chế độ ăn hoặc bệnh lý của bạn."
            )
            notes.append(
                "💡 Khuyên dùng: Ưu tiên chọn các món hấp, luộc hoặc các nhóm món phụ thuần túy."
            )

        elif penalty >= 10.0:
            notes.append(
                "📊 Đánh giá tổng quan: Cần lưu ý. Quán có một số thành phần nên tránh hoặc cần chủ động điều chỉnh khi gọi món."
            )

        elif penalty >= 5.0:
            notes.append(
                "📊 Đánh giá tổng quan: Nhắc nhở nhẹ. Một vài thành phần có thể không tối ưu, nhưng quán vẫn có nhiều lựa chọn an toàn thay thế."
            )

        elif penalty > 0.0:
            notes.append(
                "📊 Đánh giá tổng quan: Tương đối an toàn. Chỉ có rủi ro nhỏ từ một vài món cụ thể, chọn món hợp lý là có thể dùng tốt."
            )

        else:
            notes.append(
                "✅ THỰC ĐƠN LÝ TƯỞNG: Không phát hiện thành phần đáng lo ngại nào đối với hồ sơ sức khỏe của bạn."
            )
            notes.append(
                "🥗 Rất phù hợp cho chế độ ăn lành mạnh, eat-clean hoặc kiểm soát dinh dưỡng ổn định."
            )
            
        # Gán mảng kết quả vào key "notes" của quán
        res["notes"] = notes
        return res

    def generate_warning(self,res):
        """
        Thêm cảnh báo dựa vào potential_tag
        """
        
        warnings = []
        forbidden_tags = self.user_health.get("forbidden_tags", [])
    
        # 2. Duyệt qua từng potential_tag của quán ăn
        for tag in res.get("potential_tag", []):
            # Nếu tag tiềm ẩn này nằm trong danh sách cấm của user và có trong cấu hình warning
            if tag in forbidden_tags and tag in self.warnings:
                # Lấy câu cảnh báo loại "potential"
                msg = self.warnings[tag]["potential"]
                warnings.append(msg)
                
        # 3. Gán mảng kết quả vào key "warnings" của res giống như notes
        res["warnings"] = warnings
        return res
    def run_health_conditions_filter(self,raw_data):
        restaurants_list = raw_data.to_dict(orient='records')
        data_first = self.run_health_codition_first_step(restaurants_list)
        data_second = self.run_health_condition_second_step(data_first)
        df_filtered = pd.DataFrame(data_second)
        return df_filtered
        


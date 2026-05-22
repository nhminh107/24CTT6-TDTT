import pandas as pd
import numpy as np
import traceback
import logging
import os
import json 

# Khi khởi tạo Class thì chuyền cái này vô, viết các Endpoints trong routes.py để lấy từ Firebase
user_heath_profie_mockup={
        "user_id": "24120417",
        "updated_at": "2026-05-21T15:50:00Z",
        "diet_mode": "strict", 
        "more_description": "Đôi khi tôi hay bị nóng trong người và mọc mụn",
        "raw_selections": {
            "selected_conditions": [
            "Gout",
            "Dạ dày"
            ],
            "selected_allergies": [
            "Đậu phộng",
            "Bột mì"
            ]
        },
        "forbidden_tags": [
            "Red_Meat",
            "Seafood",
            "Alcohol_Pub",
            "Shellfish",
            "Spicy",
            "DeepFried_Oily",
            "Peanuts_Nuts",
            "Gluten_Present"
        ]
    }   




class RestaurantFilter:
    def __init__(self, df, prompt, user_lat, user_lng,user_health_profie):
        self.data = df
        self.user_prompt = prompt
        self.user_lat = user_lat
        self.user_lng = user_lng
        self.user_health=user_health_profie
        
        self.warnings={
                "Spicy": {
                    "potential": "Nhà hàng này có thể có vị cay nồng đặc trưng, hãy dặn nhân viên phục vụ làm mức nhẹ nhất hoặc không cay để bảo vệ dạ dày.",
                    "main": "Quán chuyên các món cay nồng đậm vị, bạn nên chủ động dặn nhà bếp gia giảm độ cay khi gọi món để tránh kích ứng dạ dày."
                },
                "DeepFried_Oily": {
                    "potential": "Nhà hàng này có thể có nhiều món chiên rán, bạn có thể nhờ đầu bếp giảm bớt dầu khi chế biến hoặc ưu tiên chọn các món luộc/hấp.",
                    "main": "Thực đơn chính của quán chứa nhiều dầu mỡ do chiên xào, bạn nên cân nhắc đổi sang các món thanh đạm để tránh đầy bụng, nóng trong."
                },
                "High_Sugar": {
                    "potential": "Quán ăn này có thể sử dụng hàm lượng đường cao trong nước sốt hoặc đồ uống, hãy nhờ người bán giảm ngọt tối đa khi gọi món.",
                    "main": "Quán có thực đơn chứa hàm lượng đường rất cao, bạn hãy yêu cầu nhân viên để riêng nước sốt/nước đường hoặc chọn dòng không đường."
                },
                "Refined_Carbs": {
                    "potential": "Quán này có thể sử dụng nhiều tinh bột tinh chế (bún, mì trắng, bánh mì), hãy hỏi nhân viên xem có thể đổi sang rau hoặc bún lứt không.",
                    "main": "Thực đơn chủ yếu là tinh bột hấp thu nhanh, bạn nên ăn kèm nhiều rau xanh hoặc hạn chế lượng ăn để tránh làm tăng đường huyết đột ngột."
                },
                "Low_GI_Diet": {
                    "potential": "Nhà hàng này có thể có các lựa chọn thực phẩm nguyên cám, hãy nhờ nhân viên tư vấn các món ăn ít tinh bột hoặc không đường.",
                    "main": "Quán này có thực đơn thuần chế độ ăn lành mạnh, rất tốt cho việc ổn định đường huyết và duy trì vóc dáng của bạn."
                },
                "Red_Meat": {
                    "potential": "Nhà hàng này có thể có món chứa thịt đỏ (bò, heo), hãy nhờ nhân viên kiểm tra xem nước dùng hoặc món xào có lẫn thịt đỏ hay không.",
                    "main": "Thực đơn chính chứa thịt đỏ (bò, heo), không phù hợp nếu bạn đang trong giai đoạn sưng đau Gout hoặc cần kiêng purin."
                },
                "Seafood": {
                    "potential": "Nhà hàng này có thể có món chứa hải sản, hãy nhờ nhân viên kiểm tra xem nước dùng hoặc nước sốt có nấu từ tôm/khô mực không.",
                    "main": "Quán chuyên phục vụ hải sản, nguy cơ cao gây kích ứng dị ứng hoặc làm tăng axit uric (Gout), bạn nên chọn món khác thay thế."
                },
                "Alcohol_Pub": {
                    "potential": "Không gian này có thể có phục vụ các thức uống có cồn, bạn nên hỏi nhân viên về menu nước ép hoặc trà lành tính để thay thế.",
                    "main": "Đây là không gian quán nước có cồn (bia, rượu, pub), không phù hợp với chế độ kiêng chất kích thích hoặc lộ trình thải độc của bạn."
                },
                "Peanuts_Nuts": {
                    "potential": "Nhà hàng này có thể sử dụng đậu phộng hoặc hạt trong nước chấm, món trộn; hãy chủ động dặn người bán bỏ qua để tránh dị ứng.",
                    "main": "Món ăn tại đây chứa đậu phộng hoặc các loại hạt nguy cơ dị ứng cao, bạn tuyệt đối không nên dùng nếu có tiền sử sốc phản vệ."
                },
                "Dairy_Product": {
                    "potential": "Quán có thể dùng sữa, bơ hoặc phô mai trong chế biến; hãy nhờ nhân viên xác nhận món ăn thuần chay hoặc không chứa sữa (Dairy-free).",
                    "main": "Thành phần món ăn chứa các sản phẩm từ sữa, bạn cần cân nhắc kỹ nếu cơ thể có hội chứng bất dung nạp lactose gây đau bụng."
                },
                "Gluten_Present": {
                    "potential": "Nhà hàng có thể sử dụng bột mì hoặc các sản phẩm chứa gluten, hãy nhờ nhân viên tư vấn các món thuần túy không có gluten để an tâm hơn.",
                    "main": "Thành phần món ăn chứa bột mì hoặc gluten, không thích hợp cho người có hệ tiêu hóa nhạy cảm hoặc mắc hội chứng Celiac."
                },
                "Shellfish": {
                    "potential": "Nhà hàng này có thể có món chứa hải sản vỏ cứng, hãy nhờ người bán xác nhận món ăn không dùng chung chảo hoặc dính vụn tôm, cua.",
                    "main": "Món ăn chứa hải sản vỏ cứng (tôm, cua, nghêu, sò), cân nhắc kỹ nếu bạn có tiền sử dị ứng nghiêm trọng với nhóm này."
                }
            }
        
        # Các tag này nếu người dùng chọn ăn xả láng cũng phải loại bỏ
        self.CRITICAL_ALLERGY_TAGS=["Peanuts_Nuts", "Gluten_Present", "Dairy_Product", "Seafood", "Shellfish"] 
        

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
        filtered_df = safe_df.copy()
        
        # 1. Lọc khoảng cách không quá 15km
        if self.user_lat and self.user_lng:
            filtered_df['distance'] = self._calculate_distance(filtered_df)
            filtered_df = filtered_df[filtered_df['distance'] <= 15]

        # 2. Lọc ngân sách (Theo feedback: giá > 0.6 * budget là loại)
        # Tức là chỉ giữ lại quán có giá <= 0.6 * budget
        if self.user_prompt.get('budget'):
            max_allowed_price = 0.6 * self.user_prompt['budget']
            filtered_df = filtered_df[filtered_df['avg_price'] <= max_allowed_price]

        # 3. Lọc độ cay (Giữ lại quán có shu trong khoảng [1, x])
        user_shu = self.user_prompt.get('shu')
        if user_shu:
            # Lọc quán có 1 <= shu <= user_shu
            filtered_df = filtered_df[(filtered_df['shu'] >= 1) & (filtered_df['shu'] <= user_shu)]
        
        # 4. Lọc theo địa điểm (dựa trên key 'location_pref' của Parser)
        if self.user_prompt.get('location_pref'):
            loc = self.user_prompt['location_pref']
            filtered_df = filtered_df[filtered_df['address'].str.contains(loc, case=False, na=False)]
            
        return filtered_df

    
    # Lọc bỏ những quán mà user phải tránh
    def run_health_codition_first_step(self, raw_data):
        """
        Lọc các quán có tag chính thuộc các tag mà user phải né,
        hiện tại là chỉ cần 1 tag chung là bỏ,
        có thể làm lại logic là nếu có n tag và n/2 tag chung mới bỏ
        """
        diet_mode= self.user_health.get("diet_mode",None)
        
        # trong trường hợp user chọn ăn nghiêm ngặt hoặc không chọn gì thì mặc định là ăn nghiêm ngặt
        if diet_mode=="strict" or diet_mode is None:
        
            forbidden_tags = self.user_health.get("forbidden_tags", [])
            
            filtered_res = [
                res for res in raw_data
                if not any(tag in forbidden_tags for tag in res.get("main_tag", []))
            ]
            
            return filtered_res
        # trong trường hợp user chọn ăn xả láng thì chỉ né những tag nguy hiển về tính mạng còn cay,dầu mỡ,... thì có thể bỏ qua
        else:
            filtered_res = [
            res for res in raw_data
            if not any(tag in self.CRITICAL_ALLERGY_TAGS for tag in res.get("main_tag", []))
            ]
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
        result_dict = {}
        
        meal_name_map = {
            'sáng': ['sáng'],
            'trưa': ['trưa'],
            # Data hien tai khong co nhan "xế"/"chiều" trong meals,
            # nen map xế ve cac nhan hop le de khong bi rong tap ung vien.
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
            try:
                # 1. Kiểm tra meal_name_map
                meal_name_data = meal_name_map.get(meal_key_parser)
                if not meal_name_data:
                    continue

                meal_names = meal_name_data if isinstance(meal_name_data, list) else [meal_name_data]
                meal_names_lower = [m.lower() for m in meal_names]

                # 2. Try-Except khi lọc base_df theo bữa ăn (bước này dễ lỗi nếu cột 'meals' có giá trị lạ)
                try:
                    meal_df = base_df[
                        base_df['meals'].apply(
                            lambda x: any(m in [str(meal).lower() for meal in x] for m in meal_names_lower)
                            if isinstance(x, list) else False
                        )
                    ].copy()
                except Exception as e:
                    print(f"Lỗi khi lọc base_df cho bữa {meal_key_parser}: {str(e)}")
                    continue

                # 3. Lấy req_types an toàn
                try:
                    req_types = meal_info.get('type', [])
                except Exception as e:
                    print(f"Lỗi khi truy cập 'type' trong meal_info: {e}")
                    req_types = []

                # 4. Logic lọc theo Type (Nghi phạm chính gây lỗi 'type')
                try:
                    if req_types:
                        expanded_reqs = []
                        for t in req_types:
                            t_lower = t.lower()
                            expanded_reqs.append(t_lower)
                            if t_lower in type_normalization:
                                expanded_reqs.extend(type_normalization[t_lower])
                        
                        # Bắt lỗi nếu DataFrame không có cột 'type'
                        if 'type' not in meal_df.columns:
                            raise KeyError(f"DataFrame thiếu cột 'type'. Các cột hiện có: {meal_df.columns.tolist()}")

                        meal_df = meal_df[
                            meal_df['type'].apply(
                                lambda x: any(any(req in str(item).lower() for req in expanded_reqs) for item in x) 
                                if isinstance(x, list) else False
                            )
                        ]
                    else:
                        if meal_key_parser in MAIN_MEALS:
                            if 'type' not in meal_df.columns:
                                raise KeyError("DataFrame thiếu cột 'type' khi lọc Blacklist.")
                                
                            meal_df = meal_df[
                                meal_df['type'].apply(
                                    lambda x: not any(b.lower() in str(t).lower() for t in x for b in BLACKLIST) 
                                    if isinstance(x, list) else True
                                )
                            ]
                except KeyError as ke:
                    print(f"LỖI CẤU TRÚC: {str(ke)}")
                    # Bạn có thể quyết định skip meal này hoặc gán df rỗng
                    meal_df = meal_df.iloc[0:0] 
                except Exception as e:
                    print(f"Lỗi logic lọc Type của {meal_key_parser}: {traceback.format_exc()}")
                    meal_df = meal_df.iloc[0:0]

                # Lưu kết quả
                result_dict[meal_key_parser] = meal_df

            except Exception as e:
                # Catch-all cho một vòng lặp meal để không làm sập toàn bộ request
                print(f"Lỗi không xác định tại meal {meal_key_parser}: {traceback.format_exc()}")
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
        
def main():
    current_file_path = os.path.abspath(__file__)
    core_dir = os.path.dirname(current_file_path)     
    backend_dir = os.path.dirname(core_dir)            
    project_root = os.path.dirname(backend_dir)       


    data_path = os.path.join(project_root, 'Back_End', 'Database', 'test.json')


    if not os.path.exists(data_path):
        print(f"❌ Không tìm thấy cơ sở dữ liệu quán ăn tại: {data_path}")
    else:
        df_raw = pd.read_json(data_path, encoding='utf-8', dtype={'id': str})
        print(f"✅ Đã đọc thành công dữ liệu từ file JSON!")
        res_filter=RestaurantFilter(df=df_raw,prompt=[],user_lat=0,user_lng=0,user_health_profie=user_heath_profie_mockup)
        
        restaurants_list = df_raw.to_dict(orient='records')
    
        # Truyền danh sách đã chuyển đổi này vào hàm filter thay vì truyền trực tiếp df_raw
        data_first = res_filter.run_heath_codition_first_step(restaurants_list)
        # Chạy tiếp bước 2 với dữ liệu đã lọc sạch ở bước 1
        data_second = res_filter.run_heath_condition_second_step(data_first)
        df_filtered = pd.DataFrame(data_second)
        return df_filtered
if __name__ == "__main__":
    main()



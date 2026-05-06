import pandas as pd

class RestaurantFilter:
    def __init__(self, df, prompt):
        self.data = df 
        self.user_prompt = prompt
        
    def _apply_general_filters(self):
        """
        Lọc các tiêu chí chung (áp dụng cho mọi quán) trước khi chia bữa ăn.
        """
        filtered_df = self.data.copy()
        
        # 1. Lọc theo địa điểm (dựa trên key 'location_pref' của Parser)
        if self.user_prompt.get('location_pref'):
            loc = self.user_prompt['location_pref']
            filtered_df = filtered_df[filtered_df['address'].str.contains(loc, case=False, na=False)]
            
        # 2. Lọc theo giá (Lấy trung bình quán không được vượt quá tổng Budget)
        if self.user_prompt.get('budget'):
            budget = self.user_prompt['budget']
            filtered_df = filtered_df[filtered_df['avg_price'] <= budget]
            
        return filtered_df

    def run_filter_pipeline(self): 
        # Bước 1: Lọc dữ liệu tổng quan
        base_df = self._apply_general_filters()
        
        # Bước 2: Chuẩn bị Dictionary kết quả rỗng
        result_dict = {}
        
        # Mapping để đồng bộ tên bữa ăn từ LLMParser sang Dataset JSON 
        meal_name_map = {
            'sáng': 'Sáng',
            'trưa': 'Trưa',
            'xế': 'Chiều',
            'tối': 'Tối',
            'khuya': 'Khuya'
        }
        
        # Bước 3: Lọc chi tiết theo từng bữa ăn có trong meals_detail
        meals_detail = self.user_prompt.get('meals_detail', [])
        
        for meal_info in meals_detail:
            meal_key_parser = meal_info.get('meal') # ví dụ: 'sáng'
            meal_name_data = meal_name_map.get(meal_key_parser) # chuyển thành: 'Sáng'
            
            if not meal_name_data:
                continue

            # Lọc ra các quán có phục vụ bữa ăn này
            meal_df = base_df[base_df['meals'].apply(lambda x: meal_name_data in x if isinstance(x, list) else False)].copy()
            
            # Lọc tiếp theo 'type' (loại quán) TÙY THUỘC VÀO TỪNG BỮA
            req_types = meal_info.get('type', [])
            if req_types:
                desired_types = set(req_types)
                meal_df = meal_df[
                    meal_df['type'].apply(lambda x: bool(set(x) & desired_types) if isinstance(x, list) else False)
                ]
            
            # Lưu Dataframe đã lọc xong vào Dictionary kết quả
            result_dict[meal_key_parser] = meal_df
            
        return result_dict
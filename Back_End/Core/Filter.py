import pandas as pd
import numpy as np

class RestaurantFilter:
    def __init__(self, df, prompt, user_lat, user_lng):
        self.data = df
        self.user_prompt = prompt
        self.user_lat = user_lat
        self.user_lng = user_lng
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
        filtered_df = self.data.copy()

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

    def run_filter_pipeline(self): 
        # Bước 1: Lọc dữ liệu tổng quan
        base_df = self._apply_general_filters()
        
        # Bước 2: Chuẩn bị Dictionary kết quả rỗng
        result_dict = {}
        
        # Mapping để đồng bộ tên bữa ăn từ LLMParser sang Dataset JSON của bạn
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
    

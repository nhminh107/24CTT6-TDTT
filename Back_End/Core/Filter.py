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
        
        for meal_info in meals_detail:
            meal_key_parser = meal_info.get('meal')
            meal_name_data = meal_name_map.get(meal_key_parser)

            if not meal_name_data:
                continue

            meal_names = meal_name_data if isinstance(meal_name_data, list) else [meal_name_data]
            meal_names_lower = [m.lower() for m in meal_names]

            meal_df = base_df[
                base_df['meals'].apply(
                    lambda x: any(m in [str(meal).lower() for meal in x] for m in meal_names_lower)
                    if isinstance(x, list) else False
                )
            ].copy()
            
            req_types = meal_info.get('type', [])
            if req_types:
                expanded_reqs = []
                for t in req_types:
                    t_lower = t.lower()
                    expanded_reqs.append(t_lower)
                    if t_lower in type_normalization:
                        expanded_reqs.extend(type_normalization[t_lower])
                        
                meal_df = meal_df[
                    meal_df['type'].apply(
                        lambda x: any(any(req in str(item).lower() for req in expanded_reqs) for item in x) if isinstance(x, list) else False
                    )
                ]
            else:
                if meal_key_parser in MAIN_MEALS:
                    meal_df = meal_df[
                        meal_df['type'].apply(
                            lambda x: not any(b.lower() in str(t).lower() for t in x for b in BLACKLIST) if isinstance(x, list) else True
                        )
                    ]
            
            result_dict[meal_key_parser] = meal_df
            
        return result_dict

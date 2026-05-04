import pandas as pd

class RestaurantFilter:
    def __init__(self, df, prompt):
        self.data = df #Pandas dataframe
        self.user_prompt = prompt #Cái này nhận từ parsing, API sẽ xử lí nha
    import pandas as pd

    def run_filter_pipeline(raw_json, user_criteria):
        """
        Hàm Mock Output tạm thời.
        Hiện tại trả về toàn bộ dữ liệu gốc dưới dạng DataFrame cho các buổi, CHƯA qua bộ lọc.
        """
        # 1. Chuyển raw_json từ Parsing thành Pandas DataFrame
        df = pd.DataFrame(raw_json)
        
        # 2. Tạo Dictionary với định dạng y hệt tài liệu đã thống nhất
        # Hiện tại chưa lọc nên cứ gán tạm bản sao của DataFrame gốc cho các buổi
        result_dict = {
            'sang': df.copy(),
            'trua': df.copy(),
            'chieu': df.copy(),
            'toi': df.copy(),
            'khuya': df.copy()
        }
        
        # 3. Trả về kết quả cho bên Thuật toán
        return result_dict 
        

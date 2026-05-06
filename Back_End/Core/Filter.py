import pandas as pd

class RestaurantFilter:
    def __init__(self, df, prompt):
        self.data = df #Pandas dataframe
        self.user_prompt = prompt #Cái này nhận từ parsing, API sẽ xử lí nha
    def run_filter_pipeline(self): # Phải có self và thụt lề vào trong class
        """
        Hàm Mock Output tạm thời.
        Hiện tại trả về toàn bộ dữ liệu gốc dưới dạng DataFrame cho các buổi, CHƯA qua bộ lọc.
        """
        # Sử dụng self.data thay vì df vì df chỉ tồn tại trong hàm __init__
        result_dict = {
            'sang': self.data.copy(),
            'trua': self.data.copy(),
            'chieu': self.data.copy(),
            'toi': self.data.copy(),
            'khuya': self.data.copy()
        }
        
        # Trả về kết quả cho bên Thuật toán
        return result_dict
        

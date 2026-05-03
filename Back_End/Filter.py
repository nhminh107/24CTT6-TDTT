import pandas as pd

class RestaurantFilter:
    def __init__(self, df, prompt):
        self.data = df #Pandas dataframe
        self.user_prompt = prompt #Cái này nhận từ parsing, API sẽ xử lí nha
    def run_filter_pipeline(self):
        return [] 
    
import os
import pandas as pd

from Back_End.Core.parsing import LLMParser
from Back_End.Core.Filter import RestaurantFilter
from Back_End.Core.scoring_class import RestaurantScorer
from Back_End.Core.Maps import suggest_locations, get_place_detail
from Back_End.Database.database import ChromaDBManager

def main():
    print("="*50)
    print("BẮT ĐẦU TEST CÁC MODULE (PARSING, FILTER, MAPS, SCORING)")
    print("="*50)

    # 1. Parsing
    print("\n--- 1. Testing LLMParser ---")
    parser = LLMParser()
    user_prompt = "Tôi muốn tìm quán ăn sáng, trưa, tối ở Quận 1. Kinh phí 1 triệu rưỡi. Buổi tối phải là nhà hàng âu có không khí lãng mạn."
    parsed_json = parser.JSON_response(user_prompt)
    print(f"Input: '{user_prompt}'")
    print("LLMParser.JSON_response() returns:")
    print(parsed_json)

    # Load data for Filter and Scoring
    data_path = os.path.join(os.getcwd(), 'Back_End', 'Database', 'data.json')
    if os.path.exists(data_path):
        df = pd.read_json(data_path, encoding='utf-8', dtype={'id': str})
    else:
        print(f"\nLỗi: Không tìm thấy data tại {data_path}")
        df = pd.DataFrame()

    # 2. Filter
    print("\n--- 2. Testing RestaurantFilter ---")
    if not df.empty:
        filter_obj = RestaurantFilter(df=df, prompt=parsed_json, user_lat= 10.768225346989555, user_lng = 106.69726024041029)
        filtered_data = filter_obj.run_filter_pipeline()
        print("RestaurantFilter.run_filter_pipeline() returns:")
        if isinstance(filtered_data, dict):
            for meal, meal_df in filtered_data.items():
                print(f"  - Bữa '{meal}': DataFrame có kích thước {meal_df.shape}")
        else:
            print(filtered_data)
    else:
        filtered_data = {}
        print("Bỏ qua Filter vì không có dữ liệu.")

    # 3. Maps
    print("\n--- 3. Testing Maps ---")
    search_text = "Ben Thanh"
    suggestions = suggest_locations(search_text)
    print(f"suggest_locations('{search_text}') returns:")
    print(suggestions)

    if suggestions:
        # Giả sử lấy kết quả đầu tiên (có dạng tuple (description, place_id))
        place_id = suggestions[0][1] 
        details = get_place_detail(place_id)
        print(f"\nget_place_detail('{place_id}') returns:")
        print(details)

    # 4. Scoring
    print("\n--- 4. Testing RestaurantScorer ---")
    if not df.empty and filtered_data:
        # Vị trí giả định để test (Trung tâm Q1)
        user_lat = 10.7769
        user_lng = 106.7009
        
        db_manager = ChromaDBManager()
        scorer = RestaurantScorer(user_lat=user_lat, user_lng=user_lng, db=db_manager)
        final_itinerary = scorer.run_scoring_pipeline(filtered_data=filtered_data, parsed_json=parsed_json)
        
        print("RestaurantScorer.run_scoring_pipeline() returns:")
        if not final_itinerary.empty:
            print(f"DataFrame có kích thước {final_itinerary.shape}")
            # In ra một số cột quan trọng để kiểm tra
            cols = ['id', 'name', 'meal', 'score']
            available_cols = [c for c in cols if c in final_itinerary.columns]
            print(final_itinerary[available_cols].head())
        else:
            print("DataFrame rỗng (Không tìm thấy lịch trình phù hợp)")
    else:
        print("Bỏ qua Scoring vì không có dữ liệu đầu vào phù hợp.")

    print("\n" + "="*50)
    print("HOÀN THÀNH TEST")
    print("="*50)

if __name__ == "__main__":
    main()
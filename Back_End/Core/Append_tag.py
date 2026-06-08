import requests
import json
import re

def analyze_restaurant_tags(name, restaurant_type, shu, semantic_text):
    """
    Sử dụng Ollama Local để phân tích thông tin văn bản của nhà hàng và gán tag sức khỏe.
    """
    context_data = f"""
    - Tên nhà hàng: {name}
    - Loại hình (Type): {restaurant_type}
    - Độ cay (SHU từ 1-7): {shu}
    - Mô tả/Đánh giá (Semantic Text): {semantic_text}
    """

    # ĐỒNG BỘ HOÀN TOÀN: Mô tả tag nào thì JSON trả về đúng tag đó
    prompt = f"""Bạn là một chuyên gia dinh dưỡng và y tế. Hãy phân tích thông tin của nhà hàng dưới đây để phân loại và gán các tag sức khỏe/dị ứng phù hợp.

    Thông tin nhà hàng:
    {context_data}

    Đối với mỗi tag dưới đây, hãy xác định giá trị là:
    - "main": Đặc trưng cốt lõi của quán (xuất hiện dày đặc trong đa số món ăn).
    - "potential": Có khả năng cao là có xuất hiện (món phụ, món đính kèm hoặc nguy cơ nhiễm chéo).
    - "none": Không liên quan hoặc hoàn toàn không có.

    Danh sách các tag cần đánh giá đúng định nghĩa:
    - Spicy: Đồ ăn có vị cay nồng (mì cay, lẩu Thái, đồ Hàn, Tứ Xuyên).
    - DeepFried_Oily: Đồ chiên rán nhiều dầu mỡ (gà rán, khoai tây chiên, đồ nướng).
    - High_Sugar: Món ăn/thức uống sử dụng nhiều đường, đồ ngọt (chè, trà sữa, bánh ngọt).
    - Refined_Carbs: Tinh bột tinh chế (mì Ý, pizza, bánh mỳ, burger).
    - High_Sodium: Chế độ ăn nhiều muối và các loại khoáng (Món kho,đồ ăn nhanh,...).
    - Red_Meat: Các loại thịt đỏ (bò bít tết, lẩu đuôi bò, thịt dê, thịt cừu).
    - Seafood: Hải sản nói chung (cá, tôm, mực, cua, hàu).
    - Alcohol_Pub: Quán nhậu, đồ uống có cồn, bia rượu.
    - Peanuts_Nuts: Có chứa lạc/đậu phộng hoặc các hạt bản địa (quán gỏi, đồ Thái).
    - Dairy_Product: Sản phẩm từ bơ sữa, phô mai, kem tươi (thường có ở quán Âu, tiệm bánh).
    - Gluten_Present: Món ăn chứa bột mỳ, mì sợi, đồ chiên xù.
    - Shellfish: Động vật có vỏ thuộc nhóm dị ứng mạnh (tôm, cua, ghẹ, ốc, nghêu, sò).

    🔥 QUY TẮC BẮT BUỘC:
    Chỉ trả về đúng 1 JSON object duy nhất gồm các key là tên các tag trên và giá trị tương ứng. Không giải thích.

    Cấu trúc JSON chính xác:
    {{
      "Spicy": "main/potential/none",
      "DeepFried_Oily": "main/potential/none",
      "High_Sugar": "main/potential/none",
      "Refined_Carbs": "main/potential/none",
      "High_Sodium": "main/potential/none",
      "Red_Meat": "main/potential/none",
      "Seafood": "main/potential/none",
      "Alcohol_Pub": "main/potential/none",
      "Peanuts_Nuts": "main/potential/none",
      "Dairy_Product": "main/potential/none",
      "Gluten_Present": "main/potential/none",
      "Shellfish": "main/potential/none"
    }}"""

    ollama_url = "http://localhost:11434/api/chat"
    payload = {
        "model": "gemma3:4b", 
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",  # ÉP OLLAMA TRẢ VỀ JSON THUẦN TÚY (Rất quan trọng!)
        "options": {
            "temperature": 0.1 
        }
    }

    try:
        # Tăng timeout lên 45-60s phòng trường hợp máy local bị nghẽn khi chạy nhiều quán
        response = requests.post(ollama_url, json=payload, timeout=45)
        output_text = response.json()['message']['content'].strip()
        
        # Vẫn giữ Regex phòng hờ lỗi sinh chuỗi ngẫu nhiên bên ngoài
        match = re.search(r'\{.*\}', output_text, re.DOTALL)
        clean_json_str = match.group(0) if match else output_text

        raw_json = json.loads(clean_json_str)
        
        final_result = {
            "main_tag": [],
            "potential_tag": []
        }
        
        for tag, status in raw_json.items():
            if status == "main":
                final_result["main_tag"].append(tag)
            elif status == "potential":
                final_result["potential_tag"].append(tag)
                
        return final_result

    except Exception as e:
        print(f"❌ Lỗi khi xử lý quán '{name}': {e}")
        return {"main_tag": [], "potential_tag": []}

import os
# --- KỊCH BẢN CHẠY THỬ NGHIỆM VỚI DỮ LIỆU MẪU ---
if __name__ == "__main__":
    print("🚀 Đang kiểm tra kết nối tới Ollama và phân tích thử dữ liệu mẫu...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Đi lùi ra thư mục cha (Back_End), rồi đi vào 'Database' -> 'old_data.json'
    input_filename = os.path.join(current_dir,"merged_file.json")
        
    with open(input_filename, 'r', encoding='utf-8') as file:
      # 2. Nạp dữ liệu JSON thành List/Dict trong Python
      sample_restaurants = json.load(file)
  
    from concurrent.futures import ThreadPoolExecutor

    def process_single_restaurant(res):
        print(f"-> Bắt đầu phân tích: {res['name']}")
        tags = analyze_restaurant_tags(res['name'], res['type'], res['shu'], res['semantic_text'])
        res["main_tag"] = tags["main_tag"]
        res["potential_tag"] = tags["potential_tag"]
        return res

    # Chạy song song 4 quán cùng lúc (không nên để quá cao tránh tràn RAM/VRAM của máy cá nhân)
    max_workers = 4 

    print(f"🚀 Đang quét dữ liệu dinh dưỡng cho {len(sample_restaurants)} quán ăn...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Cập nhật trực tiếp kết quả vào list
      sample_restaurants = list(executor.map(process_single_restaurant, sample_restaurants))
    print("✅ Đã xử lý xong toàn bộ dữ liệu quán ăn!")

    # --- ĐOẠN CODE GHI RA FILE JSON Ở ĐÂY ---
    output_filename = os.path.join(current_dir, "data.json")
    
    try:
        # Mở file ở chế độ ghi ('w'), ép định dạng utf-8 để không bị lỗi font tiếng Việt
        with open(output_filename, "w", encoding="utf-8") as f:
            # json.dump sẽ chuyển list thành text JSON và đổ thẳng vào file f
            # ensure_ascii=False: Giữ nguyên chữ tiếng Việt có dấu, không bị biến thành \u2032
            # indent=4: Tự động xuống dòng và thụt lề 4 khoảng trắng cho đẹp mắt, dễ đọc
            json.dump(sample_restaurants, f, ensure_ascii=False, indent=4)
            
        print(f"🎉 Xuất dữ liệu thành công! Đã lưu kết quả tại file: {output_filename}")
        
    except Exception as e:
        print(f"❌ Thất bại khi ghi file JSON: {e}")

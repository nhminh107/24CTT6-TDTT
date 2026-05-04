# Yêu cầu Triển khai: Thuật toán Tối ưu hóa Lịch trình Du lịch (Phase 1)
## 1. Môi trường & Version Control
**BẮT BUỘC thực hiện các bước sau trước khi viết code:**
1. Kiểm tra nhánh hiện tại (`git branch`).
2. Nếu chưa ở nhánh `Minh_Algorithm`, hãy tạo và chuyển sang nhánh đó:
   `git checkout -b Minh_Algorithm`
3. Tuyệt đối không commit hoặc push code. Chỉ sửa đổi và tạo file.

## 2. Cấu trúc Thư mục
Tất cả code của module này phải nằm trong thư mục Backend. Nếu chưa có, hãy tạo cấu trúc sau:
```text
Back_End/
├── Algorithm/
│   ├── __init__.py
│   ├── models.py       # Định nghĩa Pydantic models / Data classes
│   └── optimizer.py    # Chứa logic thuật toán chính
```
Và để xây dựng thuật toán bước đầu thì bạn chỉ cần quan tâm tới những cái trong thư mục Database kèm với output từ parsing.py thôi.
## 3. Bối cảnh bài toán:
Hệ thống là một ứng dụng gợi ý lịch trình ăn uống.
- INPUT Algorithm : 1 list[dict] có dạng như ví dụ đây [{'sáng': df}, {'trưa': df}, {'tối': df}] df là DataFrame Pandas. Cái list[dict] đó đã qua module lọc rồi, đảm bảo trả về đúng bữa ăn cũng như type nhà hàng (bạn cần xem các field trong Back_End/Database/data.json để nắm rõ), và ChromaDB lưu id nhà hàng kèm theo semantic text của nhà hàng, user_lat, user_lng
- Mục tiêu: Thay vì dùng Knapsack & Routing tìm duy nhất 1 đường đi ngắn nhất thỏa mãn ngân sách, hệ thống cần sinh ra 5 phương án lộ trình (Candidate Routes). 
- Phương pháp:
Sinh tổ hợp các lộ trình (Có thể dùng K-Means kết hợp sinh ngẫu nhiên hoặc Vét cạn cục bộ).
Dùng hệ thống chấm điểm đa tiêu chí (MCDM) để đánh giá.
Trả về top 5 lộ trình có tổng điểm cao nhất.


## 4. Chi tiết thuật toán & Công thức: 
Cần triển khai hàm calculate_route_score(route: list[dict], user_budget: int) -> float dựa trên công thức sau:$$Total\_Score = (w_1 \cdot C_1) + (w_2 \cdot C_2) + (w_3 \cdot C_3) + (w_4 \cdot C_4) + (w_5 \cdot C_5) + (w_6 \cdot C_6)$$
Chi tiết các tiêu chí (Tất cả cần chuẩn hóa về thang 0-1 hoặc 0-10):
$C_1$ (Khoảng cách): Tổng khoảng cách di chuyển giữa 3 quán. Khoảng cách lý tưởng là 4km-7km (Điểm cao). Quá gần (<1km) hoặc quá xa (>15km) thì điểm thấp. Dùng công thức Haversine để tính dựa trên lat và lng.$C_2$ (Đa dạng ẩm thực): Dựa vào mảng type của quán. 3 loại khác nhau -> max điểm. 3 loại giống nhau -> min điểm.
$C_3$ (Tối ưu ngân sách): Tổng chi phí avg_price của lộ trình so với user_budget. Lý tưởng là đạt 85% - 95% ngân sách.
$C_4$ (Đánh giá): Tính trung bình cột star của 3 quán.
$C_5$ (Semantic): Viết hàm lấy distance từ chromadb, bạn có thể thêm nó ở Back_End/Database/database.py rồi sử dụng
Trọng số (Tạm thời hardcode):$w_1=0.25, w_2=0.2, w_3=0.2, w_4=0.2, w_5=0, w_6=0.15$

## 5. Cấu trúc code yêu cầu 
Trong file Back_End/Algorithm/optimizer.py, cần viết class,  yêu cầu thiết kế các hàm chính sau:

calculate_haversine(lat1, lon1, lat2, lon2): Tính khoảng cách vật lý.

normalize_score(value, min_val, max_val): Chuẩn hóa dữ liệu thành phần.

calculate_route_score(...): Implement công thức MCDM ở mục 4.

generate_candidates(candidate_pool: dict[str, pd.DataFrame], budget: int, top_n=5): Hàm Main gọi từ API. Sinh các lộ trình hợp lệ, chấm điểm và trả về list 5 lộ trình tốt nhất.

Đó chỉ là gợi ý, bạn có thể thay đổi để đúng với những gì tôi yêu cầu nhất

## 6. Testcase: 
- Thực hiện các testcase để kiểm tra. Chỉ cần in ra là được
- Yêu cầu testcase: 
1. Tạm thời module Filter chưa hoàn thiện, nên bạn tự sinh cái list[dict] đó, có thể tạo bằng cách lấy 1 phần dữ liệu từ data.json
2. Đối với user_lat, user_lng: Bạn có thể gán tùy ý, miễn là nó ở trong phạm vi của cái list[dict] để đảm bảo có kết quả chấp nhận được là ổn
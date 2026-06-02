# Phân Tích Kiến Trúc Web: LangGraph Agent & Giao diện Chat

Hệ thống Web mà chúng ta vừa xây dựng hoạt động dựa trên mô hình **Client-Server** (Khách - Chủ), chia làm 2 phần hoàn toàn tách biệt kết nối với nhau qua cổng API.

Dưới đây là giải thích luồng hoạt động chi tiết để bạn dễ dàng nắm bắt:

---

## 1. Backend (Phần "Não bộ") - FastAPI
Đây là máy chủ xử lý Logic và AI, chạy tại `http://localhost:8000`.

### Vấn đề: 
Bản thân LangGraph Agent (`src.agent.graph`) chỉ là một hàm chạy trên màn hình đen Terminal. Giao diện Web không thể gọi trực tiếp file Python được.
### Giải quyết (`api/main.py`):
Chúng ta dùng **FastAPI** để "bọc" con Agent này lại và phơi ra (expose) một endpoint (đường dẫn) để giao tiếp qua HTTP.

- **Khởi tạo Agent 1 lần**: 
  ```python
  agent = build_agent(provider="custom")
  ```
  Việc này giúp tiết kiệm thời gian, Agent được nạp vào bộ nhớ sẵn sàng đợi lệnh.
- **Tạo Endpoint `/api/chat`**:
  Khi React gửi một mảng tin nhắn lên, FastAPI sẽ nhận, ép kiểu (parse) thành đúng định dạng `dict` mà LangGraph mong muốn, rồi ném vào cho Agent suy nghĩ:
  ```python
  response = agent.invoke({"messages": messages_dict})
  ```
- **CORS (Cross-Origin Resource Sharing)**: 
  Mặc định, trình duyệt chặn không cho Frontend (cổng 5173) gọi API sang Backend (cổng 8000) vì khác "nhà". Cấu hình `CORSMiddleware` cho phép phá bỏ rào cản này.

---

## 2. Frontend (Phần "Mặt tiền") - React + Vite
Đây là ứng dụng chạy trên trình duyệt của người dùng tại `http://localhost:5173`.

### Vai trò (`frontend/src/App.tsx`):
- **Quản lý Trạng thái (State)**: Dùng `useState` để nhớ 2 thứ cực kỳ quan trọng:
  1. `messages`: Lịch sử toàn bộ cuộc hội thoại (để gửi lên cho AI hiểu bối cảnh).
  2. `isLoading`: Trạng thái Agent đang suy nghĩ để hiện hiệu ứng 3 dấu chấm (Typing Indicator).
- **Giao diện & Tương tác**: Render giao diện HTML và dùng CSS để tạo phong cách Glassmorphism mờ ảo. Khi người dùng bấm "Gửi", hàm `handleSubmit` sẽ chạy.

---

## 3. Luồng Chạy Toàn Cảnh (Request / Response Loop)

Hãy tưởng tượng bạn nhắn: *"Mình muốn mua tai nghe"*

1. **User Action (Frontend)**: Bạn gõ chữ vào ô input và nhấn Enter. 
2. **Cập nhật UI (Frontend)**: React lập tức đẩy câu của bạn vào giao diện cho bạn nhìn thấy, đồng thời bật trạng thái `isLoading = true` (hiện 3 dấu chấm).
3. **Gửi Request (Frontend -> Backend)**: React dùng hàm `fetch()` gom toàn bộ lịch sử đoạn chat thành JSON và bắn sang `http://localhost:8000/api/chat`.
4. **Xử lý AI (Backend)**: 
   - FastAPI nhận được gói tin, ném vào `agent.invoke()`.
   - AI Agent đọc, thấy bạn muốn mua tai nghe. Nó tự động gọi hàm (Tool Calling) `list_products` để tìm tai nghe trong kho.
   - LLM sinh ra câu trả lời: *"Mình tìm thấy vài loại tai nghe sau..."*
   - FastAPI lấy câu chốt hạ cuối cùng của LLM để đóng gói trả về.
5. **Nhận Response (Backend -> Frontend)**: 
   - React nhận được câu trả lời từ API.
   - Nó tắt `isLoading = false` (giấu 3 dấu chấm đi).
   - Nó thêm câu trả lời của AI vào danh sách `messages` -> Giao diện tự động render hiện bong bóng chat của AI.
   - Hàm `scrollToBottom()` tự động cuộn màn hình xuống tin nhắn mới nhất.

### Tổng kết
Cách chia tách **Frontend (React)** và **Backend (FastAPI + LangGraph)** này chính là chuẩn mực thực tế của các ứng dụng AI như ChatGPT hay Claude. Sau này bạn có thể thay React bằng Mobile App (iOS/Android) mà không cần phải viết lại logic AI Backend một chút nào!

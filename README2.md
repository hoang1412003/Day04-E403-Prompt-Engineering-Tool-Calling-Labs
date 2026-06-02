# Order Agent Web Interface 🚀

Dự án này là phiên bản nâng cấp của bài Lab **Prompt Engineering & Tool Calling**, cung cấp một giao diện Web Chatbot thực tế để tương tác trực tiếp với LangGraph AI Agent thay vì chỉ chạy qua Terminal.

## 🌟 Tính năng nổi bật
- **Giao diện hiện đại (Modern UI)**: Thiết kế Dark Mode thời thượng kết hợp phong cách Glassmorphism (hiệu ứng kính mờ trong suốt).
- **Trải nghiệm mượt mà**: Có hiệu ứng "Agent đang nhập..." (Typing indicator) và tự động cuộn (auto-scroll) tin nhắn.
- **Tích hợp nguyên bản**: Sử dụng đúng tệp `src/agent/graph.py` đã được thiết kế Prompt cực kỳ an toàn. AI có thể tìm kiếm sản phẩm, báo giá, kiểm tra tồn kho và chốt đơn đặt hàng y hệt như nhân viên thật.

## 🏗️ Kiến trúc hệ thống
Hệ thống được chia làm 2 phần:
1. **Backend API (`/api`)**: Xây dựng bằng `FastAPI` (Python), bọc LangGraph Agent lại và mở cổng kết nối RESTful `POST /api/chat`.
2. **Frontend UI (`/frontend`)**: Xây dựng bằng `React + Vite` (Node.js), đảm nhiệm phần hiển thị mặt tiền và gửi lịch sử hội thoại lên Backend.

---

## 🛠️ Hướng dẫn Cài đặt & Khởi chạy

### Bước 1: Cấu hình Môi trường
Hãy chắc chắn rằng bạn đã có file `.env` ở thư mục gốc của dự án với cấu hình cho model `custom` (DeepSeek):
```env
CUSTOM_MODEL=deepseek-v4-flash
CUSTOM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
CUSTOM_LLM_ENDPOINT=https://opencode.ai/zen/go/v1
```

### Bước 2: Chạy Backend (Python FastAPI)
Mở 1 tab Terminal mới và chạy các lệnh sau:
```bash
# Cài đặt thư viện nếu chưa có
pip install fastapi uvicorn pydantic

# Khởi chạy server Backend (chạy ở cổng 8000)
uvicorn api.main:app --host 127.0.0.1 --port 8000
```
*Lưu ý: Luôn để Terminal này chạy ngầm.*

### Bước 3: Chạy Frontend (React Vite)
Mở 1 tab Terminal khác và chạy các lệnh sau:
```bash
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt các gói thư viện Node.js
npm install

# Khởi chạy server Web (chạy ở cổng 5173)
npm run dev
```

### Bước 4: Trải nghiệm
Mở trình duyệt Web của bạn lên và truy cập vào:
👉 **http://localhost:5173**

Hãy thử đóng vai một khách hàng khó tính và đưa ra những yêu cầu mua sắm phức tạp hoặc đòi hỏi xuất hóa đơn giả để thử thách các quy tắc (Guardrails) của Agent nhé!

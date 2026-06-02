# Bài học từ việc cải thiện Order Agent (Prompt Engineering & Tool Calling)

Trong bài Lab này, chúng ta đã cùng nhau nâng cấp một Baseline Agent yếu kém thành một Agent xử lý đơn hàng chuyên nghiệp với điểm số đạt **98.85/100**. Dưới đây là những kiến thức quan trọng và các kỹ thuật đã được áp dụng:

## 1. Xử lý "Dữ liệu bẩn" từ LLM (Data Coercion)
Mặc dù LLM (ví dụ: DeepSeek, GPT-4) rất thông minh, nhưng đôi khi chúng sinh ra dữ liệu không đúng chuẩn định dạng mà code Python mong đợi.
- **Lỗi đã gặp**: Model trả về danh sách sản phẩm ngăn cách bằng ký tự xuống dòng (`\n`) thay vì dấu phẩy (`,`) như code gốc kỳ vọng (vd: `'3\nHD-002:2\nWC-001:1'`). Điều này gây ra lỗi `ValueError: invalid literal for int()`.
- **Cách giải quyết**: Không nên tin tưởng 100% vào output của model. Chúng ta đã sửa hàm `_coerce_items` để sử dụng Regex `re.split(r"[,\n]+", text)`, cho phép bóc tách chuỗi linh hoạt bằng cả dấu phẩy lẫn dấu xuống dòng, kết hợp với khối lệnh `try...except ValueError` để bỏ qua rác dữ liệu.

## 2. Thiết kế System Prompt chặt chẽ (Guardrails & Workflow)
Prompt không chỉ để bảo LLM "Làm gì", mà quan trọng hơn là bảo nó **"Không được làm gì"** và **"Làm theo trình tự nào"**.
- **Chặn (Guardrails)**: Đặt luật rõ ràng yêu cầu model từ chối lịch sự và **KHÔNG GỌI TOOL** khi khách hàng đòi xuất hóa đơn giả, bypass kho hàng, hay xin giảm giá sai quy định.
- **Xác minh thông tin (Clarification)**: Buộc model kiểm tra đủ 4 trường (Tên, SĐT, Email, Địa chỉ). Nếu thiếu, phải hỏi lại khách ngay lập tức, cấm tuyệt đối việc gọi Tool tìm kiếm hay tạo đơn khi thiếu thông tin.
- **Ép buộc trình tự (Forced Workflow)**: LLM thường hay tự suy diễn hoặc nhảy cóc. Chúng ta đã liệt kê rõ trình tự bắt buộc: `list_products` -> `get_product_details` -> `get_discount` -> `calculate_order_totals` -> `save_order`.
- **Giảm ma sát (Auto Execution)**: Ban đầu model tính tiền xong lại dừng lại hỏi "Bạn có muốn lưu đơn không?". Chúng ta đã khắc phục bằng câu lệnh: *"GỌI save_order NGAY LẬP TỨC sau khi tính toán thành công mà không cần chờ khách hàng xác nhận."*

## 3. Quản lý Missing Fields (Giá trị rỗng / NoneType)
- **Lỗi đã gặp**: Hàm `save_order` yêu cầu `discount_rate` là kiểu `float`, nhưng LLM đôi lúc lại truyền thẳng biến rỗng (trong JSON là `null`, Python hiểu là `None`). Khi đó gọi hàm `float(None)` sẽ bị sập chương trình (`TypeError`).
- **Cách giải quyết**: Chủ động thiết lập giá trị mặc định (Fallback) an toàn trong hàm python chứa logic gọi tool:
  ```python
  # Thay vì: discount_rate = float(payload.get("discount_rate", 0.0))
  # Xử lý an toàn:
  dr_raw = payload.get("discount_rate")
  dr = float(dr_raw) if dr_raw is not None else 0.0
  ```

## 4. Đặc thù môi trường (Environment Specifics)
- **Lỗi đã gặp**: Code chạy ra kết quả đúng y hệt file JSON yêu cầu, nhưng script chấm điểm (grader) lại báo sai đường dẫn.
- **Nguyên nhân**: Trên hệ điều hành Windows, thư viện `Pathlib` sinh ra đường dẫn dùng dấu backslash `\` (ví dụ: `artifacts\orders\ORD.json`), trong khi file đáp án mẫu trên Linux/Mac dùng forward slash `/` (`artifacts/orders/ORD.json`).
- **Cách giải quyết**: Phải chuẩn hóa chuỗi đường dẫn khi serialize JSON (`str(relative_path).replace("\\", "/")`) để code chạy trơn tru trên mọi hệ điều hành.

## 5. Tách biệt cấu hình Provider (LLM Configuration)
- Thay vì hardcode API Key và Endpoint vào thẳng trong source code, chúng ta sử dụng biến môi trường (Environment Variables thông qua `.env`). 
- Việc thiết lập `provider == "custom"` cho phép ta linh hoạt thay đổi model (Gemini, OpenAI, Ollama, DeepSeek) thông qua tham số lệnh (`--provider custom`) mà không cần đụng vào code. Điều này rất hữu ích cho MLOps và đánh giá tự động (Evaluation).

---
**Tóm tắt cốt lõi:** Làm việc với AI Agent không chỉ là viết prompt hay, mà là sự kết hợp giữa **Prompt Engineering** (kiểm soát hành vi LLM) và **Phòng thủ trong code (Defensive Programming)** (bắt lỗi dữ liệu, xử lý None, bắt lỗi Type).

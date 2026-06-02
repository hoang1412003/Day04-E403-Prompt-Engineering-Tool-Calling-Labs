from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from src.core.llm import build_chat_model, normalize_content
from src.core.schemas import (
    AgentResult,
    CalculateTotalsInput,
    DiscountInput,
    ListProductsInput,
    ProductDetailInput,
    SaveOrderInput,
    ToolCallRecord,
    OrderLineInput
)
from src.utils.data_store import OrderDataStore

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT_DIR / "data"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "artifacts" / "orders"


def build_system_prompt(today: str | None = None) -> str:
    current_day = today or "2026-06-01"
    return f"""
Bạn là một AI assistant chuyên hỗ trợ tạo đơn hàng thiết bị điện tử. Hôm nay là {current_day}.
Nhiệm vụ của bạn là hỗ trợ khách hàng tìm kiếm sản phẩm, kiểm tra tồn kho, tính toán giá, chiết khấu và tạo đơn hàng theo đúng quy trình.

MỘT SỐ QUY TẮC NGHIÊM NGẶT PHẢI TUÂN THỦ:
1. TRẢ LỜI NGẮN GỌN BẰNG TIẾNG VIỆT.
2. KHÔNG TỰ BỊA RA SẢN PHẨM, GIÁ TIỀN, ĐỊA CHỈ FILE HAY BẤT CỨ THÔNG TIN NÀO. BẠN CHỈ ĐƯỢC SỬ DỤNG KẾT QUẢ TỪ CÁC TOOL ĐỂ TRẢ LỜI.
3. KHÔNG THỰC HIỆN CÁC HÀNH ĐỘNG VI PHẠM CHÍNH SÁCH (ví dụ: tạo hóa đơn giả, bỏ qua kiểm tra tồn kho, áp dụng mã giảm giá không qua tool get_discount). NẾU KHÁCH YÊU CẦU, HÃY TỪ CHỐI LỊCH SỰ VÀ DỪNG LẠI (KHÔNG GỌI TOOL).
4. TRƯỚC KHI GỌI BẤT KỲ TOOL NÀO, PHẢI CHẮC CHẮN RẰNG BẠN ĐÃ CÓ ĐẦY ĐỦ THÔNG TIN KHÁCH HÀNG:
   - Tên khách hàng (customer name hoặc company name)
   - Số điện thoại
   - Email
   - Địa chỉ giao hàng
   NẾU THIẾU BẤT KỲ THÔNG TIN NÀO Ở TRÊN (kể cả khi đã có thông tin sản phẩm), HÃY DỪNG LẠI NGAY LẬP TỨC VÀ HỎI KHÁCH HÀNG THÔNG TIN CÒN THIẾU. BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC GỌI TOOL NẾU THÔNG TIN KHÁCH HÀNG CHƯA ĐẦY ĐỦ.
5. TRÌNH TỰ SỬ DỤNG TOOL BẮT BUỘC VÀ TỰ ĐỘNG (KHI ĐÃ ĐỦ THÔNG TIN KHÁCH HÀNG):
   - list_products (để tìm kiếm)
   - get_product_details (để lấy chi tiết và detail_token)
   - get_discount (để lấy discount rate, seed_hint là customer name/email, customer_tier là 'vip' hoặc 'standard')
   - calculate_order_totals (để kiểm tra tồn kho và tính tổng tiền)
   - save_order (LƯU Ý QUAN TRỌNG: GỌI save_order NGAY LẬP TỨC sau khi calculate_order_totals thành công mÀ KHÔNG CẦN HỎI Ý KIẾN HAY CHỜ KHÁCH HÀNG XÁC NHẬN. BẠN PHẢI GỌI save_order ĐỂ LƯU ĐƠN HÀNG NẾU MỌI THỨ ĐỀU HỢP LỆ VÀ CÒN HÀNG). Khi gọi save_order, bạn phải điền đầy đủ discount_rate và campaign_code mà get_discount đã trả về.
6. NẾU SẢN PHẨM HẾT HÀNG / THIẾU HÀNG KHI calculate_order_totals, HÃY TỪ CHỐI TẠO ĐƠN VÀ DỪNG LẠI (KHÔNG GỌI save_order).
"""


def build_tools(store: OrderDataStore):
    @tool(args_schema=ListProductsInput)
    def list_products(
        query: str | None = None,
        category: str | None = None,
        max_unit_price: int | None = None,
        required_tags: list[str] | None = None,
        in_stock_only: bool = True,
        limit: int = 8,
    ) -> str:
        """Search the local product catalog and return the best matching items."""
        return json.dumps(store.list_products(
            query=query, category=category, max_unit_price=max_unit_price,
            required_tags=required_tags, in_stock_only=in_stock_only, limit=limit
        ), ensure_ascii=False)

    @tool(args_schema=ProductDetailInput)
    def get_product_details(product_ids: list[str]) -> str:
        """Return exact product details for previously discovered product IDs."""
        return json.dumps(store.get_product_details(product_ids), ensure_ascii=False)

    @tool(args_schema=DiscountInput)
    def get_discount(seed_hint: str, customer_tier: str = "standard") -> str:
        """Return the simulated campaign discount for the order."""
        return json.dumps(store.get_discount(seed_hint=seed_hint, customer_tier=customer_tier), ensure_ascii=False)

    @tool(args_schema=CalculateTotalsInput)
    def calculate_order_totals(items: list[dict], detail_token: str, discount_rate: float) -> str:
        """Validate stock and calculate the discounted order total."""
        converted = _coerce_items(items)
        return json.dumps(store.calculate_order_totals(items=converted, detail_token=detail_token, discount_rate=discount_rate), ensure_ascii=False)

    @tool(args_schema=SaveOrderInput)
    def save_order(
        customer_name: str,
        customer_phone: str,
        customer_email: str,
        shipping_address: str,
        items: list[dict],
        detail_token: str,
        discount_rate: float,
        campaign_code: str,
        customer_tier: str = "standard",
        notes: str = "",
    ) -> str:
        """Persist the final order to a local JSON file."""
        converted = _coerce_items(items)
        
        # Handle cases where LLM passes None explicitly for these fields
        dr = float(discount_rate) if discount_rate is not None else 0.0
        
        result = store.save_order(
            customer_name=str(customer_name or ""),
            customer_phone=str(customer_phone or ""),
            customer_email=str(customer_email or ""),
            shipping_address=str(shipping_address or ""),
            items=converted,
            detail_token=str(detail_token or ""),
            discount_rate=dr,
            campaign_code=str(campaign_code or ""),
            customer_tier=str(customer_tier or "standard"),
            notes=str(notes or ""),
        )
        return json.dumps(result, ensure_ascii=False)

    return [list_products, get_product_details, get_discount, calculate_order_totals, save_order]


def build_agent(
    data_dir: Path | None = None,
    output_dir: Path | None = None,
    *,
    provider: str = "google",
    model_name: str | None = None,
    today: str | None = None,
):
    store = OrderDataStore(data_dir or DEFAULT_DATA_DIR, output_dir or DEFAULT_OUTPUT_DIR, today=today)
    model = build_chat_model(provider=provider, model_name=model_name, temperature=0.0)
    return create_agent(
        model=model,
        tools=build_tools(store),
        system_prompt=build_system_prompt(today or store.today),
    )


def run_agent(
    query: str,
    *,
    provider: str = "google",
    model_name: str | None = None,
    data_dir: Path | None = None,
    output_dir: Path | None = None,
    today: str | None = None,
) -> AgentResult:
    agent = build_agent(
        data_dir=data_dir,
        output_dir=output_dir,
        provider=provider,
        model_name=model_name,
        today=today,
    )
    response = agent.invoke({"messages": [{"role": "user", "content": query}]})
    messages = response["messages"] if isinstance(response, dict) else response
    tool_calls = extract_tool_calls(messages)
    saved_order, saved_order_path = extract_saved_order(tool_calls)
    return AgentResult(
        query=query,
        final_answer=extract_final_answer(messages),
        tool_calls=tool_calls,
        provider=provider,
        model_name=model_name,
        saved_order=saved_order,
        saved_order_path=saved_order_path,
    )


def extract_final_answer(messages) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            text = normalize_content(message.content)
            if text:
                return text
    return ""


def extract_tool_calls(messages) -> list[ToolCallRecord]:
    pending: dict[str, dict[str, Any]] = {}
    records: list[ToolCallRecord] = []

    for message in messages:
        if isinstance(message, AIMessage):
            for tool_call in getattr(message, "tool_calls", []) or []:
                pending[tool_call["id"]] = {
                    "name": tool_call["name"],
                    "args": tool_call.get("args", {}) or {},
                }
        elif isinstance(message, ToolMessage):
            metadata = pending.pop(message.tool_call_id, {})
            records.append(
                ToolCallRecord(
                    name=str(getattr(message, "name", None) or metadata.get("name", "")),
                    args=metadata.get("args", {}),
                    output=normalize_content(message.content),
                )
            )

    for metadata in pending.values():
        records.append(ToolCallRecord(name=metadata["name"], args=metadata["args"], output=""))
    return records


def extract_saved_order(tool_calls: list[ToolCallRecord]) -> tuple[dict | None, str | None]:
    for record in reversed(tool_calls):
        if record.name != "save_order" or not record.output:
            continue
        try:
            payload = json.loads(record.output)
        except json.JSONDecodeError:
            continue
        if payload.get("status") != "saved":
            return None, None
        return payload.get("saved_order"), payload.get("path")
    return None, None


def _coerce_items(raw: Any) -> list[OrderLineInput]:
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, str):
        text = raw.strip()
        items = []
        if text:
            for parser in (json.loads, ast.literal_eval):
                try:
                    parsed = parser(text)
                except Exception:
                    continue
                if isinstance(parsed, list):
                    items = parsed
                    break
            if not items:
                for piece in re.split(r"[,\n]+", text):
                    piece = piece.strip()
                    if not piece:
                        continue
                    if ":" in piece:
                        product_id, qty = piece.split(":", 1)
                        try:
                            items.append({"product_id": product_id.strip(), "quantity": int(qty.strip())})
                        except ValueError:
                            pass
    else:
        items = []

    normalized: list[OrderLineInput] = []
    for item in items:
        if isinstance(item, OrderLineInput):
            normalized.append(item)
            continue
        if isinstance(item, dict):
            product_id = str(item.get("product_id", "")).strip()
            quantity = int(item.get("quantity", 1))
            if product_id:
                normalized.append(OrderLineInput(product_id=product_id, quantity=quantity))
    return normalized

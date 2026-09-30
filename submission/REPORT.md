# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Anh Tuấn
- **MSSV:** 2A202602700
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/harrynguyen127/K4-L3-DAY13-NguyenAnhTuan-2A202602700-Monitoring-LLMOps
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602700`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| CP0 health check | [cp0-health-check.png](evidence/cp0-health-check.png) |
| CP0 baseline log validator | [cp0-baseline-log-validator.png](evidence/cp0-baseline-log-validator.png) |
| CP0 dashboard validator | [cp0-dashboard-validator.png](evidence/cp0-dashboard-validator.png) |
| CP0 public tests | [cp0-pytest.png](evidence/cp0-pytest.png) |
| CP0 Langfuse trace check | [cp0-langfuse-trace-check.png](evidence/cp0-langfuse-trace-check.png) |
| Pytest cuối | Chưa bổ sung |
| Log validator | [02-log-validator.png](evidence/02-log-validator.png) |
| Dashboard validator | Chưa bổ sung |
| Structured log | [04-structured-log.png](evidence/04-structured-log.png) |
| PII redaction | [05-pii-redaction.png](evidence/05-pii-redaction.png) |
| Trace list | Chưa bổ sung |
| Trace waterfall | Chưa bổ sung |
| Trace metadata | Chưa bổ sung |
| Prompt versions | Chưa bổ sung |
| Prompt rollback | Chưa bổ sung |
| Dashboard runtime | Chưa bổ sung |
| Incident metric | Chưa bổ sung |
| Incident log | Chưa bổ sung |
| Incident trace | Chưa bổ sung |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Baseline: 28 records, 20 records thiếu required fields/enrichment và 0 correlation ID. CP1: 66 records, không thiếu field/enrichment, 31 correlation ID duy nhất và 0 PII leak. |
| `validate_dashboard.py` | 6/6 panel | Chưa đo cuối | Contract YAML hợp lệ đủ 6/6 panel; dashboard runtime sẽ được chứng minh ở CP2. |
| `pytest` | 24 passed, 0 failed | Chưa đo cuối | Public tests đạt tại CP0/CP1; sẽ chạy lại trên commit cuối ở CP4. |
| Số traces hợp lệ | 33 root observations nhìn thấy trong project cá nhân | Chưa đo theo rubric CP2 | Kết nối Langfuse hoạt động; CP2 cần kiểm tra tiếp cây root/retrieval/generation và metadata. |
| Số PII leak | 0 | 0 | Validator không phát hiện PII thô; log runtime cho thấy email, điện thoại Việt Nam, CCCD và thẻ thanh toán đều được thay bằng marker `REDACTED`. |
| Latency P95 / TTFT P95 | 1445 ms / 123 ms | Chưa đo | Tính trên 10 sự kiện `response_sent` trong log baseline |
| Retrieval success rate | 100% (10/10) | Chưa đo | Chưa bật incident; tất cả retrieval được ghi nhận thành công |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa context của request trước, nhận `x-request-id` từ header hoặc sinh ID dạng `req-<8-hex>`, bind ID vào context, lưu vào `request.state` và trả lại qua response header. Request kiểm thử gửi `req-a1b2c3d4`; response header và structured log đều trả cùng ID này.
- **Các metadata được ghi vào structured log:** `ts`, `event`, `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`; log phản hồi còn có latency, TTFT, token và cost.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` chạy trước `JsonlFileProcessor` và JSON renderer, thay email, số điện thoại Việt Nam, CCCD và thẻ thanh toán bằng marker `REDACTED` trước khi ghi file.
- **Cách kiểm chứng kết quả:** [Log validator đạt 100/100](evidence/02-log-validator.png), [structured log có đủ metadata runtime](evidence/04-structured-log.png), và [request PII giả đã được redact đủ email, điện thoại, CCCD và thẻ, đồng thời response trả đúng correlation ID](evidence/05-pii-redaction.png).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Sau khi chạy workload local, tôi mở project Langfuse `day13-k4-l3b-2A202602700`, lọc `isRootObservation:true` và xác nhận 33 root observations `lab-agent-run` có trace name `day13-agent-request`; correlation ID trên metadata khớp với output của workload. [Evidence kiểm tra kết nối CP0](evidence/cp0-langfuse-trace-check.png).
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
- **SLO và lý do chọn:**
- **Cách tính error budget:**
- **Ba alert và runbook tương ứng:**

> Ví dụ cách viết error budget: "SLO 99.5% trong 28 ngày nghĩa là error budget 0.5%. Nếu workload có 10,000 request thì tối đa 50 request được phép lỗi hoặc chậm hơn ngưỡng SLO."

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

> Gợi ý cách viết ngắn, không thay cho evidence thực tế: "Metric cho thấy `[latency/error/cost/quality]` bất thường trong `[khoảng thời gian]`. Log line `[event]` có `correlation_id=[...]` đại diện cho request bị ảnh hưởng. Trace cùng `correlation_id` cho thấy span `[retrieval/generation/prompt/tool]` có dấu hiệu `[chậm/lỗi/token tăng]`. Root cause là `[nguyên nhân suy ra từ evidence]`. Fix action là `[hành động khôi phục]`; preventive measure là `[alert/runbook/test/guardrail để ngăn tái diễn]`."

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

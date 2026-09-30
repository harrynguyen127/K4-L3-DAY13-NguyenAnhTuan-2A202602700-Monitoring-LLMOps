# Alert và runbook vận hành

Ba alert dưới đây dựa trên triệu chứng người dùng hoặc SLO. Quy trình điều tra chung là dùng metric để xác định khoảng thời gian, dùng structured log để chọn `correlation_id`, rồi mở trace cùng ID để xác định observation bất thường.

## Alert 1

- **Tên:** `HighLatencyP95`
- **Severity:** `warning`
- **Duration:** `5m`
- **Kênh thông báo:** Slack `#k4-l3b-alerts`
- **Owner:** `student-2A202602700`
- **SLI/SLO liên quan:** latency P95 của `response_sent.latency_ms`; SLO yêu cầu request thành công trong không quá 3000 ms.
- **Điều kiện:** `p95(response_sent.latency_ms) > 3000` liên tục trong 5 phút.
- **Ảnh hưởng:** nhóm request chậm nhất khiến người dùng phải chờ lâu dù phần lớn request có thể vẫn thành công.

### Kiểm tra đầu tiên

1. Mở panel **Latency percentiles and TTFT**, xác nhận P95/P99 vượt đường SLO và ghi lại khoảng thời gian.
2. Lọc các dòng `response_sent` trong `data/logs.jsonl`, chọn request có `latency_ms` cao và lấy `correlation_id`.
3. Mở trace cùng `correlation_id` trên Langfuse, so sánh thời gian `knowledge-retrieval` và `fake-llm-generation` để xác định bước chậm.

### Mitigation và khôi phục

- Nếu retrieval chậm, tắt practice scenario liên quan hoặc khôi phục cấu hình retrieval ổn định.
- Nếu generation chậm sau khi đổi prompt, rollback label `production` về prompt version đã ổn định.
- Giảm concurrency tạm thời nếu tail latency tăng do tải.
- Alert được xem là khôi phục khi latency P95 trở lại `<= 3000 ms` trong ít nhất 5 phút; nếu không, owner báo Lab Coach và đính kèm khoảng thời gian, correlation ID cùng trace ID.

## Alert 2

- **Tên:** `HighErrorRate`
- **Severity:** `critical`
- **Duration:** `5m`
- **Kênh thông báo:** Slack `#k4-l3b-alerts`
- **Owner:** `student-2A202602700`
- **SLI/SLO liên quan:** tỷ lệ `request_failed` trên `request_received`; guardrail tối đa 2%.
- **Điều kiện:** `count(request_failed) / count(request_received) * 100 > 2` liên tục trong 5 phút.
- **Ảnh hưởng:** người dùng không nhận được câu trả lời thành công; error budget bị tiêu thụ trực tiếp.

### Kiểm tra đầu tiên

1. Mở panel **Error rate and retrieval success**, xác nhận error rate và breakdown theo `error_type`.
2. Lọc dòng `request_failed` trong khoảng cảnh báo, lấy `error_type`, `tool_name` và `correlation_id` đại diện.
3. Mở trace cùng `correlation_id`, kiểm tra observation lỗi hoặc bước cuối cùng hoàn thành trước lỗi để khoanh vùng retrieval/generation.

### Mitigation và khôi phục

- Tắt practice scenario hoặc cấu hình vừa làm lỗi tăng.
- Nếu lỗi gắn với prompt/version mới, rollback `production` về version ổn định.
- Nếu retrieval lỗi, dùng fallback an toàn hoặc tạm ngừng luồng phụ thuộc retrieval cho đến khi dependency phục hồi.
- Alert được xem là khôi phục khi error rate trở lại `<= 2%` trong ít nhất 5 phút; do severity `critical`, owner phải lưu correlation ID và trace ID trong báo cáo incident.

## Alert 3

- **Tên:** `LowRetrievalSuccess`
- **Severity:** `warning`
- **Duration:** `5m`
- **Kênh thông báo:** Slack `#k4-l3b-alerts`
- **Owner:** `student-2A202602700`
- **SLI/SLO liên quan:** tỷ lệ record có `tool_success=true` trên tổng record có `tool_success`; guardrail tối thiểu 90%.
- **Điều kiện:** `count(tool_success == true) / count(tool_success != null) * 100 < 90` liên tục trong 5 phút.
- **Ảnh hưởng:** câu trả lời có thể thiếu context, giảm chất lượng hoặc chuyển thành lỗi nếu retrieval là bước bắt buộc.

### Kiểm tra đầu tiên

1. Mở panel **Error rate and retrieval success**, xác nhận retrieval success dưới 90% và xác định khoảng thời gian.
2. Lọc log có `tool_name=retrieval` và `tool_success=false`, lấy `correlation_id` cùng `error_type` nếu có.
3. Mở trace tương ứng, kiểm tra `knowledge-retrieval` để xác nhận timeout, lỗi dependency hay không tìm thấy tài liệu.

### Mitigation và khôi phục

- Tắt practice scenario gây retrieval chậm/lỗi và kiểm tra lại nguồn tài liệu.
- Dùng context fallback đã scrub nếu nghiệp vụ cho phép, tránh trả dữ liệu không kiểm chứng.
- Không kết luận model sinh kém trước khi xác nhận retrieval đã cung cấp đúng context.
- Alert được xem là khôi phục khi retrieval success trở lại `>= 90%` trong ít nhất 5 phút; nếu không, owner báo Lab Coach với log và trace liên quan.

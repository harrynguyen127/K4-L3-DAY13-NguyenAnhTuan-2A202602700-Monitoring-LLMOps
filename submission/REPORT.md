# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Anh Tuấn
- **MSSV:** 2A202602700
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/harrynguyen127/K4-L3-DAY13-NguyenAnhTuan-2A202602700-Monitoring-LLMOps
- **Commit SHA nội dung và evidence:** `7f42904f4d89cc864ec355bfe13c88dfa379b908`
- **Challenge ID:** day13-k4-l3b-monitoring-llmops-v1
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
| Pytest cuối | [01-pytest.txt](evidence/01-pytest.txt) |
| Log validator | [02-log-validator.png](evidence/02-log-validator.png) |
| Dashboard validator | [03-dashboard-validator.png](evidence/03-dashboard-validator.png) |
| Structured log | [04-structured-log.png](evidence/04-structured-log.png) |
| PII redaction | [05-pii-redaction.png](evidence/05-pii-redaction.png) |
| Trace list | [06-trace-list.png](evidence/06-trace-list.png) |
| Trace waterfall | [07-trace-waterfall.png](evidence/07-trace-waterfall.png) |
| Trace metadata | [08-trace-metadata.png](evidence/08-trace-metadata.png) |
| Prompt versions | [09-prompt-versions.png](evidence/09-prompt-versions.png) |
| Prompt rollback | [production v2](evidence/10a-prompt-production-v2.png), [rollback production về v1](evidence/10b-prompt-rollback-v1.png) |
| Dashboard runtime | [overview](evidence/11-dashboard-overview.png), [latency/errors](evidence/11a-dashboard-latency-errors.png), [cost/token/quality](evidence/11b-dashboard-cost-token-quality.png) |
| Incident metric | [12-incident-metric.png](evidence/12-incident-metric.png) |
| Incident log | [13-incident-log.png](evidence/13-incident-log.png) |
| Incident trace | [14-incident-trace.png](evidence/14-incident-trace.png) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 | Baseline: 28 records, 20 records thiếu required fields/enrichment và 0 correlation ID. CP1: 66 records, không thiếu field/enrichment, 31 correlation ID duy nhất và 0 PII leak. |
| `validate_dashboard.py` | 6/6 panel | 6/6 panel | Contract YAML hợp lệ và dashboard Streamlit đọc dữ liệu thật từ `data/logs.jsonl`; xem [validator](evidence/03-dashboard-validator.png) và [runtime](evidence/11-dashboard-overview.png). |
| `pytest` | 24 passed, 0 failed | 24 passed, 0 failed | Toàn bộ public tests đạt trên trạng thái source cuối; xem [output pytest](evidence/01-pytest.txt). |
| Số traces hợp lệ | 33 root observations nhìn thấy trong project cá nhân | Ít nhất 38 root observations | Evidence cho thấy trace `day13-agent-request` có root agent và hai child observation retrieval/generation; workload CP3 tạo thêm 5 trace trong cùng project cá nhân. |
| Số PII leak | 0 | 0 | Validator không phát hiện PII thô; log runtime cho thấy email, điện thoại Việt Nam, CCCD và thẻ thanh toán đều được thay bằng marker `REDACTED`. |
| Latency P95 / TTFT P95 | 1445 ms / 123 ms | 2653 ms / 50 ms trong workload CP3 | Năm request challenge có application latency 2652–2653 ms, đều vượt ngưỡng challenge 2000 ms; TTFT không tăng, giúp loại trừ generation là bước gây chậm. |
| Retrieval success rate | 100% (10/10) | 100% (31/31) | Retrieval vẫn thành công về mặt chức năng; CP3 là sự cố latency, không phải retrieval failure. Năm canary sau mitigation cũng thành công. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa context của request trước, nhận `x-request-id` từ header hoặc sinh ID dạng `req-<8-hex>`, bind ID vào context, lưu vào `request.state` và trả lại qua response header. Request kiểm thử gửi `req-a1b2c3d4`; response header và structured log đều trả cùng ID này.
- **Các metadata được ghi vào structured log:** `ts`, `event`, `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`; log phản hồi còn có latency, TTFT, token và cost.
- **Cách bảo đảm PII được scrub trước khi ghi:** Processor `scrub_event` chạy trước `JsonlFileProcessor` và JSON renderer, thay email, số điện thoại Việt Nam, CCCD và thẻ thanh toán bằng marker `REDACTED` trước khi ghi file.
- **Cách kiểm chứng kết quả:** [Log validator đạt 100/100](evidence/02-log-validator.png), [structured log có đủ metadata runtime](evidence/04-structured-log.png), và [request PII giả đã được redact đủ email, điện thoại, CCCD và thẻ, đồng thời response trả đúng correlation ID](evidence/05-pii-redaction.png).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Sau khi chạy workload local, tôi mở project Langfuse `day13-k4-l3b-2A202602700`, lọc `isRootObservation:true` và xác nhận 33 root observations `lab-agent-run` có trace name `day13-agent-request`; correlation ID trên metadata khớp với output của workload. [Evidence kiểm tra kết nối CP0](evidence/cp0-langfuse-trace-check.png).
- **Cấu trúc root/retrieval/generation observations:** Mỗi lượt chat là trace `day13-agent-request`; root `lab-agent-run` có type `agent`, bên dưới là `knowledge-retrieval` type `retriever` và `fake-llm-generation` type `generation`. Generation ghi model `claude-sonnet-4-5`, TTFT, input/output token và cost. [Waterfall runtime](evidence/07-trace-waterfall.png).
- **Cách nối trace với log:** Middleware tạo hoặc nhận `correlation_id`, structured log ghi ID này ở `request_received`/`response_sent`, còn `propagate_attributes` đưa cùng ID vào metadata của mọi observation. Khi điều tra, tôi lọc log để lấy ID của request rồi tìm đúng trace theo metadata, thay vì mở trace ngẫu nhiên. [Trace metadata](evidence/08-trace-metadata.png).
- **Prompt name:** Text prompt `day13-chat`, gồm ba biến bắt buộc `{{feature}}`, `{{docs}}`, `{{message}}`.
- **Version/label baseline:** v1 giữ template gốc, có labels `baseline` và `production` sau rollback.
- **Version/label candidate:** v2 thêm hướng dẫn dùng documents và trả lời không quá ba câu, có labels `candidate` và `latest`.
- **Trace ID của mỗi version:** baseline v1 `24ee857eed93ef7a02fd41567e77e84b`; candidate v2 `74339e32326a16e13d0657ed6f58a3bd`; production v2 trước rollback `13574f9f9e25bb6e4262e316ffd0cc74`; production v1 sau rollback `bdebdcbbf67643bd33f7d8b265e95ef7`.
- **Cách promote và rollback `production`:** Tôi chuyển label `production` từ v1 sang v2, chạy cùng input và xác nhận trace production ghi `prompt_version=2`; sau đó chuyển label về v1 và xác nhận trace mới ghi `prompt_version=1`. Ứng dụng không đổi code vì fetch prompt theo label. [Danh sách versions](evidence/09-prompt-versions.png), [production v2](evidence/10a-prompt-production-v2.png), [rollback v1](evidence/10b-prompt-rollback-v1.png).

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard Streamlit đọc `data/logs.jsonl`, lọc cửa sổ 60 phút và refresh mỗi 30 giây. Sáu panel gồm latency P50/P95/P99 và TTFT P95; traffic; error rate và retrieval success; cost theo thời gian; input/output token; quality proxy. Workload CP2 ghi nhận 21 request, latency P50/P95/P99 lần lượt 266/1796/1858 ms, TTFT P95 50 ms, error rate 0%, retrieval success 100%, cost `$0.046104`, 708 input token, 2932 output token và quality trung bình 0.88. [Dashboard overview](evidence/11-dashboard-overview.png), [latency/errors](evidence/11a-dashboard-latency-errors.png), [cost/token/quality](evidence/11b-dashboard-cost-token-quality.png).
- **SLO và lý do chọn:** SLO yêu cầu 99.5% request trong cửa sổ 28 ngày có `response_sent` và `latency_ms <= 3000`. Ngưỡng 3000 ms cao hơn P95 baseline 1445 ms và P95 CP2 1796 ms nên có khoảng đệm cho tail latency, nhưng vẫn đủ thấp để phát hiện thời gian chờ ảnh hưởng người dùng. Cấu hình chi tiết nằm tại [`config/slo.yaml`](../config/slo.yaml).
- **Cách tính error budget:** Error budget bằng `100% - 99.5% = 0.5%`. Với 10,000 request trong 28 ngày, số request được phép lỗi hoặc chậm hơn 3000 ms là `10,000 × 0.5% = 50`.
- **Ba alert và runbook tương ứng:** `HighLatencyP95` cảnh báo khi P95 vượt 3000 ms trong 5 phút; `HighErrorRate` mức critical khi error rate vượt 2% trong 5 phút; `LowRetrievalSuccess` cảnh báo khi retrieval success dưới 90% trong 5 phút. Cả ba gửi Slack `#k4-l3b-alerts`, owner `student-2A202602700`, và có quy trình Metrics → Logs → Traces cùng mitigation trong [`config/alert_rules.yaml`](../config/alert_rules.yaml) và [`docs/alerts.md`](../docs/alerts.md).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (cohort K4, feature `monitoring`).
- **Khoảng thời gian điều tra:** `2026-09-30 05:40:17–05:40:30 UTC` (`12:40:17–12:40:30 ICT`).
- **Triệu chứng từ metrics:** Cả 5 request challenge có application latency `2652–2653 ms`, vượt ngưỡng riêng của challenge `2000 ms`; P95 của workload là `2653 ms`, cao hơn baseline P95 `1445 ms` khoảng 84%. TTFT P95 vẫn là `50 ms`, error rate là `0%` và retrieval success là `100%`, nên đây là latency spike trước generation chứ không phải lỗi request hay model chậm. Client quan sát end-to-end `7991–13316 ms` khi chạy concurrency 5 vì các request đồng bộ bị xếp hàng, làm ảnh hưởng người dùng còn rõ hơn application latency từng request.
- **Log line và correlation ID liên quan:** Dòng `response_sent` lúc `2026-09-30T05:40:19.909128Z` có `correlation_id=req-b3ed9f23`, `feature=monitoring`, `latency_ms=2653`, `ttft_ms=50`, `tool_name=retrieval`, `tool_success=true`. Bốn request cùng incident là `req-cbbd553d`, `req-025b663c`, `req-cf044367`, `req-9f5e24a7`.
- **Trace ID và span gây ảnh hưởng:** Trace `42711d808987b9896634daa08535e271` khớp request `req-b3ed9f23` theo timestamp/correlation metadata. Root `lab-agent-run` mất `2.654 s`; child `knowledge-retrieval` mất `2.501 s`, trong khi `fake-llm-generation` chỉ mất `0.152 s`. Span gây ảnh hưởng là `knowledge-retrieval`.
- **Root cause:** Challenge bật scenario `rag_slow`; đường retrieval bị thêm độ trễ khoảng `2.5 s`. Chuỗi evidence nhất quán: metric tăng latency nhưng TTFT/error không tăng → log chọn request `req-b3ed9f23` → trace cho thấy gần như toàn bộ thời gian nằm trong child retrieval.
- **Fix action:** Đã tắt scenario bằng `python scripts/inject_incident.py --disable`; health check xác nhận `rag_slow=false`. Năm canary sau mitigation có application latency `151–152 ms` (client end-to-end `325–803 ms` ở concurrency 5), trở về dưới baseline và ngưỡng challenge.
- **Preventive measure:** Bổ sung SLI/alert riêng cho latency của span `knowledge-retrieval` (cảnh báo khi P95 vượt `2000 ms`), timeout/circuit breaker và fallback an toàn cho vector store, đồng thời thêm regression load test kiểm tra retrieval latency. Giữ runbook Metrics → Logs → Traces để alert luôn dẫn tới correlation ID và trace cụ thể.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Tôi giữ structured log làm nguồn chuẩn cho dashboard vận hành, Langfuse làm nguồn trace/prompt, rồi nối hai nguồn bằng `correlation_id`. Cách tách này tránh gọi trace là log và cho phép dashboard phản ánh toàn bộ request trong khi Langfuse giải thích chi tiết từng bước.
- **Một lỗi/blocker đã gặp:** Trên Langfuse v4, metadata không xuất hiện trong phần Preview/Raw của input-output nên ban đầu tôi chưa thấy `correlation_id` và prompt version; ngoài ra prompt chưa tồn tại khiến ứng dụng ghi `prompt_source=local-fallback`.
- **Cách tìm nguyên nhân và xử lý:** Tôi mở mục Attributes của observation để kiểm tra metadata, tạo `day13-chat` v1/v2 trong đúng project, chạy cùng input theo từng label và xác nhận lại bằng trace có `prompt_source=langfuse`. Sau đó tôi promote v2 rồi rollback production về v1 và lưu hai trace ID làm bằng chứng.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics cho biết loại triệu chứng và khoảng thời gian bất thường; structured log thu hẹp xuống request cụ thể bằng `correlation_id`; trace cùng ID cho thấy retrieval hay generation là bước chậm/lỗi. Root cause chỉ được kết luận khi ba lớp evidence cùng khớp.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version giúp gắn chất lượng, latency, token và cost với đúng thay đổi. Token/cost phát hiện prompt dài hoặc output tăng bất thường; SLO xác định mức dịch vụ chấp nhận được; label `production` cho phép deploy hoặc rollback prompt mà không sửa code.
- **Điều quan trọng nhất đã học:** Observability hữu ích khi các tín hiệu liên kết được với nhau. Một dashboard đẹp hoặc một trace chi tiết riêng lẻ chưa đủ nếu không thể đi từ metric tới log và trace của cùng request.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Không còn hạng mục code bắt buộc chưa hoàn thành. Ảnh incident trace hiện thể hiện Trace ID và chênh lệch duration giữa retrieval/generation; nếu cần tăng độ rõ khi chấm, có thể chụp bổ sung trường `correlation_id` trong Attributes để mối nối log → trace xuất hiện trực tiếp trong cùng ảnh.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA đã ghi trong báo cáo.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

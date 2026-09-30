# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: P95 của `response_sent.latency_ms`, ngưỡng SLO 3000 ms.
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` liên tục 5 phút.
- Ảnh hưởng tới người dùng: Người dùng phải chờ lâu hơn trước khi nhận câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận P50/P95/P99 và thời điểm tăng trên panel Latency.
  2. Lọc log trong khoảng đó và lấy `correlation_id` của request chậm.
  3. Mở trace cùng ID, so sánh thời gian child `retrieval` và `generation`.
- Mitigation tạm thời: Tắt practice incident nếu đang bật; rollback prompt nếu generation tăng sau đổi version; giảm tải trong lúc điều tra.
- Owner: `student-2A202602974`

## Alert 2

- Tên: `HighErrorRate`
- Severity: `critical`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Tỷ lệ `request_failed / request_received`, guardrail tối đa 2%.
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` liên tục 5 phút.
- Ảnh hưởng tới người dùng: Một phần request không nhận được câu trả lời thành công.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận error rate và retrieval success trên panel Errors.
  2. Lọc `request_failed`, nhóm theo `error_type`, lấy một `correlation_id` đại diện.
  3. Mở trace tương ứng để xác định child observation lỗi và thông báo trạng thái.
- Mitigation tạm thời: Tắt incident/tool bị lỗi, dùng fallback an toàn và rollback thay đổi gần nhất.
- Owner: `student-2A202602974`

## Alert 3

- Tên: `LowAnswerQuality`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: Trung bình `response_sent.quality_score`, guardrail tối thiểu 0.75.
- Điều kiện và thời gian duy trì: `avg(quality_score) < 0.75` liên tục 10 phút.
- Ảnh hưởng tới người dùng: Câu trả lời có dấu hiệu kém liên quan hoặc thiếu thông tin.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận thời điểm quality giảm trên panel Quality và đối chiếu Tokens/Cost.
  2. Lọc log `response_sent` có quality thấp, lấy `correlation_id` và prompt label.
  3. Mở trace để kiểm tra retrieval context, prompt version và generation usage.
- Mitigation tạm thời: Rollback label `production` về prompt baseline và theo dõi lại quality.
- Owner: `student-2A202602974`

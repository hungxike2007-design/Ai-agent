# Product

## Register

product

## Users

- **Người dùng thường**: Phân tích dữ liệu Excel, nhận gợi ý làm sạch, tạo biểu đồ và báo cáo qua giao diện AI; làm việc bằng tiếng Việt, thường tại máy cá nhân hoặc máy văn phòng.
- **Quản trị (Admin)**: Giám sát người dùng, file hệ thống, phiên phân tích, token và phản hồi; cần màn hình rõ ràng, thao tác nhanh, ít trang trí thừa.

## Product Purpose

Ứng dụng web Flask hỗ trợ tải dữ liệu, phân tích và trò chuyện với AI để ra insight, biểu đồ và báo cáo. Trang quản trị tập trung vào vận hành: ai đang dùng, file nào trên hệ thống, phiên nào tiêu tốn tài nguyên. Thành công nghĩa là người dùng hoàn thành phân tích đúng ý với ít công sức; quản trị nắm được tình trạng hệ thống mà không bị lạc trong giao diện.

## Brand Personality

- **Rõ ràng, đáng tin**: Dữ liệu và hành động phải đọc được ngay; tránh cảm giác “demo AI” hay đồ họa rỗng.
- **Chuyên nghiệp, gọn**: Giống công cụ làm việc (Linear, Notion, trình phân tích) hơn là landing marketing.
- **Thân thiện tiếng Việt**: Nhãn, thông báo lỗi và trợ giúp ngắn, đúng ngữ cảnh; không văn máy dài dòng.

## Anti-references

- Giao diện kiểu SaaS generic: ba ô “số lớn + icon + gradient”, card lặp vô tận, dark mode tím–xanh chỉ vì “AI”.
- Chữ gradient (`background-clip: text`), glassmorphism làm nền mặc định, viền cạnh dày làm accent.
- Font và palette giống mọi template “AI tool” (Inter + cyan/purple) nếu không có chủ đích riêng của dự án.
- Modal là lựa chọn đầu tiên cho mọi thao tác; hover là chức năng duy nhất (bỏ qua bàn phím/touch).

## Design Principles

1. **Ưu tiên tác vụ**: Mật độ và luồng phù hợp phân tích dữ liệu và quản trị; trang trí chỉ khi hỗ trợ hiểu thị hoặc trạng thái.
2. **Một giọng màu nhất quán**: Accent dùng cho hành động chính, trạng thái chọn và phản hồi; neutrals có sắc nhẹ (OKLCH), tránh xám thuần và đen/trắng tuyệt đối trên diện rộng.
3. **Nhất quán thành phần**: Nút, bảng, trạng thái loading/empty/error theo cùng một hệ; không đổi “từ vựng” giữa các màn (ví dụ Workspace vs Project).
4. **Hiệu năng cảm nhận được**: Giảm layout shift, biểu đồ và bảng không chặn tương tác; chuyển động ngắn, có chủ đích, tôn trọng `prefers-reduced-motion`.
5. **Tiếp cận thực tế**: Tương phản chữ đạt WCAG AA, focus-visible cho điều khiển, nhãn form và bảng đọc được với bàn phím.

## Accessibility & Inclusion

- Mục tiêu **WCAG 2.1 AA** cho văn bản và thành phần điều khiển trên các màn chính (đăng nhập, dashboard AI, admin).
- Không dựa chỉ vào màu để truyền đạt trạng thái (kèm nhãn hoặc icon có ý nghĩa).
- Form và bảng: nhãn rõ ràng, thông báo lỗi cụ thể (định dạng, quyền, mạng).
- Giảm chuyển động khi người dùng bật “Reduce motion” trên hệ điều hành.

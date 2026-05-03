---
name: AI Agent Analytics
description: Giao diện phân tích dữ liệu AI — product UI brand teal–emerald; admin dùng cùng theme file (impeccable-theme.css).
colors:
  brand-primary: "#0d9488"
  brand-dark: "#0f766e"
  surface-bg: "#f7faf9"
  surface-raised: "#ffffff"
  text-primary: "#0f172a"
  text-muted: "#64748b"
  border-subtle: "#e2e8f0"
  semantic-success: "#059669"
  semantic-danger: "#dc2626"
  semantic-info: "#2563eb"
  semantic-warning: "#d97706"
typography:
  display:
    fontFamily: "\"Plus Jakarta Sans\", system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "\"Plus Jakarta Sans\", system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "-0.01em"
  title:
    fontFamily: "\"Plus Jakarta Sans\", system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "\"Plus Jakarta Sans\", system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "\"Plus Jakarta Sans\", system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0.06em"
rounded:
  sm: "8px"
  md: "12px"
  lg: "16px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.brand-primary}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "{colors.brand-dark}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  card-surface:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "16px 20px"
  nav-item-active:
    backgroundColor: "{colors.surface-bg}"
    textColor: "{colors.brand-primary}"
    rounded: "{rounded.sm}"
    padding: "10px 14px"
---

# Design System: AI Agent Analytics

## 1. Overview

**Creative North Star: "Trạm phân tích trong sạch"**

Hệ thống nhìn như một **công cụ phân tích chuyên nghiệp**, không như landing AI generic. Nền và neutrals **nghiêng hue brand** (teal–emerald ~168° trong OKLCH) qua `static/css/impeccable-theme.css`, dùng chung cho đăng nhập, dashboard AI và **Admin** (`admin_dashboard`). Trục chữ Plus Jakarta Sans; accent và semantic thống nhất (không tím–xanh trang trí).

**Key Characteristics:**

- OKLCH cho màu brand và neutrals có sắc; tránh `#000` / `#fff` và xám thuần trên diện rộng.
- Accent hiếm: primary CTA và trạng thái chọn; semantic riêng cho success / danger / info / warning.
- Typography cố định bậc rem cho UI dày đặc; không fluid type trong panel dữ liệu.
- Chuyển động ngắn, ease-out; tôn trọng `prefers-reduced-motion`.

Điều hệ thống **từ chối** được ghi trong `PRODUCT.md` (anti-references): hero metric ba ô clone, gradient text, glass mặc định, modal là giải pháp đầu tiên.

## 2. Colors

Palette gốc gắn với token trong `:root` của **impeccable-theme.css** (hue brand xấp xỉ 168°).

### Primary

- **Teal Emerald (brand)** (`#0d9488` / `oklch(52% 0.17 168)`): Nút chính, liên kết hành động, logo/mark khi cần nhấn mạnh brand.

### Secondary

- **Teal đậm** (`#0f766e` / `oklch(42% 0.16 168)`): Hover nút primary, pressed.

### Neutral

- **Nền app** (`#f7faf9` / `oklch(97% 0.006 168)`): Canvas toàn trang.
- **Surface nổi** (`#ffffff`): Card, panel, modal trên nền sáng.
- **Viền** (`#e2e8f0` hoặc token `--border-dark` trong theme): Đường chia tách, khung bảng.

### Semantic

- **Success** `#059669`, **Danger** `#dc2626`, **Info** `#2563eb`, **Warning** `#d97706`: Badge, toast, border trạng thái — luôn kèm nhãn hoặc icon, không chỉ màu.

### Named Rules

**The One Accent Rule.** Màu brand chỉ gắn với hành động chính, mục điều hướng đang chọn, hoặc điểm nhấn đơn lẻ — không lấp đầy Section bằng teal “cho đẹp”.

**The Admin Shell Rule.** `admin_dashboard` dùng chung theme file `impeccable-theme.css` để sóng nhìn khớp đăng nhập / dashboard người dùng — accent teal brand, không tách một palette cyan riêng.

## 3. Typography

**Display / UI:** Plus Jakarta Sans (`400–700`) — `dashboard.html`, `index.html`, file `impeccable-theme.css`.

**Admin:** Import `impeccable-theme.css` + Plus Jakarta như luồng chính; KPI strip và accent dùng cùng `--brand` (~168°).

**Character:** Sans hiện đại, rõ chữ tiếng Việt; hierarchy bằng weight và spacing hơn là quá nhiều cỡ chữ.

### Hierarchy

- **Display** (700, ~1.75rem): Tiêu đề vùng / hero copy ngắn trên marketing surfaces.
- **Headline** (600, ~1.25rem): Tiêu đề panel, section trong app.
- **Title** (600, 1rem): Tiêu đề card, hàng bảng nhấn.
- **Body** (400, 0.9375rem, line-height ~1.5): Nội dung, ô chat, mô tả; prose dài giữ max-width ~65ch khi cần.
- **Label** (600, 0.75rem, uppercase + letter-spacing): Meta, tab phụ, legend nhỏ.

### Named Rules

**The Tabular Data Rule.** Số liệu, ID, token counts dùng `font-variant-numeric: tabular-nums` để cột không nhảy.

## 4. Elevation

Ưu tiên **tách bề mặt bằng viền + nền trắng** trên nền xám–xanh rất nhạt. Shadow dùng có chủ đích:

### Shadow Vocabulary

- **ambient-sm** (`--shadow-sm` trong theme): Card và sidebar nhẹ, gần như “dán” vào nền.
- **ambient-md** (`--shadow-md`): Modal, dropdown nổi.
- **ambient-lg** (`--shadow-lg`): Chỉ overlay quan trọng (modal xác nhận).

**Backdrop blur** (`--blur`) chỉ trên sidebar/kính có ranh giới rõ (dashboard user); không làm nền toàn trang mờ mặc định.

### Named Rules

**The Flat-First Rule.** Surface ở trạng thái nghỉ phẳng; shadow tăng khi hover, focus, hoặc layer modal — tránh “card nổi” đồng loạt không có trật tự z-index.

## 5. Components

### Buttons

- **Shape:** Bo `8px` (sm); nút primary đặt trên nền đủ tương phản (brand trên trắng hoặc trắng trên brand).
- **Primary:** Nền `brand-primary`, chữ trắng, padding ngang rộng hơn chiều cao để vùng bấm đủ lớn.
- **Hover / Focus:** Đậm màu `brand-dark`; `focus-visible` viền 2px contrast.

### Sidebar navigation

- **Style:** Nền surface trong suốt hoặc kính nhẹ có viền phải 1px `border-subtle`; item active = nền tint brand nhạt + chữ brand, không viền trái dày màu.

### Cards / Panels

- **Corner:** `12–16px`; **Border:** 1px neutral; **Padding:** 16–24px theo scale.
- **Admin KPI:** Một panel chứa nhiều chỉ số (chia cột / divider), không lặp ba card icon+số giống hệt.

### Inputs / Chat bubbles

- **User:** Nền tint brand nhạt; **AI:** Surface trắng/viền — luôn có landmark và khả năng đọc keyboard.

### Charts

- **Line:** Một dataset chính, màu brand teal; grid trục Y nhạt.
- **Doughnut:** Tối đa 4 slice semantic; legend dưới, font label nhỏ.

## 6. Do's and Don'ts

### Do:

- **Do** đọc token từ `impeccable-theme.css` hoặc `:root` của template trước khi thêm màu mới.
- **Do** căn chỉnh admin và dashboard user về cùng nguyên tắc accent hiếm và semantic cố định.
- **Do** giữ `PRODUCT.md` và file này đồng bộ khi đổi anti-pattern hoặc personality.

### Don't:

- **Don't** dùng gradient text, hero metric ba ô clone, hoặc glassmorphism làm nền toàn cục (theo `PRODUCT.md`).
- **Don't** đặt chữ xám (`--muted`) trực tiếp trên nền màu đậm mà không chỉnh contrast.
- **Don't** thêm section Markdown ngoài sáu phần của Stitch (Overview … Do's and Don'ts); ghi chú layout/motion vào Overview hoặc Components.

import pandas as pd
import json
import plotly.express as px
import plotly.utils

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend (no UI window)

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import matplotlib.font_manager as fm
import os
import numpy as np
from openpyxl.utils import get_column_letter

# ── CẤU HÌNH FONT ──────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.unicode_minus': False,
    'text.color': '#f8fafc',
    'axes.labelcolor': '#cbd5e1',
    'xtick.color': '#cbd5e1',
    'ytick.color': '#cbd5e1',
})


def _safe_label(text: str) -> str:
    """Trả về chuỗi an toàn với UTF-8, bỏ dấu nếu cần."""
    try:
        text.encode('utf-8')
        return text
    except Exception:
        import unicodedata
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )


def get_cleaning_suggestions(df):
    suggestions = []
    null_data = df.isnull().sum()
    for col, count in null_data.items():
        if count > 0:
            # Check if column is numeric for mean option
            is_numeric = pd.to_numeric(df[col], errors='coerce').notnull().sum() > 0
            actions = [{"type": "drop_nulls", "label": "Xóa dòng rác"}]
            if is_numeric:
                actions.append({"type": "fill_mean", "label": "Điền giá trị trung bình"})
                
            suggestions.append({
                "column": col,
                "issue": f"Có {count} dòng bị trống (NULL)",
                "action": "Điền giá trị trung bình hoặc xóa dòng rác",
                "actions": actions
            })
            
    for col in df.select_dtypes(include=['number']).columns:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            suggestions.append({
                "column": col,
                "issue": f"Có {neg_count} giá trị âm không hợp lệ",
                "action": "Xóa dòng rác hoặc lấy giá trị tuyệt đối",
                "actions": [
                    {"type": "drop_negatives", "label": "Xóa dòng số âm"},
                    {"type": "abs_values", "label": "Lấy giá trị tuyệt đối"}
                ]
            })
    return suggestions


def auto_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Skill: Excel Analysis - Tự động làm sạch dữ liệu.
    - Loại bỏ trùng lặp.
    - Xử lý khoảng trắng thừa.
    - Điền giá trị mặc định cho ô trống.
    """
    df = df.copy()
    
    # 1. Xóa dòng trùng lặp hoàn toàn
    df = df.drop_duplicates()
    
    # 2. Xử lý khoảng trắng thừa cho các cột văn bản
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip()
        
    # 3. Điền giá trị mặc định
    # Cột số -> 0, Cột chữ -> "N/A"
    num_cols = df.select_dtypes(include=['number']).columns
    df[num_cols] = df[num_cols].fillna(0)
    
    obj_cols = df.select_dtypes(include=['object']).columns
    df[obj_cols] = df[obj_cols].fillna("N/A")
    
    return df


def deep_clean_data(df: pd.DataFrame) -> tuple:
    """
    Lọc sâu dữ liệu rác TRƯỚC khi phân tích AI & vẽ biểu đồ.
    Xử lý 8 loại rác: trùng lặp, dòng rỗng, cột rỗng,
    header lặp, khoảng trắng, encoding, kiểu dữ liệu sai, outlier.
    Returns: (clean_df, cleaning_report_dict)
    """
    report = {
        "rows_before": len(df),
        "cols_before": len(df.columns),
        "actions": [],
        "warnings": [],
        "rows_removed": 0,
        "cols_removed": 0
    }
    df = df.copy()

    # ── 1. Xóa cột rỗng 100% hoặc cột "Unnamed" ────────────────────────
    empty_cols = [c for c in df.columns
                  if df[c].isna().all() or
                  (str(c).startswith('Unnamed') and df[c].isna().sum() > len(df) * 0.9)]
    if empty_cols:
        df = df.drop(columns=empty_cols)
        report["actions"].append({
            "type": "cols_removed", "icon": "fa-table-columns",
            "text": f"Xóa {len(empty_cols)} cột rỗng/không tên",
            "detail": ", ".join(str(c) for c in empty_cols)
        })
        report["cols_removed"] = len(empty_cols)

    # ── 2. Xóa dòng rỗng (>80% cột trống) ───────────────────────────────
    if len(df.columns) > 0:
        threshold = max(1, int(len(df.columns) * 0.8))
        mask_empty = df.isna().sum(axis=1) >= threshold
        empty_count = int(mask_empty.sum())
        if empty_count > 0:
            df = df[~mask_empty].reset_index(drop=True)
            report["actions"].append({
                "type": "empty_rows", "icon": "fa-eraser",
                "text": f"Xóa {empty_count} dòng rỗng (>80% cột trống)", "detail": ""
            })

    # ── 3. Xóa dòng trùng lặp hoàn toàn ─────────────────────────────────
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        report["actions"].append({
            "type": "duplicates", "icon": "fa-clone",
            "text": f"Xóa {dup_count} dòng trùng lặp hoàn toàn", "detail": ""
        })

    # ── 4. Phát hiện header lặp trong data ───────────────────────────────
    try:
        col_names_lower = [str(c).strip().lower() for c in df.columns]
        header_mask = df.apply(
            lambda row: sum(1 for i, c in enumerate(df.columns)
                           if str(row[c]).strip().lower() == col_names_lower[i]) >= len(df.columns) * 0.8,
            axis=1
        )
        header_count = int(header_mask.sum())
        if header_count > 0:
            df = df[~header_mask].reset_index(drop=True)
            report["actions"].append({
                "type": "header_rows", "icon": "fa-heading",
                "text": f"Xóa {header_count} dòng header lặp trong dữ liệu", "detail": ""
            })
    except Exception:
        pass

    # ── 5. Khoảng trắng thừa + chuẩn hóa text ──────────────────────────
    text_cols = df.select_dtypes(include=['object']).columns
    strip_count = 0
    for col in text_cols:
        original = df[col].astype(str)
        df[col] = df[col].astype(str).str.strip()
        # Chuẩn hóa giá trị rỗng
        df[col] = df[col].replace({'nan': np.nan, 'None': np.nan, 'none': np.nan, '': np.nan, 'NaT': np.nan})
        strip_count += int((original != df[col].astype(str)).sum())
    if strip_count > 0:
        report["actions"].append({
            "type": "whitespace", "icon": "fa-broom",
            "text": f"Chuẩn hóa {strip_count} ô (khoảng trắng, giá trị rỗng)", "detail": ""
        })

    # ── 6. Ký tự đặc biệt / encoding lỗi ────────────────────────────────
    encoding_fixes = 0
    for col in text_cols:
        if col in df.columns:
            before = df[col].astype(str)
            df[col] = df[col].astype(str).str.replace('\x00', '', regex=False)
            df[col] = df[col].apply(
                lambda x: ''.join(ch for ch in str(x) if ch in '\n\t' or (isinstance(ch, str) and ord(ch) >= 32))
                if pd.notna(x) else x
            )
            encoding_fixes += int((before != df[col].astype(str)).sum())
    if encoding_fixes > 0:
        report["actions"].append({
            "type": "encoding", "icon": "fa-code",
            "text": f"Sửa {encoding_fixes} ô có ký tự đặc biệt/encoding lỗi", "detail": ""
        })

    # ── 7. Cột số bị lẫn text → tự động chuyển kiểu ─────────────────────
    type_fixes = {}
    for col in list(df.columns):
        if df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col]):
            numeric_vals = pd.to_numeric(df[col], errors='coerce')
            non_null = df[col].dropna().shape[0]
            numeric_ok = numeric_vals.dropna().shape[0]
            if non_null > 0 and numeric_ok / non_null > 0.7:
                bad = non_null - numeric_ok
                df[col] = numeric_vals
                if bad > 0:
                    type_fixes[col] = bad
    if type_fixes:
        detail = ", ".join(f"'{k}' ({v} giá trị sửa)" for k, v in type_fixes.items())
        report["actions"].append({
            "type": "type_fix", "icon": "fa-arrows-rotate",
            "text": f"Chuẩn hóa kiểu dữ liệu {len(type_fixes)} cột", "detail": detail
        })

    # ── 8. Phát hiện outlier (IQR × 3) — chỉ CẢNH BÁO, không xóa ──────
    num_cols = df.select_dtypes(include=['number']).columns
    for col in num_cols:
        data = df[col].dropna()
        if len(data) < 10:
            continue
        Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
        IQR = Q3 - Q1
        if IQR > 0:
            lower, upper = Q1 - 3 * IQR, Q3 + 3 * IQR
            outlier_count = int(((data < lower) | (data > upper)).sum())
            if 0 < outlier_count <= len(data) * 0.05:
                report["warnings"].append({
                    "column": col, "count": outlier_count,
                    "text": f"Cột '{col}' có {outlier_count} giá trị ngoại lệ (outlier)",
                    "icon": "fa-triangle-exclamation"
                })

    # ── Tổng kết ─────────────────────────────────────────────────────────
    report["rows_after"] = len(df)
    report["cols_after"] = len(df.columns)
    report["rows_removed"] = report["rows_before"] - report["rows_after"]

    total_fixes = len(report["actions"])
    if total_fixes == 0 and len(report["warnings"]) == 0:
        report["status"] = "clean"
        report["summary"] = "✅ Dữ liệu đã sạch, không phát hiện vấn đề."
    else:
        report["status"] = "cleaned"
        warn_text = f", phát hiện {len(report['warnings'])} cảnh báo" if report['warnings'] else ""
        report["summary"] = (
            f"🧹 Đã xử lý {total_fixes} vấn đề{warn_text}"
            f" — Còn lại {report['rows_after']:,} dòng × {report['cols_after']} cột"
        )

    print(f"[DEEP CLEAN] {report['summary']}")
    return df, report


def export_excel_styled(df: pd.DataFrame, output_path: str):
    """
    Skill: Excel Analysis - Xuất Excel với định dạng chuyên nghiệp.
    - Tự động căn chỉnh độ rộng cột (Auto-adjust width).
    - In đậm tiêu đề (Bold header).
    """
    writer = pd.ExcelWriter(output_path, engine='openpyxl')
    df.to_excel(writer, index=False, sheet_name='Data_Analysis')
    
    workbook = writer.book
    worksheet = writer.sheets['Data_Analysis']
    
    # Tự động căn chỉnh độ rộng cột dựa trên nội dung dài nhất
    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter # Lấy chữ cái tên cột
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column].width = adjusted_width
        
    # In đậm hàng tiêu đề
    from openpyxl.styles import Font
    for cell in worksheet[1]:
        cell.font = Font(bold=True)
        
    writer.close()


# ── BẢNG MÀU CHUYÊN NGHIỆP ──────────────────────────────────────────────────
_PALETTE = [
    "#10a37f", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#22c55e"
]


def _setup_style(fig, ax):
    """Áp dụng nền và grid nhất quán cho mọi biểu đồ."""
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")
    ax.tick_params(colors="#cbd5e1", labelsize=9)
    ax.xaxis.label.set_color("#cbd5e1")
    ax.yaxis.label.set_color("#cbd5e1")
    ax.title.set_color("#f8fafc")
    ax.spines[:].set_color("#475569")
    ax.grid(axis='y', color="#334155", linewidth=0.6, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)


def _parse_date_series(series: pd.Series) -> pd.Series:
    """
    Tự động parse một Series các giá trị chuỗi thời gian về datetime,
    hỗ trợ DD/MM/YYYY và các định dạng phổ biến khác.
    """
    try:
        # Thử parse với dayfirst=True trước (định dạng phổ biến tại Việt Nam)
        parsed = pd.to_datetime(series, dayfirst=True, errors='coerce')
        if parsed.notna().mean() > 0.8:
            return parsed
    except Exception:
        pass
    try:
        parsed = pd.to_datetime(series, errors='coerce')
        if parsed.notna().mean() > 0.8:
            return parsed
    except Exception:
        pass
    return pd.to_datetime(series, errors='coerce')


def _select_best_numeric_column(num_cols):
    """
    Chọn cột số quan trọng nhất dựa trên từ khóa tiếng Việt/Anh
    (ưu tiên doanh thu, lợi nhuận, tổng số tiền trước các cột đếm, số lượng).
    """
    if not num_cols:
        return None
    keywords = [
        'doanh thu', 'revenue', 'lợi nhuận', 'loi nhuan', 'profit', 
        'tổng', 'total', 'thành tiền', 'thanh tien', 'tiền', 'money', 
        'giá', 'price', 'amount', 'số lượng', 'so luong', 'quantity', 'count'
    ]
    for kw in keywords:
        for col in num_cols:
            if kw in str(col).lower():
                return col
    return num_cols[0]


def _detect_date_column(df):
    """Phát hiện cột ngày/thời gian."""
    for col in df.columns:
        # Nếu cột đã là datetime sẵn
        if df[col].dtype in ['datetime64[ns]', 'datetime64'] or pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    
    # Thử quét các cột dạng chuỗi
    for col in df.columns:
        if df[col].dtype == 'object' or pd.api.types.is_string_dtype(df[col]):
            col_lower = str(col).lower()
            # Chỉ check nếu tên cột chứa các từ khóa liên quan đến thời gian
            if any(k in col_lower for k in ['ngày', 'ngay', 'date', 'time', 'thời gian', 'thang', 'năm', 'tháng']):
                try:
                    sample = df[col].dropna().head(10).astype(str)
                    parsed = _parse_date_series(sample)
                    if parsed.dt.year.between(1990, 2100).mean() > 0.8:
                        return col
                except Exception:
                    pass
    return None


def _analyze_dataframe(df):
    """
    Phân tích cấu trúc DataFrame và trả về loại biểu đồ phù hợp nhất
    cùng thông tin cột cần thiết để vẽ.
    """
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    obj_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    date_col = _detect_date_column(df)

    # Loại bỏ date_col ra khỏi obj_cols để tránh vẽ bar_count/pie trên cột ngày
    if date_col and date_col in obj_cols:
        obj_cols.remove(date_col)

    # ── TRƯỜNG HỢP 1: Có cột ngày + cột số → Line Chart xu hướng ──────────
    if date_col and num_cols:
        best_num = _select_best_numeric_column(num_cols)
        return {
            "chart_type": "line",
            "date_col": date_col,
            "num_col": best_num,
            "reason": f"Co cot ngay '{date_col}' + so lieu '{best_num}' → Line Chart xu huong"
        }

    # ── TRƯỜNG HỢP 2: Cột text có 2-6 nhóm → Pie Chart ────────────────────
    for col in obj_cols:
        n = df[col].nunique()
        # Tránh các cột có toàn bộ giá trị duy nhất (không lặp lại) trừ khi dữ liệu quá nhỏ
        max_freq = df[col].value_counts().max()
        if 2 <= n <= 6 and (max_freq > 1 or len(df) < 5):
            return {
                "chart_type": "pie",
                "cat_col": col,
                "reason": f"Cot '{col}' co {n} nhom → Pie Chart the hien ty le"
            }

    # ── TRƯỜNG HỢP 3: Cột text có 7-20 nhóm + cột số → Bar tổng hợp ───────
    for col in obj_cols:
        n = df[col].nunique()
        if 7 <= n <= 20 and num_cols:
            best_num = _select_best_numeric_column(num_cols)
            return {
                "chart_type": "bar_agg",
                "cat_col": col,
                "num_col": best_num,
                "reason": f"Cot '{col}' co {n} nhom + so lieu '{best_num}' → Bar Chart tong hop"
            }

    # ── TRƯỜNG HỢP 4: Cột text nhiều nhóm → Bar đếm ─────────────────────
    bar_cat = None
    for col in obj_cols:
        n = df[col].nunique()
        # Tránh các cột định danh duy nhất (chỉ có count = 1)
        max_freq = df[col].value_counts().max()
        if 2 <= n <= 30 and (max_freq > 1 or len(df) < 5):
            bar_cat = col
            break
    if bar_cat:
        return {
            "chart_type": "bar_count",
            "cat_col": bar_cat,
            "reason": f"Cot '{bar_cat}' nhieu nhom → Bar Chart dem so luong"
        }

    # ── TRƯỜNG HỢP 5: Nhiều cột số → Multi-Bar so sánh ─────────────────
    if len(num_cols) >= 2:
        return {
            "chart_type": "multi_bar",
            "num_cols": num_cols[:4],
            "reason": f"Nhieu cot so → Bar Chart so sanh chi tieu"
        }

    # ── TRƯỜNG HỢP 6: Chỉ 1 cột số → Histogram phân phối ───────────────
    if len(num_cols) == 1:
        return {
            "chart_type": "hist",
            "num_col": num_cols[0],
            "reason": f"Chi 1 cot so '{num_cols[0]}' → Histogram phan phoi"
        }

    return {"chart_type": "none", "reason": "Khong tim thay cot phu hop"}


# ── TỪ ĐIỂN KÝ HIỆU GIẢI THÍCH ───────────────────────────────────────────────
_SYMBOL_MEANINGS = {
    'x':   'Da nop / Co mat',
    'X':   'Da nop / Co mat',
    'v':   'Vang / Chua nop',
    'V':   'Vang / Chua nop',
    'o':   'Khong co mat',
    'O':   'Khong co mat',
    '':    '(O trong)',
    'nan': '(Khong co du lieu)',
}


def _draw_legend_panel(fig, counts_series, col_name, total):
    """
    Vẽ bảng CHÚ THÍCH bên phải biểu đồ:
      Ký hiệu | Số lượng | Tỷ lệ | Ý nghĩa
    """
    ax_leg = fig.add_axes([0.67, 0.06, 0.31, 0.88])
    ax_leg.set_facecolor('#111827')
    ax_leg.axis('off')

    # ── Tiêu đề panel
    ax_leg.text(0.5, 0.975, 'CHÚ THÍCH',
                transform=ax_leg.transAxes,
                ha='center', va='top', fontsize=11, fontweight='bold',
                color='#f8fafc')
    ax_leg.text(0.5, 0.935, _safe_label(f'Cột dữ liệu: {col_name}'),
                transform=ax_leg.transAxes,
                ha='center', va='top', fontsize=8,
                color='#94a3b8', style='italic')

    # Đường kẻ dưới tiêu đề
    ax_leg.add_patch(mpatches.FancyBboxPatch(
        (0.04, 0.905), 0.92, 0.002,
        boxstyle='square,pad=0',
        facecolor='#10a37f', edgecolor='none',
        transform=ax_leg.transAxes))

    # ── Header cột
    hdr_y = 0.875
    ax_leg.text(0.08, hdr_y, 'Phân loại', transform=ax_leg.transAxes,
                fontsize=7.5, fontweight='bold', color='#64748b', va='top')
    ax_leg.text(0.42, hdr_y, 'Số lượng', transform=ax_leg.transAxes,
                fontsize=7.5, fontweight='bold', color='#64748b', va='top')
    ax_leg.text(0.60, hdr_y, 'Tỷ lệ (%)', transform=ax_leg.transAxes,
                fontsize=7.5, fontweight='bold', color='#64748b', va='top')

    # ── Các dòng
    y = 0.820
    row_h = min(0.13, 0.78 / max(len(counts_series), 1))

    for i, (label, count) in enumerate(counts_series.items()):
        if y < 0.06:
            break

        pct = count / total * 100
        label_str = str(label).strip()
        color = _PALETTE[i % len(_PALETTE)]
        meaning = _SYMBOL_MEANINGS.get(label_str, '')

        # Nền hàng
        ax_leg.add_patch(mpatches.FancyBboxPatch(
            (0.04, y - row_h * 0.85), 0.92, row_h * 0.88,
            boxstyle='round,pad=0.01',
            facecolor=color + '1A',  # 10% opacity
            edgecolor=color + '44',
            transform=ax_leg.transAxes, clip_on=False))

        # Chấm màu
        ax_leg.plot(0.10, y - row_h * 0.35, 'o',
                    color=color, markersize=8,
                    transform=ax_leg.transAxes, clip_on=False)

        # Ký hiệu (lớn, nổi bật)
        ax_leg.text(0.22, y - row_h * 0.25, label_str,
                    transform=ax_leg.transAxes,
                    fontsize=11, fontweight='bold', color='#f1f5f9', va='top')

        # Số lượng
        ax_leg.text(0.42, y - row_h * 0.25, str(int(count)),
                    transform=ax_leg.transAxes,
                    fontsize=9, color='#cbd5e1', va='top')

        # Tỷ lệ %
        ax_leg.text(0.60, y - row_h * 0.25, f'{pct:.1f}%',
                    transform=ax_leg.transAxes,
                    fontsize=9, color='#10a37f', fontweight='bold', va='top')

        # Ý nghĩa (nếu biết)
        if meaning:
            ax_leg.text(0.22, y - row_h * 0.60, meaning,
                        transform=ax_leg.transAxes,
                        fontsize=6.5, color='#64748b', va='top', style='italic')

        y -= row_h

    # ── Dòng tổng cộng
    ax_leg.add_patch(mpatches.FancyBboxPatch(
        (0.04, 0.01), 0.92, 0.002,
        boxstyle='square,pad=0',
        facecolor='#334155', edgecolor='none',
        transform=ax_leg.transAxes))
    ax_leg.text(0.08, 0.04, f'Tong: {int(total)} ban ghi',
                transform=ax_leg.transAxes,
                fontsize=7.5, color='#94a3b8', va='bottom')


def generate_auto_chart(df, file_id):
    """
    Phân tích thông minh DataFrame, chọn 1 loại biểu đồ phù hợp nhất,
    và vẽ kèm bảng CHÚ THÍCH giải thích ký hiệu trong dữ liệu.
    Trả về đường dẫn ảnh PNG hoặc None.
    """
    chart_path = f"static/charts/chart_{file_id}.png"
    full_path = os.path.join(os.getcwd(), chart_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    if os.path.exists(full_path):
        os.remove(full_path)

    info = _analyze_dataframe(df)
    chart_type = info.get("chart_type", "none")
    print(f"[CHART] Chon: {chart_type} | {info.get('reason', '')}")

    if chart_type == "none":
        return None

    # Chart có legend → rộng hơn để chứa panel bên phải
    has_legend = chart_type in ("pie", "bar_count", "bar_agg")
    fig_w = 12.5 if has_legend else 10.0
    fig = plt.figure(figsize=(fig_w, 6.2))
    fig.patch.set_facecolor("#0f172a")

    # Axes chính
    if has_legend:
        ax = fig.add_axes([0.05, 0.10, 0.59, 0.82])
    else:
        ax = fig.add_axes([0.08, 0.10, 0.88, 0.82])
    _setup_style(fig, ax)

    try:
        # ── PIE CHART ──────────────────────────────────────────────────────
        if chart_type == "pie":
            col = info["cat_col"]
            counts = df[col].value_counts()
            total = counts.sum()

            # Gộp nhóm < 3%
            pct_r = counts / total
            mask = pct_r < 0.03
            if mask.any() and len(counts) > 3:
                counts = counts[~mask]
                counts["Khac"] = total - counts.sum()

            colors = _PALETTE[:len(counts)]
            wedges, _, autotexts = ax.pie(
                counts.values,
                labels=None,
                autopct="%1.1f%%",
                colors=colors,
                startangle=90,
                pctdistance=0.72,
                wedgeprops={"linewidth": 2.5, "edgecolor": "#0f172a"}
            )
            for at in autotexts:
                at.set_color("white")
                at.set_fontsize(9.5)
                at.set_fontweight("bold")

            ax.set_title(_safe_label(f"Phân bổ: {col}"),
                         fontsize=15, pad=20, color="#f8fafc", fontweight="bold")
            ax.axis("equal")
            _draw_legend_panel(fig, counts, col, total)

        # ── BAR COUNT ─────────────────────────────────────────────────────
        elif chart_type == "bar_count":
            col = info["cat_col"]
            counts = df[col].value_counts().head(15)
            total = counts.sum()

            bars = ax.bar(
                [str(l) for l in counts.index],
                counts.values,
                color=_PALETTE[:len(counts)],
                edgecolor="none", width=0.65
            )
            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2,
                        h + counts.max() * 0.015,
                        f"{int(h):,}",
                        ha="center", va="bottom",
                        color="#f1f5f9", fontsize=8.5, fontweight="bold")

            ax.set_title(_safe_label(f"Số lượng theo: {col}"),
                         fontsize=15, pad=18, color="#f8fafc", fontweight="bold")
            ax.set_xlabel(_safe_label(col), fontsize=10, color="#cbd5e1")
            ax.set_ylabel("Số lượng", fontsize=10, color="#cbd5e1")
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
            plt.sca(ax)
            plt.xticks(rotation=40, ha="right", fontsize=8.5)
            _draw_legend_panel(fig, counts, col, total)

        # ── BAR AGG ───────────────────────────────────────────────────────
        elif chart_type == "bar_agg":
            cat_col = info["cat_col"]
            num_col = info["num_col"]
            agg = df.groupby(cat_col)[num_col].sum()\
                    .nlargest(15).sort_values(ascending=False)

            for i, (idx, val) in enumerate(agg.items()):
                ax.bar(str(idx), val,
                       color=_PALETTE[i % len(_PALETTE)],
                       edgecolor="none", width=0.65)
                ax.text(i, val + agg.max() * 0.015,
                        f"{val:,.0f}",
                        ha="center", va="bottom",
                        color="#f1f5f9", fontsize=8, fontweight="bold")

            ax.set_title(_safe_label(f"Tổng {num_col} theo {cat_col}"),
                         fontsize=15, pad=18, color="#f8fafc", fontweight="bold")
            ax.set_xlabel(_safe_label(cat_col), fontsize=10, color="#cbd5e1")
            ax.set_ylabel(_safe_label(num_col), fontsize=10, color="#cbd5e1")
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
            plt.sca(ax)
            plt.xticks(rotation=40, ha="right", fontsize=8.5)
            _draw_legend_panel(fig, agg, cat_col, agg.sum())

        # ── LINE CHART ────────────────────────────────────────────────────
        elif chart_type == "line":
            date_col = info["date_col"]
            num_col = info["num_col"]
            tmp = df[[date_col, num_col]].copy()
            tmp[date_col] = _parse_date_series(tmp[date_col])
            tmp = tmp.dropna().sort_values(date_col)
            tmp = tmp.groupby(date_col)[num_col].sum().reset_index()

            ax.plot(tmp[date_col], tmp[num_col],
                    color=_PALETTE[0], linewidth=2.2,
                    marker="o", markersize=5,
                    markerfacecolor="#fff", markeredgecolor=_PALETTE[0])
            ax.fill_between(tmp[date_col], tmp[num_col],
                            alpha=0.12, color=_PALETTE[0])

            # Annotate max point
            if len(tmp) > 1:
                max_i = tmp[num_col].idxmax()
                ax.annotate(
                    f"Max: {tmp[num_col].max():,.0f}",
                    xy=(tmp[date_col].iloc[max_i], tmp[num_col].iloc[max_i]),
                    xytext=(12, 12), textcoords="offset points",
                    color="#10a37f", fontsize=8.5, fontweight="bold",
                    arrowprops={"arrowstyle": "->", "color": "#10a37f", "lw": 1.2}
                )

            ax.set_title(_safe_label(f"Xu hướng {num_col} theo thời gian"),
                         fontsize=15, pad=18, color="#f8fafc", fontweight="bold")
            ax.set_xlabel(_safe_label(date_col), fontsize=10, color="#cbd5e1")
            ax.set_ylabel(_safe_label(num_col), fontsize=10, color="#cbd5e1")
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
            plt.sca(ax)
            plt.xticks(rotation=35, ha="right", fontsize=8.5)

        # ── MULTI-BAR ─────────────────────────────────────────────────────
        elif chart_type == "multi_bar":
            cols = info["num_cols"]
            means = {c: df[c].mean() for c in cols}
            x_labels = list(means.keys())
            y_vals = list(means.values())

            bars = ax.bar(x_labels, y_vals,
                          color=_PALETTE[:len(x_labels)],
                          edgecolor="none", width=0.55)
            for bar in bars:
                h = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2,
                        h + max(y_vals) * 0.015,
                        f"{h:,.1f}",
                        ha="center", va="bottom",
                        color="#f1f5f9", fontsize=8.5, fontweight="bold")

            ax.set_title("So sánh giá trị trung bình các chỉ tiêu",
                         fontsize=15, pad=18, color="#f8fafc", fontweight="bold")
            ax.set_ylabel("Giá trị trung bình", fontsize=10, color="#cbd5e1")
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{x:,.1f}"))
            plt.sca(ax)
            plt.xticks(rotation=30, ha="right", fontsize=9)

        # ── HISTOGRAM ─────────────────────────────────────────────────────
        elif chart_type == "hist":
            num_col = info["num_col"]
            data = df[num_col].dropna()
            n_bins = min(30, max(10, int(len(data) ** 0.5)))
            ax.hist(data, bins=n_bins,
                    color=_PALETTE[0], edgecolor="#0f172a", linewidth=0.4)

            mean_v, med_v = data.mean(), data.median()
            ax.axvline(mean_v, color="#f59e0b", linewidth=1.8,
                       linestyle="--", label=f"TB: {mean_v:.2f}")
            ax.axvline(med_v, color="#3b82f6", linewidth=1.8,
                       linestyle=":", label=f"TV: {med_v:.2f}")
            ax.legend(facecolor="#1e293b", edgecolor="#334155",
                      labelcolor="#f1f5f9", fontsize=8.5)

            ax.set_title(_safe_label(f"Phân phối: {num_col}"),
                         fontsize=15, pad=18, color="#f8fafc", fontweight="bold")
            ax.set_xlabel(_safe_label(num_col), fontsize=10, color="#cbd5e1")
            ax.set_ylabel("Tần suất", fontsize=10, color="#cbd5e1")
            ax.yaxis.set_major_formatter(
                mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

        # ── Lưu ──────────────────────────────────────────────────────────
        fig.savefig(full_path, dpi=130, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        return "/" + chart_path

    except Exception as e:
        print(f"[CHART ERROR] ({chart_type}): {e}")
        import traceback
        traceback.print_exc()
        plt.close("all")
        return None


def generate_multi_charts(df, file_id, max_charts=1):
    """
    Backward-compat wrapper — chỉ gọi generate_auto_chart (1 biểu đồ duy nhất).
    """
    path = generate_auto_chart(df, file_id)
    return [path] if path else []


def generate_chart_insight(df, chart_info):
    """
    Tạo insight dạng text giải thích biểu đồ từ thống kê dữ liệu.
    Không gọi AI — dùng heuristic thuần cho tốc độ nhanh.
    """
    insights = []
    chart_type = chart_info.get("chart_type", "none")
    if chart_type == "none":
        return []

    try:
        if chart_type == "pie":
            col = chart_info["cat_col"]
            counts = df[col].value_counts()
            total = counts.sum()
            top_name, top_val = counts.index[0], counts.iloc[0]
            top_pct = top_val / total * 100
            insights.append(f"📊 Nhóm **'{top_name}'** chiếm tỷ trọng lớn nhất ({top_pct:.1f}%)")
            if len(counts) >= 2:
                bot_name = counts.index[-1]
                bot_pct = counts.iloc[-1] / total * 100
                insights.append(f"📉 Nhóm **'{bot_name}'** chiếm ít nhất ({bot_pct:.1f}%)")
            if top_pct > 60:
                insights.append("⚠️ Phân bố **không đều** — một nhóm chiếm ưu thế rõ rệt")

        elif chart_type == "bar_count":
            col = chart_info["cat_col"]
            counts = df[col].value_counts()
            insights.append(f"📊 **'{counts.index[0]}'** xuất hiện nhiều nhất ({counts.iloc[0]:,} lần)")
            if len(counts) > 1 and counts.iloc[0] > counts.iloc[-1] * 3:
                insights.append("⚠️ Chênh lệch lớn giữa các nhóm — cần kiểm tra nguyên nhân")
            insights.append(f"📋 Tổng cộng **{len(counts)}** nhóm khác nhau")

        elif chart_type == "bar_agg":
            cat_col, num_col = chart_info["cat_col"], chart_info["num_col"]
            agg = df.groupby(cat_col)[num_col].sum()
            insights.append(f"📊 **'{agg.idxmax()}'** có tổng {num_col} cao nhất ({agg.max():,.0f})")
            if agg.max() > 0:
                gap = agg.max() - agg.min()
                insights.append(f"📏 Khoảng cách giữa cao nhất và thấp nhất: **{gap:,.0f}**")

        elif chart_type == "line":
            date_col = chart_info["date_col"]
            num_col = chart_info["num_col"]
            tmp = df[[date_col, num_col]].copy()
            tmp[date_col] = _parse_date_series(tmp[date_col])
            tmp = tmp.dropna().sort_values(date_col)
            tmp = tmp.groupby(date_col)[num_col].sum().reset_index()
            
            data = tmp[num_col]
            if len(data) > 1:
                trend = "tăng 📈" if data.iloc[-1] > data.iloc[0] else "giảm 📉"
                if data.iloc[0] != 0:
                    pct = abs(data.iloc[-1] - data.iloc[0]) / abs(data.iloc[0]) * 100
                    insights.append(f"Xu hướng **{trend}** ({pct:.1f}% thay đổi)")
                insights.append(f"Cao nhất: **{data.max():,.0f}** | Thấp nhất: **{data.min():,.0f}**")
                std = data.std()
                mean = data.mean()
                if mean > 0 and std / mean > 0.5:
                    insights.append("⚠️ Biến động **mạnh** — dữ liệu dao động nhiều")

        elif chart_type == "hist":
            num_col = chart_info["num_col"]
            data = pd.to_numeric(df[num_col], errors='coerce').dropna()
            skew = data.skew()
            if abs(skew) < 0.5:
                shape = "đối xứng (phân phối chuẩn)"
            elif skew > 0:
                shape = "lệch phải (nhiều giá trị nhỏ, ít giá trị lớn)"
            else:
                shape = "lệch trái (nhiều giá trị lớn, ít giá trị nhỏ)"
            insights.append(f"📊 Dạng phân phối: **{shape}**")
            insights.append(f"Trung bình: **{data.mean():,.2f}** | Trung vị: **{data.median():,.2f}**")

        elif chart_type == "multi_bar":
            cols = chart_info["num_cols"]
            means = {c: df[c].mean() for c in cols}
            max_col = max(means, key=means.get)
            insights.append(f"📊 Chỉ tiêu **'{max_col}'** có giá trị trung bình cao nhất ({means[max_col]:,.1f})")

    except Exception as e:
        print(f"[INSIGHT ERROR] {e}")

    return insights


def build_smart_summary_v2(df: pd.DataFrame) -> str:
    """
    Phiên bản cải tiến của build_smart_summary.
    Sử dụng Stratified Sampling + Statistics-First cho file lớn.
    Giảm 80-95% token so với v1.
    """
    import io as _io
    parts = []
    n_rows, n_cols = df.shape

    # 1. Cấu trúc cơ bản
    parts.append(f"Số dòng: {n_rows} | Số cột: {n_cols}")
    parts.append(f"Tên cột: {', '.join(df.columns.tolist())}")

    # 2. Kiểu dữ liệu
    dtype_lines = [f"  - {col}: {str(dt)}" for col, dt in df.dtypes.items()]
    parts.append("Kiểu dữ liệu:\n" + "\n".join(dtype_lines))

    # 3. Thống kê mô tả cho cột số
    num_cols = df.select_dtypes(include='number').columns.tolist()
    if num_cols:
        desc = df[num_cols].describe().round(2)
        buf = _io.StringIO()
        desc.to_string(buf)
        parts.append(f"Thống kê mô tả (cột số):\n{buf.getvalue()}")
        # Thêm: tương quan giữa các cột số (nếu >= 2 cột)
        if len(num_cols) >= 2:
            corr = df[num_cols].corr().round(2)
            corr_buf = _io.StringIO()
            corr.to_string(corr_buf)
            parts.append(f"Ma trận tương quan:\n{corr_buf.getvalue()}")

    # 4. Giá trị null
    null_info = df.isnull().sum()
    null_str = ", ".join(f"{c}={v}" for c, v in null_info.items() if v > 0)
    parts.append(f"Giá trị null: {null_str if null_str else 'Không có'}")

    # 5. Cột text: top giá trị
    cat_cols = df.select_dtypes(include='object').columns.tolist()
    for col in cat_cols[:5]:
        top = df[col].value_counts().head(5)
        top_str = ", ".join(f"{k}({v})" for k, v in top.items())
        nunique = df[col].nunique()
        parts.append(f"'{col}': {nunique} giá trị khác nhau. Top 5: {top_str}")

    # 6. Dữ liệu mẫu — STRATIFIED SAMPLING
    sample_buf = _io.StringIO()
    if n_rows <= 80:
        # File nhỏ: gửi hết
        sample = df
        sample_label = f"toàn bộ {n_rows}"
    elif n_rows <= 500:
        # File trung bình: head + tail + random
        head = df.head(30)
        tail = df.tail(20)
        mid_sample = df.iloc[30:-20].sample(min(50, len(df) - 50), random_state=42) if len(df) > 50 else pd.DataFrame()
        sample = pd.concat([head, mid_sample, tail]).drop_duplicates()
        sample_label = f"{len(sample)}/{n_rows} (stratified)"
    else:
        # File lớn: statistics-first, ít dữ liệu raw
        head = df.head(20)
        tail = df.tail(10)
        mid_sample = df.iloc[20:-10].sample(min(40, len(df) - 30), random_state=42)
        sample = pd.concat([head, mid_sample, tail]).drop_duplicates()
        sample_label = f"{len(sample)}/{n_rows} (stratified sampling)"

    sample.fillna("").to_csv(sample_buf, index=False)
    parts.append(f"Dữ liệu mẫu ({sample_label}):\n{sample_buf.getvalue()}")

    return "\n\n".join(parts)


def cleanup_orphan_charts(active_file_ids: list):
    """Xóa các file chart PNG không còn được sử dụng."""
    charts_dir = os.path.join(os.getcwd(), "static", "charts")
    if not os.path.exists(charts_dir):
        return
    for fname in os.listdir(charts_dir):
        if not fname.endswith(".png"):
            continue
        matched = any(str(fid) in fname for fid in active_file_ids)
        if not matched:
            try:
                os.remove(os.path.join(charts_dir, fname))
            except Exception:
                pass

def generate_plotly_json(df):
    """
    Tạo cấu trúc JSON cho biểu đồ Plotly dựa trên phân tích dữ liệu.
    """
    info = _analyze_dataframe(df)
    chart_type = info.get("chart_type", "none")
    
    try:
        if chart_type == "pie":
            col = info["cat_col"]
            counts = df[col].value_counts().reset_index()
            counts.columns = [col, 'Số lượng']
            fig = px.pie(counts, values='Số lượng', names=col, title=f'Phân bổ: {col}',
                         color_discrete_sequence=_PALETTE)
        
        elif chart_type == "bar_count":
            col = info["cat_col"]
            counts = df[col].value_counts().head(15).reset_index()
            counts.columns = [col, 'Số lượng']
            fig = px.bar(counts, x=col, y='Số lượng', title=f'Số lượng theo: {col}',
                         color=col, color_discrete_sequence=_PALETTE)
            
        elif chart_type == "bar_agg":
            cat_col = info["cat_col"]
            num_col = info["num_col"]
            df_copy = df.copy()
            df_copy[num_col] = pd.to_numeric(df_copy[num_col], errors='coerce')
            agg = df_copy.groupby(cat_col)[num_col].sum().nlargest(15).reset_index()
            fig = px.bar(agg, x=cat_col, y=num_col, title=f'Tổng {num_col} theo {cat_col}',
                         color=cat_col, color_discrete_sequence=_PALETTE)

        elif chart_type == "line":
            date_col = info["date_col"]
            num_col = info["num_col"]
            tmp = df[[date_col, num_col]].copy()
            tmp[date_col] = _parse_date_series(tmp[date_col])
            tmp[num_col] = pd.to_numeric(tmp[num_col], errors='coerce')
            tmp = tmp.dropna().sort_values(date_col)
            tmp = tmp.groupby(date_col)[num_col].sum().reset_index()
            fig = px.line(tmp, x=date_col, y=num_col, title=f'Xu hướng {num_col} theo thời gian',
                          markers=True)
            fig.update_traces(line_color=_PALETTE[0])

        elif chart_type == "hist":
            num_col = info["num_col"]
            data = df[[num_col]].copy()
            data[num_col] = pd.to_numeric(data[num_col], errors='coerce')
            fig = px.histogram(data, x=num_col, title=f'Phân phối: {num_col}',
                               color_discrete_sequence=[_PALETTE[0]])

        else:
            return None

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            font=dict(color="#f8fafc", family="Inter, sans-serif"),
            title_font=dict(size=18, color="#f8fafc"),
            margin=dict(l=40, r=40, t=60, b=40)
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        print(f"[PLOTLY ERROR] {e}")
        return None

def clean_excel_structure(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Tự động chuẩn hóa cấu trúc Excel:
    - Loại bỏ các dòng/cột trống ở rìa ngoài.
    - Tìm dòng header thực sự dựa trên mật độ và kiểu dữ liệu.
    - Đặt dòng header làm tên cột, cắt bỏ phần tiêu đề/metadata phía trên.
    - Loại bỏ các dòng tổng cộng, trung bình ở cuối bảng.
    - Chuẩn hóa tên cột (strip, điền Unnamed nếu trống, loại bỏ cột trống vô ích).
    """
    if df_raw.empty:
        return df_raw

    # 1. Tạo bản sao và loại bỏ các dòng, cột trống hoàn toàn ở rìa ngoài
    df = df_raw.copy()
    df = df.dropna(how='all', axis=1)
    df = df.dropna(how='all', axis=0)
    df = df.reset_index(drop=True)

    if df.empty:
        return df

    # Helper check numeric
    def is_data_numeric(val):
        if pd.isna(val):
            return False
        if isinstance(val, (int, float, np.number)):
            if isinstance(val, (int, np.integer)) and 1900 <= val <= 2100:
                return False
            return True
        try:
            float_val = float(val)
            if float_val.is_integer() and 1900 <= float_val <= 2100:
                return False
            return True
        except (ValueError, TypeError):
            return False

    # 2. Tìm chỉ số dòng chứa header
    max_non_null = df.notna().sum(axis=1).max()
    header_idx = 0
    found = False

    for i in range(len(df)):
        row_vals = df.iloc[i]
        non_null_count = row_vals.notna().sum()
        
        # Kiểm tra độ rộng của dòng
        if non_null_count >= max(3, int(max_non_null * 0.6)):
            # Đếm số lượng giá trị số liệu trong dòng
            data_numeric_count = sum(1 for val in row_vals if is_data_numeric(val))
            
            # Header thường không chứa dữ liệu số thuần túy (trừ khi là năm)
            if data_numeric_count <= non_null_count * 0.3:
                header_idx = i
                found = True
                break

    # Nếu không tìm thấy bằng heuristic, chọn dòng đầu tiên có độ rộng tương đối
    if not found:
        for i in range(len(df)):
            if df.iloc[i].notna().sum() >= max(2, int(max_non_null * 0.6)):
                header_idx = i
                break

    # 3. Tạo tiêu đề cột
    raw_headers = df.iloc[header_idx].tolist()
    cleaned_headers = []
    for col_idx, h in enumerate(raw_headers):
        if pd.isna(h) or str(h).strip() == "":
            cleaned_headers.append(f"Unnamed_{col_idx}")
        else:
            cleaned_headers.append(str(h).strip())

    # 4. Cắt dữ liệu từ dòng sau header
    df_data = df.iloc[header_idx + 1:].copy()
    df_data.columns = cleaned_headers

    # 5. Loại bỏ các cột "Unnamed" không có dữ liệu
    cols_to_keep = []
    for col in df_data.columns:
        # Nếu cột không rỗng hoàn toàn
        if not df_data[col].isna().all():
            # Và không phải toàn chuỗi rỗng
            non_empty = df_data[col].astype(str).str.strip().replace({'nan': '', 'None': '', '': np.nan})
            if not non_empty.isna().all():
                cols_to_keep.append(col)
    df_data = df_data[cols_to_keep]

    # 6. Xử lý trùng lặp tên cột
    seen = {}
    unique_headers = []
    for h in df_data.columns:
        if h in seen:
            seen[h] += 1
            unique_headers.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            unique_headers.append(h)
    df_data.columns = unique_headers

    # 7. Loại bỏ dòng tổng cộng / trung bình
    def is_aggregate_row(row_series):
        # Lấy giá trị ô đầu tiên không null
        first_val = None
        for val in row_series:
            if pd.notna(val) and str(val).strip() != "":
                first_val = val
                break
        if first_val is None:
            return False
        first_val_str = str(first_val).strip().lower()
        agg_keywords = [
            "tổng cộng", "tong cong", "tổng", "tong", "cộng", "cong", "lũy kế", "luy ke", 
            "trung bình", "trung binh", "kết quả", "ket qua", "bình quân", "binh quan",
            "total", "grand total", "subtotal", "sum", "average", "mean", "summary"
        ]
        for kw in agg_keywords:
            if first_val_str == kw or first_val_str.startswith(kw + " ") or first_val_str.startswith(kw + ":"):
                return True
        return False

    non_agg_mask = ~df_data.apply(is_aggregate_row, axis=1)
    df_data = df_data[non_agg_mask]

    # 8. Loại bỏ dòng trống hoàn toàn và reset index
    df_data = df_data.dropna(how='all', axis=0)
    df_data = df_data.reset_index(drop=True)

    return df_data
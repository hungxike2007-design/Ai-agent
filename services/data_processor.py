import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend (no UI window)

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import matplotlib.font_manager as fm
import os
import numpy as np

# ── CẤU HÌNH FONT ──────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.unicode_minus': False,
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
            suggestions.append({
                "column": col,
                "issue": f"Co {count} o trong",
                "action": "Dien gia tri trung binh hoac xoa dong"
            })
    for col in df.select_dtypes(include=['number']).columns:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            suggestions.append({
                "column": col,
                "issue": f"Co {neg_count} gia tri am",
                "action": "Xoa dong rac hoac lay gia tri tuyet doi"
            })
    return suggestions


# ── BẢNG MÀU CHUYÊN NGHIỆP ──────────────────────────────────────────────────
_PALETTE = [
    "#10a37f", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#14b8a6", "#f97316", "#6366f1", "#22c55e"
]


def _setup_style(fig, ax):
    """Áp dụng nền và grid nhất quán cho mọi biểu đồ."""
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")
    ax.tick_params(colors="#94a3b8", labelsize=9)
    ax.xaxis.label.set_color("#94a3b8")
    ax.yaxis.label.set_color("#94a3b8")
    ax.title.set_color("#f1f5f9")
    ax.spines[:].set_color("#334155")
    ax.grid(axis='y', color="#334155", linewidth=0.6, linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)


def _detect_date_column(df):
    """Phát hiện cột ngày/thời gian."""
    for col in df.select_dtypes(include=["datetime64"]).columns:
        return col
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            parsed = pd.to_datetime(df[col], errors="raise", infer_datetime_format=True)
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
    obj_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_col = _detect_date_column(df)

    # ── TRƯỜNG HỢP 1: Có cột ngày + cột số → Line Chart xu hướng ──────────
    if date_col and num_cols:
        return {
            "chart_type": "line",
            "date_col": date_col,
            "num_col": num_cols[0],
            "reason": f"Co cot ngay '{date_col}' + so lieu → Line Chart xu huong"
        }

    # ── TRƯỜNG HỢP 2: Cột text có 2-6 nhóm → Pie Chart ────────────────────
    for col in obj_cols:
        n = df[col].nunique()
        if 2 <= n <= 6:
            return {
                "chart_type": "pie",
                "cat_col": col,
                "reason": f"Cot '{col}' co {n} nhom → Pie Chart the hien ty le"
            }

    # ── TRƯỜNG HỢP 3: Cột text có 7-20 nhóm + cột số → Bar tổng hợp ───────
    for col in obj_cols:
        n = df[col].nunique()
        if 7 <= n <= 20 and num_cols:
            return {
                "chart_type": "bar_agg",
                "cat_col": col,
                "num_col": num_cols[0],
                "reason": f"Cot '{col}' co {n} nhom + so lieu → Bar Chart tong hop"
            }

    # ── TRƯỜNG HỢP 4: Cột text nhiều nhóm → Bar đếm ─────────────────────
    bar_cat = None
    for col in obj_cols:
        n = df[col].nunique()
        if 2 <= n <= 30:
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
    ax_leg.text(0.5, 0.975, 'CHU THICH',
                transform=ax_leg.transAxes,
                ha='center', va='top', fontsize=10, fontweight='bold',
                color='#f1f5f9')
    ax_leg.text(0.5, 0.935, _safe_label(f'Cot: {col_name}'),
                transform=ax_leg.transAxes,
                ha='center', va='top', fontsize=7.5,
                color='#94a3b8', style='italic')

    # Đường kẻ dưới tiêu đề
    ax_leg.add_patch(mpatches.FancyBboxPatch(
        (0.04, 0.905), 0.92, 0.002,
        boxstyle='square,pad=0',
        facecolor='#10a37f', edgecolor='none',
        transform=ax_leg.transAxes))

    # ── Header cột
    hdr_y = 0.875
    ax_leg.text(0.08, hdr_y, 'Ky hieu', transform=ax_leg.transAxes,
                fontsize=7, fontweight='bold', color='#64748b', va='top')
    ax_leg.text(0.42, hdr_y, 'SL', transform=ax_leg.transAxes,
                fontsize=7, fontweight='bold', color='#64748b', va='top')
    ax_leg.text(0.60, hdr_y, 'Ty le', transform=ax_leg.transAxes,
                fontsize=7, fontweight='bold', color='#64748b', va='top')

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

            ax.set_title(_safe_label(f"Phan bo: {col}"),
                         fontsize=14, pad=16, color="#f1f5f9", fontweight="bold")
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

            ax.set_title(_safe_label(f"So luong theo: {col}"),
                         fontsize=14, pad=14, fontweight="bold")
            ax.set_xlabel(_safe_label(col), fontsize=10)
            ax.set_ylabel("So luong", fontsize=10)
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

            ax.set_title(_safe_label(f"Tong {num_col} theo {cat_col}"),
                         fontsize=14, pad=14, fontweight="bold")
            ax.set_xlabel(_safe_label(cat_col), fontsize=10)
            ax.set_ylabel(_safe_label(num_col), fontsize=10)
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
            tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
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

            ax.set_title(_safe_label(f"Xu huong {num_col} theo thoi gian"),
                         fontsize=14, pad=14, fontweight="bold")
            ax.set_xlabel(_safe_label(date_col), fontsize=10)
            ax.set_ylabel(_safe_label(num_col), fontsize=10)
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

            ax.set_title("So sanh gia tri trung binh cac chi tieu",
                         fontsize=14, pad=14, fontweight="bold")
            ax.set_ylabel("Gia tri trung binh", fontsize=10)
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

            ax.set_title(_safe_label(f"Phan phoi: {num_col}"),
                         fontsize=14, pad=14, fontweight="bold")
            ax.set_xlabel(_safe_label(num_col), fontsize=10)
            ax.set_ylabel("Tan suat", fontsize=10)
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
"""インシデント・アクシデント報告システム - メインアプリ"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

from incident_constants import (
    DEPARTMENTS, CATEGORIES, SEVERITY_LEVELS, SEVERITY_ORDER, WEEKDAYS,
)
from incident_data_manager import load_data, filter_data, export_filtered_csv
from incident_form import render_report_form
from incident_analyzer import (
    summary_by_month, summary_by_department, summary_by_job_type,
    summary_by_shift, summary_by_weekday, summary_by_category,
    summary_by_severity, cross_tabulate, calc_incident_rate,
    calc_fall_rate, compare_periods, compare_year_over_year,
    recurrence_analysis, trend_analysis, get_month_data,
)
from incident_charts import (
    bar_chart, horizontal_bar_chart, line_chart, heatmap,
    pie_chart, comparison_bar,
)
from help_content import HELP_TEXTS
from demo_data import generate_demo_data


# ===== ページ設定 =====
st.set_page_config(
    page_title="インシデント報告システム",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== カスタムCSS =====
st.markdown("""
<style>
    /* メインコンテナ */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 1rem;
    }

    /* サイドバー */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #a0a0b8 !important;
        font-size: 0.85rem;
    }

    /* KPIカード */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    [data-testid="stMetric"] label {
        color: #6c757d !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #212529 !important;
    }

    /* デモバナー */
    .demo-banner {
        background: linear-gradient(90deg, #ff9800, #ff5722);
        color: white;
        padding: 0.7rem 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 600;
        margin-top: 0.5rem;
        margin-bottom: 1.5rem;
        font-size: 0.95rem;
        letter-spacing: 0.03em;
    }

    /* セクション見出し */
    .section-header {
        background: linear-gradient(90deg, #2196F3, #1976D2);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 1rem 0 0.5rem 0;
        font-size: 1.1rem;
        font-weight: 600;
    }

    /* タブスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.5rem;
    }

    /* テーブル */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }

    /* ボタン */
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #2196F3, #1976D2) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
    }

    /* フォーム内のディバイダー */
    .stForm hr {
        margin: 0.8rem 0;
    }

    /* ダウンロードボタン */
    .stDownloadButton > button {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


def render_sidebar():
    """サイドバー描画"""
    with st.sidebar:
        st.markdown("# 🏥 インシデント報告")
        st.caption("おもろまちメディカルセンター\n医療安全委員会")

        st.divider()

        # デモ/実データ切替
        is_demo = st.toggle("📊 デモモード", value=True, help="デモデータで機能を確認できます")

        st.divider()

        # ページ選択
        page = st.radio(
            "ナビゲーション",
            options=[
                "📝 報告入力",
                "📊 ダッシュボード",
                "🔍 詳細分析",
                "📋 データ一覧",
                "❓ 使い方",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        # フィルタ条件
        filters = {}
        if page not in ["📝 報告入力", "❓ 使い方"]:
            st.markdown("**🔎 フィルタ条件**")
            col1, col2 = st.columns(2)
            with col1:
                default_start = date(2025, 4, 1) if is_demo else date(date.today().year, 1, 1)
                filters["start_date"] = st.date_input("開始日", value=default_start)
            with col2:
                filters["end_date"] = st.date_input("終了日", value=date.today())

            filters["department"] = st.selectbox("部署", ["全部署"] + DEPARTMENTS)
            filters["category"] = st.selectbox("カテゴリ", ["全カテゴリ"] + CATEGORIES)
            filters["severity"] = st.selectbox(
                "重症度", ["全レベル"] + list(SEVERITY_LEVELS.keys())
            )

            st.divider()
            st.markdown("**⚙️ 指標設定**")
            filters["patient_days"] = st.number_input(
                "月間患者日数",
                min_value=1,
                value=2820,
                help="94床 × 30日 = 2,820",
            )

        # データ件数
        if is_demo:
            demo_df = generate_demo_data()
            count = len(demo_df)
        else:
            count = len(load_data())

        st.divider()
        st.metric("📁 登録件数", f"{count} 件")

        if is_demo:
            st.caption("🎭 デモデータ（2025年4月〜2026年3月）")

    return page, filters, is_demo


def get_data(is_demo: bool, filters: dict) -> pd.DataFrame:
    """データソースに応じてデータを取得"""
    if is_demo:
        df = generate_demo_data()
    else:
        df = load_data()
    return filter_data(df, **filters)


def page_report(is_demo: bool):
    """報告入力ページ"""
    if is_demo:
        st.markdown('<div class="demo-banner">🎭 デモモードで表示中 ー 実データの入力はデモモードをOFFにしてください</div>', unsafe_allow_html=True)

    render_report_form()

    # 直近の報告履歴
    df = load_data()
    if not df.empty:
        st.divider()
        st.markdown('<div class="section-header">📋 直近の報告（最新5件）</div>', unsafe_allow_html=True)
        recent = df.sort_values("reported_at", ascending=False).head(5)
        display_cols = ["report_id", "occurred_date", "department", "category", "severity"]
        available_cols = [c for c in display_cols if c in recent.columns]
        st.dataframe(
            recent[available_cols],
            column_config={
                "report_id": "報告ID",
                "occurred_date": "発生日",
                "department": "部署",
                "category": "カテゴリ",
                "severity": "重症度",
            },
            use_container_width=True,
            hide_index=True,
        )


def page_dashboard(df: pd.DataFrame, filters: dict, is_demo: bool):
    """ダッシュボードページ"""
    if is_demo:
        st.markdown('<div class="demo-banner">🎭 デモモードで表示中 ー 実際のデータではありません</div>', unsafe_allow_html=True)

    st.header("📊 ダッシュボード")

    if df.empty:
        st.info("📭 データがありません。「📝 報告入力」からインシデントを登録してください。")
        return

    patient_days = filters.get("patient_days", 2820)

    # 基準月を決定（デモは2026年3月、実データは当月）
    if is_demo:
        ref_year, ref_month = 2026, 3
    else:
        now = datetime.now()
        ref_year, ref_month = now.year, now.month

    current_month = get_month_data(df, ref_year, ref_month)
    period_comp = compare_periods(df, ref_year, ref_month)

    # KPIカード
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "📋 当月件数",
            f"{period_comp['当月件数']} 件",
            delta=f"{period_comp['増減']:+d}（前月比）",
            delta_color="inverse",
        )
    with col2:
        rate = calc_incident_rate(period_comp["当月件数"], patient_days)
        st.metric("📈 インシデント率", f"{rate}", help="1000患者日あたり")
    with col3:
        fall_rate = calc_fall_rate(current_month, patient_days)
        st.metric("🦶 転倒転落率", f"{fall_rate}", help="1000患者日あたり")
    with col4:
        severe = 0
        if not current_month.empty and "severity" in current_month.columns:
            severe = len(current_month[current_month["severity"].isin(["3a", "3b", "4a", "4b"])])
        st.metric("🚨 重症事例（Lv3↑）", f"{severe} 件")

    st.markdown("")  # スペーサー

    # 月次推移 & カテゴリ別
    col1, col2 = st.columns(2)
    with col1:
        trend = trend_analysis(df)
        if not trend.empty:
            fig = line_chart(trend, "年月", "件数", "📈 月次推移（移動平均付き）", y2="移動平均(3M)")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        cat = summary_by_category(df)
        if not cat.empty:
            fig = bar_chart(cat, "カテゴリ", "件数", "📊 カテゴリ別件数")
            st.plotly_chart(fig, use_container_width=True)

    # 部署別 & 重症度別
    col1, col2 = st.columns(2)
    with col1:
        dept = summary_by_department(df)
        if not dept.empty:
            fig = horizontal_bar_chart(dept, "件数", "部署", "🏢 部署別件数")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        sev = summary_by_severity(df)
        if not sev.empty:
            fig = pie_chart(sev, "重症度", "件数", "🎯 重症度分布")
            st.plotly_chart(fig, use_container_width=True)

    # 勤務帯別 & 曜日別
    col1, col2 = st.columns(2)
    with col1:
        shift = summary_by_shift(df)
        if not shift.empty:
            fig = bar_chart(shift, "勤務帯", "件数", "🕐 勤務帯別件数")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        wd = summary_by_weekday(df)
        if not wd.empty:
            fig = bar_chart(wd, "曜日", "件数", "📅 曜日別件数")
            st.plotly_chart(fig, use_container_width=True)

    # 職種別
    job = summary_by_job_type(df)
    if not job.empty:
        fig = horizontal_bar_chart(job, "件数", "職種", "👤 職種別件数")
        st.plotly_chart(fig, use_container_width=True)


def page_analysis(df: pd.DataFrame, filters: dict, is_demo: bool):
    """詳細分析ページ"""
    if is_demo:
        st.markdown('<div class="demo-banner">🎭 デモモードで表示中 ー 実際のデータではありません</div>', unsafe_allow_html=True)

    st.header("🔍 詳細分析")

    if df.empty:
        st.info("📭 データがありません。")
        return

    # 基準月
    if is_demo:
        ref_year, ref_month = 2026, 3
    else:
        now = datetime.now()
        ref_year, ref_month = now.year, now.month

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔀 クロス集計", "🕐 時間帯分析", "🦶 転倒転落専門",
        "📊 前月比・前年比", "🔄 再発分析"
    ])

    with tab1:
        st.markdown('<div class="section-header">クロス集計ヒートマップ</div>', unsafe_allow_html=True)
        col_options = {
            "部署": "department",
            "カテゴリ": "category",
            "職種": "job_type",
            "勤務帯": "shift",
            "曜日": "weekday",
            "重症度": "severity",
            "経験年数": "experience_years",
        }
        col1, col2 = st.columns(2)
        with col1:
            row_label = st.selectbox("行軸", list(col_options.keys()), index=0)
        with col2:
            col_label = st.selectbox("列軸", list(col_options.keys()), index=1)

        if row_label != col_label:
            cross = cross_tabulate(df, col_options[row_label], col_options[col_label])
            if not cross.empty:
                fig = heatmap(cross, f"{row_label} × {col_label}")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("行軸と列軸は異なる項目を選んでください")

    with tab2:
        st.markdown('<div class="section-header">勤務帯 × 曜日 ヒートマップ</div>', unsafe_allow_html=True)
        cross = cross_tabulate(df, "shift", "weekday")
        if not cross.empty:
            ordered_cols = [d for d in WEEKDAYS if d in cross.columns]
            cross = cross.reindex(columns=ordered_cols, fill_value=0)
            shift_order = ["日勤", "準夜", "深夜"]
            ordered_rows = [s for s in shift_order if s in cross.index]
            cross = cross.reindex(ordered_rows, fill_value=0)
            fig = heatmap(cross, "🕐 勤務帯 × 曜日")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("")
        st.markdown("**💡 読み方**: 色が濃いほど発生件数が多いセルです。特定の曜日・勤務帯に集中していないかを確認してください。")

    with tab3:
        st.markdown('<div class="section-header">転倒転落 専門分析</div>', unsafe_allow_html=True)
        fall_df = df[df["category"] == "転倒転落"]
        if fall_df.empty:
            st.info("転倒転落データがありません")
        else:
            # KPI
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("転倒転落 総件数", f"{len(fall_df)} 件")
            with col2:
                patient_days = filters.get("patient_days", 2820)
                fall_r = calc_fall_rate(df, patient_days)
                st.metric("1000患者日あたり", f"{fall_r}")
            with col3:
                severe_falls = len(fall_df[fall_df["severity"].isin(["3a", "3b", "4a", "4b"])]) if "severity" in fall_df.columns else 0
                st.metric("重症転倒（Lv3↑）", f"{severe_falls} 件")

            col1, col2 = st.columns(2)
            with col1:
                if "fall_location" in fall_df.columns:
                    loc = fall_df["fall_location"].dropna()
                    loc = loc[loc != ""]
                    if not loc.empty:
                        loc_counts = loc.value_counts().reset_index()
                        loc_counts.columns = ["場所", "件数"]
                        fig = bar_chart(loc_counts, "場所", "件数", "📍 発生場所別")
                        st.plotly_chart(fig, use_container_width=True)
            with col2:
                if "fall_injury" in fall_df.columns:
                    inj = fall_df["fall_injury"].dropna()
                    inj = inj[inj != ""]
                    if not inj.empty:
                        inj_counts = inj.value_counts().reset_index()
                        inj_counts.columns = ["障害", "件数"]
                        fig = bar_chart(inj_counts, "障害", "件数", "🩹 身体的障害別")
                        st.plotly_chart(fig, use_container_width=True)

            # リスク因子
            if "fall_risk_factors" in fall_df.columns:
                risk_series = fall_df["fall_risk_factors"].dropna()
                risk_series = risk_series[risk_series != ""]
                if not risk_series.empty:
                    all_risks = risk_series.str.split("|").explode()
                    risk_counts = all_risks.value_counts().reset_index()
                    risk_counts.columns = ["リスク因子", "件数"]
                    fig = horizontal_bar_chart(risk_counts, "件数", "リスク因子", "⚠️ リスク因子別件数")
                    st.plotly_chart(fig, use_container_width=True)

            # アセスメントスコア別
            if "fall_assessment_score" in fall_df.columns:
                score_series = fall_df["fall_assessment_score"].dropna()
                score_series = score_series[score_series != ""]
                if not score_series.empty:
                    score_counts = score_series.value_counts().reset_index()
                    score_counts.columns = ["スコア", "件数"]
                    fig = bar_chart(score_counts, "スコア", "件数", "📊 アセスメントスコア別")
                    st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown('<div class="section-header">前月比・前年同月比</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📅 前月比")
            comp = compare_periods(df, ref_year, ref_month)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("当月", f"{comp['当月件数']} 件")
                st.metric("増減", f"{comp['増減']:+d} 件")
            with c2:
                st.metric("前月", f"{comp['前月件数']} 件")
                st.metric("増減率", f"{comp['増減率(%)']:+.1f}%")
        with col2:
            st.markdown("#### 📆 前年同月比")
            yoy = compare_year_over_year(df, ref_year, ref_month)
            c1, c2 = st.columns(2)
            with c1:
                st.metric("当年", f"{yoy['当年件数']} 件")
                st.metric("増減", f"{yoy['増減']:+d} 件")
            with c2:
                st.metric("前年同月", f"{yoy['前年同月件数']} 件")
                st.metric("増減率", f"{yoy['増減率(%)']:+.1f}%")

        # カテゴリ別前月比
        st.markdown("#### カテゴリ別 前月比")
        if ref_month == 1:
            prev_year, prev_month = ref_year - 1, 12
        else:
            prev_year, prev_month = ref_year, ref_month - 1
        current_cat = get_month_data(df, ref_year, ref_month)
        prev_cat = get_month_data(df, prev_year, prev_month)

        if not current_cat.empty or not prev_cat.empty:
            current_counts = current_cat["category"].value_counts().to_dict() if not current_cat.empty else {}
            prev_counts = prev_cat["category"].value_counts().to_dict() if not prev_cat.empty else {}
            all_cats = sorted(set(list(current_counts.keys()) + list(prev_counts.keys())))
            current_filled = {c: current_counts.get(c, 0) for c in all_cats}
            prev_filled = {c: prev_counts.get(c, 0) for c in all_cats}
            fig = comparison_bar(current_filled, prev_filled, f"{ref_month}月", f"{prev_month}月", "カテゴリ別 前月比")
            st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.markdown('<div class="section-header">再発パターン分析</div>', unsafe_allow_html=True)
        recurrence = recurrence_analysis(df)
        if recurrence.empty:
            st.info("再発パターン（同一部署×同一カテゴリ×同一勤務帯で2件以上）はありません")
        else:
            st.warning(f"⚠️ **{len(recurrence)} パターン**の再発を検出しました")
            st.dataframe(recurrence, use_container_width=True, hide_index=True)

            # ヒートマップ
            st.markdown("")
            dept_cat = cross_tabulate(df, "department", "category")
            if not dept_cat.empty:
                fig = heatmap(dept_cat, "🔄 部署 × カテゴリ 再発マップ")
                st.plotly_chart(fig, use_container_width=True)


def page_data(df: pd.DataFrame, filters: dict, is_demo: bool):
    """データ一覧ページ"""
    if is_demo:
        st.markdown('<div class="demo-banner">🎭 デモモードで表示中 ー 実際のデータではありません</div>', unsafe_allow_html=True)

    st.header("📋 データ一覧")

    if df.empty:
        st.info("📭 データがありません。")
        return

    # サマリー
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("表示件数", f"{len(df)} 件")
    with col2:
        if "occurred_date" in df.columns and not df["occurred_date"].isna().all():
            st.metric("期間", f"{df['occurred_date'].min().strftime('%Y/%m/%d')} 〜 {df['occurred_date'].max().strftime('%Y/%m/%d')}")
    with col3:
        if "category" in df.columns:
            st.metric("カテゴリ数", f"{df['category'].nunique()} 種類")

    st.markdown("")

    # カラム名の日本語マッピング
    col_config = {
        "report_id": st.column_config.TextColumn("報告ID", width="small"),
        "occurred_date": st.column_config.DateColumn("発生日", width="small"),
        "occurred_time": st.column_config.TextColumn("時刻", width="small"),
        "shift": st.column_config.TextColumn("勤務帯", width="small"),
        "weekday": st.column_config.TextColumn("曜日", width="small"),
        "department": st.column_config.TextColumn("部署", width="medium"),
        "job_type": st.column_config.TextColumn("職種", width="small"),
        "category": st.column_config.TextColumn("カテゴリ", width="medium"),
        "severity": st.column_config.TextColumn("重症度", width="small"),
        "description": st.column_config.TextColumn("発生状況", width="large"),
        "causes": st.column_config.TextColumn("原因", width="medium"),
        "countermeasure": st.column_config.TextColumn("対策", width="large"),
        "patient_age": st.column_config.NumberColumn("年齢", width="small"),
        "patient_sex": st.column_config.TextColumn("性別", width="small"),
        "patient_dementia": st.column_config.TextColumn("認知症", width="small"),
    }

    st.dataframe(
        df,
        column_config=col_config,
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    # CSVダウンロード
    st.markdown("")
    csv_bytes = export_filtered_csv(df)
    st.download_button(
        "📥 CSVダウンロード",
        data=csv_bytes,
        file_name=f"incidents_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary",
    )


def page_help():
    """使い方ページ"""
    st.header("❓ 使い方ガイド")

    tabs = st.tabs(["📖 概要", "📝 報告方法", "🎯 重症度基準", "📊 分析の見方", "💬 FAQ"])

    with tabs[0]:
        st.markdown(HELP_TEXTS["about"])
    with tabs[1]:
        st.markdown(HELP_TEXTS["how_to_report"])
    with tabs[2]:
        st.markdown(HELP_TEXTS["severity_guide"])
    with tabs[3]:
        st.markdown(HELP_TEXTS["analysis_guide"])
    with tabs[4]:
        st.markdown(HELP_TEXTS["faq"])


# ===== メインルーティング =====
def main():
    page, filters, is_demo = render_sidebar()

    if page == "📝 報告入力":
        page_report(is_demo)
    elif page == "📊 ダッシュボード":
        df = get_data(is_demo, filters)
        page_dashboard(df, filters, is_demo)
    elif page == "🔍 詳細分析":
        df = get_data(is_demo, filters)
        page_analysis(df, filters, is_demo)
    elif page == "📋 データ一覧":
        df = get_data(is_demo, filters)
        page_data(df, filters, is_demo)
    elif page == "❓ 使い方":
        page_help()


if __name__ == "__main__":
    main()

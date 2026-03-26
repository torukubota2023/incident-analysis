"""インシデント報告 入力フォーム"""
import streamlit as st
from datetime import datetime, date, time

from incident_constants import (
    DEPARTMENTS, JOB_TYPES, EXPERIENCE_YEARS, REPORTER_ROLES,
    CATEGORIES, SEVERITY_LEVELS, CAUSE_OPTIONS, SEX_OPTIONS, DEMENTIA_OPTIONS,
    FALL_RISK_FACTORS, FALL_ASSESSMENT_SCORES, FALL_LOCATIONS, FALL_INJURIES,
    FALL_COUNTERMEASURES,
)
from incident_data_manager import append_record


def render_report_form():
    """報告入力フォームを描画する"""
    st.subheader("📝 インシデント・アクシデント報告")
    st.caption("入力目標: 3分以内 ｜ * は必須項目")

    with st.form("incident_report_form", clear_on_submit=True):
        # ===== 基本情報 =====
        st.markdown("### 📋 基本情報")
        col1, col2 = st.columns(2)
        with col1:
            occurred_date = st.date_input("発生日 *", value=date.today())
            department = st.selectbox("部署 *", options=DEPARTMENTS)
            experience_years = st.selectbox("経験年数 *", options=EXPERIENCE_YEARS)
        with col2:
            occurred_time = st.time_input("発生時刻 *", value=time(9, 0))
            job_type = st.selectbox("職種 *", options=JOB_TYPES)
            reporter_role = st.selectbox("報告者区分 *", options=REPORTER_ROLES)

        st.divider()

        # ===== 患者情報 =====
        st.markdown("### 🏥 患者情報")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            patient_age = st.number_input("年齢 *", min_value=0, max_value=120, value=70)
        with col2:
            patient_sex = st.selectbox("性別 *", options=SEX_OPTIONS)
        with col3:
            patient_dementia = st.selectbox("認知症 *", options=DEMENTIA_OPTIONS)
        with col4:
            patient_disease = st.text_input("病名", placeholder="例: 肺炎")

        st.divider()

        # ===== インシデント内容 =====
        st.markdown("### ⚠️ インシデント内容")
        category = st.selectbox("カテゴリ *", options=CATEGORIES)

        # 転倒転落の場合は追加項目を表示
        fall_risk_factors = ""
        fall_assessment_score = ""
        fall_location = ""
        fall_injury = ""

        if category == "転倒転落":
            st.markdown("#### 🔽 転倒転落 追加情報")
            col1, col2 = st.columns(2)
            with col1:
                fall_location = st.selectbox("発生場所 *", options=FALL_LOCATIONS)
                fall_assessment_score = st.selectbox(
                    "転倒転落アセスメントスコア", options=FALL_ASSESSMENT_SCORES
                )
            with col2:
                fall_injury = st.selectbox("身体的障害 *", options=FALL_INJURIES)

            selected_risk_factors = st.multiselect(
                "リスク因子（複数選択可）", options=FALL_RISK_FACTORS
            )
            fall_risk_factors = "|".join(selected_risk_factors)

        st.divider()

        # ===== 重症度 =====
        st.markdown("### 📊 重症度レベル")
        severity_options = [f"{k}: {v}" for k, v in SEVERITY_LEVELS.items()]
        severity_selected = st.selectbox("重症度 *", options=severity_options)
        severity = severity_selected.split(":")[0].strip()

        st.divider()

        # ===== 詳細記述 =====
        st.markdown("### 📝 詳細")
        description = st.text_area(
            "発生状況 *",
            placeholder="いつ・どこで・何が・どうなったか を簡潔に記載",
            height=100,
        )

        causes_selected = st.multiselect("原因（複数選択可） *", options=CAUSE_OPTIONS)
        causes = "|".join(causes_selected)

        countermeasure = st.text_area(
            "今後の対策 *",
            placeholder="再発防止のための具体的な対策を記載",
            height=100,
        )

        # ===== 送信ボタン =====
        st.divider()
        submitted = st.form_submit_button(
            "📤 報告を送信",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            record = {
                "occurred_date": str(occurred_date),
                "occurred_time": occurred_time.strftime("%H:%M"),
                "department": department,
                "job_type": job_type,
                "experience_years": experience_years,
                "reporter_role": reporter_role,
                "patient_age": patient_age,
                "patient_sex": patient_sex,
                "patient_disease": patient_disease,
                "patient_dementia": patient_dementia,
                "category": category,
                "severity": severity,
                "description": description,
                "causes": causes,
                "countermeasure": countermeasure,
                "fall_risk_factors": fall_risk_factors,
                "fall_assessment_score": fall_assessment_score,
                "fall_location": fall_location,
                "fall_injury": fall_injury,
            }

            success, message = append_record(record)
            if success:
                st.success(f"✅ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")

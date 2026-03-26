"""インシデントデータ管理モジュール"""
import os
import csv
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from filelock import FileLock

from incident_constants import (
    CSV_COLUMNS, SHIFT_RANGES, WEEKDAYS, SEVERITY_ORDER,
)


def get_csv_path() -> Path:
    """CSVファイルパスを返す"""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir / "incidents.csv"


def get_lock_path() -> Path:
    """ロックファイルパスを返す"""
    return get_csv_path().with_suffix(".csv.lock")


def create_empty_dataframe() -> pd.DataFrame:
    """空のDataFrameを返す（カラム定義済み）"""
    return pd.DataFrame(columns=CSV_COLUMNS)


@st.cache_data(ttl=30)
def load_data() -> pd.DataFrame:
    """CSVからデータを読み込む。ファイルがなければ空DFを返す"""
    csv_path = get_csv_path()
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return create_empty_dataframe()

    df = pd.read_csv(csv_path, dtype=str)
    # 型変換
    if "patient_age" in df.columns:
        df["patient_age"] = pd.to_numeric(df["patient_age"], errors="coerce")
    if "occurred_date" in df.columns:
        df["occurred_date"] = pd.to_datetime(df["occurred_date"], errors="coerce")
    return df


def derive_shift(hour: int) -> str:
    """発生時刻から勤務帯を自動判定"""
    for shift_name, (start, end) in SHIFT_RANGES.items():
        if start <= hour < end:
            return shift_name
    return "深夜"  # フォールバック


def derive_weekday(dt: datetime) -> str:
    """日付から曜日を返す"""
    return WEEKDAYS[dt.weekday()]


def generate_report_id(df: pd.DataFrame) -> str:
    """報告IDを自動採番（INC-YYYYMM-NNN形式）"""
    now = datetime.now()
    prefix = f"INC-{now.strftime('%Y%m')}-"

    if df.empty or "report_id" not in df.columns:
        return f"{prefix}001"

    # 今月のIDだけフィルタして最大番号を取得
    current_month_ids = df["report_id"].dropna()
    current_month_ids = current_month_ids[current_month_ids.str.startswith(prefix)]

    if current_month_ids.empty:
        return f"{prefix}001"

    max_num = current_month_ids.str.extract(r"(\d+)$").astype(int).max().iloc[0]
    return f"{prefix}{max_num + 1:03d}"


def validate_record(record: dict) -> tuple:
    """入力値バリデーション。(成功フラグ, メッセージ)を返す"""
    required = ["occurred_date", "occurred_time", "department", "job_type",
                 "experience_years", "reporter_role", "patient_age",
                 "patient_sex", "patient_dementia", "category", "severity",
                 "description", "causes"]

    missing = [k for k in required if not record.get(k)]
    if missing:
        return False, f"必須項目が未入力です: {', '.join(missing)}"

    # 転倒転落の場合は追加項目チェック
    if record.get("category") == "転倒転落":
        fall_required = ["fall_location", "fall_injury"]
        fall_missing = [k for k in fall_required if not record.get(k)]
        if fall_missing:
            return False, f"転倒転落の必須項目が未入力です: {', '.join(fall_missing)}"

    return True, "OK"


def append_record(record: dict) -> tuple:
    """1件追記。(成功フラグ, メッセージ)を返す"""
    # バリデーション
    is_valid, msg = validate_record(record)
    if not is_valid:
        return False, msg

    csv_path = get_csv_path()
    lock_path = get_lock_path()

    # 既存データを読み込んでID採番
    df = load_data()
    record["report_id"] = generate_report_id(df)
    record["reported_at"] = datetime.now().isoformat()

    # 勤務帯・曜日を自動導出
    try:
        hour = int(record["occurred_time"].split(":")[0])
        record["shift"] = derive_shift(hour)
    except (ValueError, IndexError):
        record["shift"] = ""

    try:
        dt = datetime.strptime(str(record["occurred_date"]), "%Y-%m-%d")
        record["weekday"] = derive_weekday(dt)
    except (ValueError, TypeError):
        record["weekday"] = ""

    # CSV書き込み（ファイルロック付き）
    try:
        with FileLock(str(lock_path)):
            file_exists = csv_path.exists() and csv_path.stat().st_size > 0
            with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                if not file_exists:
                    writer.writeheader()
                # CSVカラムに合わせて行データを構築
                row = {col: record.get(col, "") for col in CSV_COLUMNS}
                writer.writerow(row)

        # キャッシュクリア
        load_data.clear()
        return True, f"報告 {record['report_id']} を保存しました"
    except Exception as e:
        return False, f"保存エラー: {str(e)}"


def export_filtered_csv(df: pd.DataFrame) -> bytes:
    """DataFrameをCSVバイト列で返す（ダウンロード用）"""
    return df.to_csv(index=False).encode("utf-8-sig")


def filter_data(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """複合条件フィルタリング"""
    filtered = df.copy()

    if kwargs.get("start_date"):
        filtered = filtered[filtered["occurred_date"] >= pd.to_datetime(kwargs["start_date"])]
    if kwargs.get("end_date"):
        filtered = filtered[filtered["occurred_date"] <= pd.to_datetime(kwargs["end_date"])]
    if kwargs.get("department") and kwargs["department"] != "全部署":
        filtered = filtered[filtered["department"] == kwargs["department"]]
    if kwargs.get("category") and kwargs["category"] != "全カテゴリ":
        filtered = filtered[filtered["category"] == kwargs["category"]]
    if kwargs.get("severity") and kwargs["severity"] != "全レベル":
        filtered = filtered[filtered["severity"] == kwargs["severity"]]

    return filtered

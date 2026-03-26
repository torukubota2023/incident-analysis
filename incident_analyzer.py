"""インシデント分析エンジン"""
import pandas as pd
from datetime import datetime
from incident_constants import SEVERITY_ORDER, WEEKDAYS


def summary_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """月別件数集計"""
    if df.empty or "occurred_date" not in df.columns:
        return pd.DataFrame(columns=["年月", "件数"])
    temp = df.copy()
    temp["年月"] = temp["occurred_date"].dt.to_period("M").astype(str)
    result = temp.groupby("年月").size().reset_index(name="件数")
    return result.sort_values("年月")


def summary_by_department(df: pd.DataFrame) -> pd.DataFrame:
    """部署別件数集計"""
    if df.empty:
        return pd.DataFrame(columns=["部署", "件数"])
    return df.groupby("department").size().reset_index(name="件数").rename(
        columns={"department": "部署"}
    ).sort_values("件数", ascending=False)


def summary_by_job_type(df: pd.DataFrame) -> pd.DataFrame:
    """職種別件数集計"""
    if df.empty:
        return pd.DataFrame(columns=["職種", "件数"])
    return df.groupby("job_type").size().reset_index(name="件数").rename(
        columns={"job_type": "職種"}
    ).sort_values("件数", ascending=False)


def summary_by_shift(df: pd.DataFrame) -> pd.DataFrame:
    """勤務帯別件数集計"""
    if df.empty:
        return pd.DataFrame(columns=["勤務帯", "件数"])
    result = df.groupby("shift").size().reset_index(name="件数").rename(
        columns={"shift": "勤務帯"}
    )
    shift_order = {"日勤": 0, "準夜": 1, "深夜": 2}
    result["order"] = result["勤務帯"].map(shift_order)
    return result.sort_values("order").drop(columns=["order"])


def summary_by_weekday(df: pd.DataFrame) -> pd.DataFrame:
    """曜日別件数集計（月〜日の順）"""
    if df.empty:
        return pd.DataFrame(columns=["曜日", "件数"])
    result = df.groupby("weekday").size().reset_index(name="件数").rename(
        columns={"weekday": "曜日"}
    )
    weekday_order = {d: i for i, d in enumerate(WEEKDAYS)}
    result["order"] = result["曜日"].map(weekday_order)
    return result.sort_values("order").drop(columns=["order"])


def summary_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """カテゴリ別件数集計"""
    if df.empty:
        return pd.DataFrame(columns=["カテゴリ", "件数"])
    return df.groupby("category").size().reset_index(name="件数").rename(
        columns={"category": "カテゴリ"}
    ).sort_values("件数", ascending=False)


def summary_by_severity(df: pd.DataFrame) -> pd.DataFrame:
    """重症度別件数集計"""
    if df.empty:
        return pd.DataFrame(columns=["重症度", "件数"])
    result = df.groupby("severity").size().reset_index(name="件数").rename(
        columns={"severity": "重症度"}
    )
    result["order"] = result["重症度"].map(SEVERITY_ORDER)
    return result.sort_values("order").drop(columns=["order"])


def cross_tabulate(df: pd.DataFrame, row: str, col: str) -> pd.DataFrame:
    """任意2軸のクロス集計（ヒートマップ用）"""
    if df.empty:
        return pd.DataFrame()
    return pd.crosstab(df[row], df[col])


def calc_incident_rate(count: int, patient_days: int) -> float:
    """1000患者日あたりインシデント率"""
    if patient_days <= 0:
        return 0.0
    return round((count / patient_days) * 1000, 2)


def calc_fall_rate(df: pd.DataFrame, patient_days: int) -> float:
    """1000患者日あたり転倒転落率"""
    fall_count = len(df[df["category"] == "転倒転落"]) if not df.empty else 0
    return calc_incident_rate(fall_count, patient_days)


def get_month_data(df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
    """指定年月のデータを抽出"""
    if df.empty or "occurred_date" not in df.columns:
        return pd.DataFrame()
    mask = (df["occurred_date"].dt.year == year) & (df["occurred_date"].dt.month == month)
    return df[mask]


def compare_periods(df: pd.DataFrame, year: int, month: int) -> dict:
    """前月比の増減・増減率を算出"""
    current = get_month_data(df, year, month)
    # 前月
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    previous = get_month_data(df, prev_year, prev_month)

    current_count = len(current)
    prev_count = len(previous)
    diff = current_count - prev_count
    rate = round((diff / prev_count * 100), 1) if prev_count > 0 else 0.0

    return {
        "当月件数": current_count,
        "前月件数": prev_count,
        "増減": diff,
        "増減率(%)": rate,
    }


def compare_year_over_year(df: pd.DataFrame, year: int, month: int) -> dict:
    """前年同月比の増減・増減率を算出"""
    current = get_month_data(df, year, month)
    previous = get_month_data(df, year - 1, month)

    current_count = len(current)
    prev_count = len(previous)
    diff = current_count - prev_count
    rate = round((diff / prev_count * 100), 1) if prev_count > 0 else 0.0

    return {
        "当年件数": current_count,
        "前年同月件数": prev_count,
        "増減": diff,
        "増減率(%)": rate,
    }


def recurrence_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """同一部署×同一カテゴリ×同一勤務帯の再発パターン検出"""
    if df.empty:
        return pd.DataFrame(columns=["部署", "カテゴリ", "勤務帯", "件数"])
    result = (
        df.groupby(["department", "category", "shift"])
        .size()
        .reset_index(name="件数")
        .rename(columns={"department": "部署", "category": "カテゴリ", "shift": "勤務帯"})
    )
    # 2件以上を再発とみなす
    result = result[result["件数"] >= 2].sort_values("件数", ascending=False)
    return result


def trend_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """月次トレンド（3ヶ月移動平均付き）"""
    monthly = summary_by_month(df)
    if monthly.empty:
        return monthly
    monthly["移動平均(3M)"] = monthly["件数"].rolling(window=3, min_periods=1).mean().round(1)
    return monthly

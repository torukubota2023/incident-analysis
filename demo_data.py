"""デモデータ生成モジュール"""
import random
import pandas as pd
from datetime import datetime, timedelta
from incident_constants import (
    DEPARTMENTS, JOB_TYPES, EXPERIENCE_YEARS, REPORTER_ROLES,
    CATEGORIES, CAUSE_OPTIONS, SEX_OPTIONS, DEMENTIA_OPTIONS,
    FALL_RISK_FACTORS, FALL_ASSESSMENT_SCORES, FALL_LOCATIONS, FALL_INJURIES,
    CSV_COLUMNS, WEEKDAYS,
)
from incident_data_manager import derive_shift, derive_weekday


def generate_demo_data(seed: int = 42) -> pd.DataFrame:
    """リアルなインシデントデモデータを生成"""
    random.seed(seed)

    records = []
    report_num = 0

    # カテゴリの重み付け（転倒転落が最多）
    category_weights = {
        "転倒転落": 30,
        "与薬（注射・内服・外用）": 20,
        "チューブ・カテーテル": 12,
        "検査": 8,
        "医療機器": 7,
        "食事・誤嚥": 6,
        "コミュニケーション": 5,
        "患者誤認": 4,
        "手術・処置": 3,
        "離院": 3,
        "その他": 2,
    }
    categories_list = list(category_weights.keys())
    weights = list(category_weights.values())

    # 部署の重み（病棟が多い）
    dept_weights = {
        "5F病棟（外科・整形）": 30,
        "6F病棟（内科・ペイン）": 35,
        "外来": 10,
        "手術室": 5,
        "透析室": 5,
        "リハビリテーション室": 5,
        "放射線室": 3,
        "薬剤部": 4,
        "栄養科": 2,
        "事務部": 1,
    }
    depts = list(dept_weights.keys())
    dept_w = list(dept_weights.values())

    # 職種の重み（看護師が最多）
    job_weights = {
        "看護師": 55, "医師": 12, "薬剤師": 8, "リハビリスタッフ": 7,
        "介護士・補助者": 8, "放射線技師": 3, "栄養士": 3, "事務職": 2, "MSW": 1, "その他": 1,
    }
    jobs = list(job_weights.keys())
    job_w = list(job_weights.values())

    # 重症度の重み（レベル0-1が大半）
    severity_options = ["0", "1", "2", "3a", "3b", "4a", "4b"]
    severity_weights = [25, 35, 20, 10, 5, 3, 2]

    # 時間帯の重み（日勤帯が多い）
    hour_weights = {}
    for h in range(24):
        if 8 <= h < 16:
            hour_weights[h] = 5  # 日勤
        elif 16 <= h < 22:
            hour_weights[h] = 3  # 準夜
        else:
            hour_weights[h] = 1  # 深夜
    hours = list(hour_weights.keys())
    hour_w = list(hour_weights.values())

    # 発生状況テンプレート
    descriptions = {
        "転倒転落": [
            "ベッドサイドで立ち上がろうとした際にバランスを崩し転倒。ナースコールを押さず自力でトイレに行こうとしていた。",
            "夜間トイレに向かう途中、廊下で滑って転倒。スリッパを着用していた。",
            "車椅子からベッドへ移乗する際、ブレーキのかけ忘れにより車椅子が動き転落。",
            "リハビリ歩行訓練中にふらつきがあり、支えきれず膝から崩れ落ちた。",
            "ベッド柵を乗り越えようとしてベッドから転落。センサーマット反応前に転落していた。",
            "入浴後、浴室内で足を滑らせ尻餅をついた。床が濡れていた。",
            "ポータブルトイレ使用後、立ち上がる際にめまいを訴え、その場に座り込んだ。",
        ],
        "与薬（注射・内服・外用）": [
            "配薬時、同室の別患者の薬を渡してしまった。患者が服用前に看護師が気づき回収。",
            "点滴速度が指示と異なっていた。ダブルチェック時に確認不足があった。",
            "内服薬の朝食後分を配薬し忘れた。昼の巡回時に発見。",
            "インスリンの単位数を誤って投与。血糖値モニタリングにて発見。",
            "抗菌薬のアレルギー歴を確認せず投与準備を進めた。投与前に薬剤師が気づいた。",
        ],
        "チューブ・カテーテル": [
            "体動により末梢静脈ラインが自己抜去された。再挿入を実施。",
            "膀胱留置カテーテルが牽引され、一部抜けかかっていた。固定を確認し再固定。",
            "経鼻胃管の固定テープが剥がれ、チューブが数cm抜けていた。レントゲンで位置確認後再固定。",
            "中心静脈カテーテルの三方活栓が開放されたままになっていた。巡回時に発見し閉鎖。",
        ],
        "検査": [
            "検体ラベルの貼り間違いがあった。検査室で発見され再採血となった。",
            "検査予約の日時を患者に誤って伝達。検査室との確認で判明。",
            "採血時、抗凝固剤入りスピッツと凝固検査用スピッツを取り違えた。",
        ],
        "医療機器": [
            "輸液ポンプのアラームが鳴り続けていたが対応が遅れた。閉塞が原因。",
            "心電図モニターの電極が外れていたがアラーム設定がオフになっていた。",
            "酸素流量計の設定が指示と異なっていた。巡回時に発見し修正。",
        ],
        "食事・誤嚥": [
            "嚥下機能低下のある患者に常食が配膳された。食事開始前に発見し差し替え。",
            "食事介助中にむせ込みがあり、吸引を実施。SpO2低下なし。",
            "食物アレルギーのある食材が配膳に含まれていた。配膳チェック時に発見。",
        ],
        "コミュニケーション": [
            "医師の口頭指示を聞き間違え、検査オーダーの内容が異なっていた。実施前に確認し修正。",
            "退院日の変更が患者家族に伝わっておらず、迎えの手配ができていなかった。",
        ],
        "患者誤認": [
            "リストバンドの確認を怠り、隣のベッドの患者に血圧測定を実施した。",
            "検査室で患者名の呼び出し時、同姓の別患者が応答し入室しかけた。",
        ],
        "手術・処置": [
            "処置時の体位変換で点滴ルートに牽引がかかり接続が外れた。",
        ],
        "離院": [
            "認知症患者が病棟から離棟し、1階ロビーで発見された。",
        ],
        "その他": [
            "患者の私物（入れ歯）がシーツ交換時に紛失。洗濯室で発見。",
        ],
    }

    countermeasures = [
        "ダブルチェック体制の徹底と手順の再確認を行う",
        "スタッフへの注意喚起と事例共有を実施する",
        "環境整備（ベッド高さ・柵・照明）を見直す",
        "患者・家族への説明と協力依頼を行う",
        "センサーマットの適切な設置と作動確認を行う",
        "マニュアルの見直しと周知徹底を図る",
        "業務手順の改善とチェックリストの導入を検討する",
        "カンファレンスで再発防止策を検討し共有する",
        "リスクアセスメントの再評価と計画修正を行う",
        "指示受け時の復唱確認を徹底する",
    ]

    # 2025年4月〜2026年3月の1年間
    for year_month in pd.date_range("2025-04-01", "2026-03-31", freq="MS"):
        year = year_month.year
        month = year_month.month
        month_str = f"{year}{month:02d}"

        # 月あたり15〜25件
        n_incidents = random.randint(15, 25)

        for i in range(n_incidents):
            report_num += 1

            # 発生日をランダム生成
            days_in_month = (year_month + pd.offsets.MonthEnd(0)).day
            day = random.randint(1, days_in_month)
            occurred_date = datetime(year, month, day)

            # 発生時刻
            hour = random.choices(hours, weights=hour_w, k=1)[0]
            minute = random.choice([0, 10, 15, 20, 30, 40, 45, 50])

            # カテゴリ
            category = random.choices(categories_list, weights=weights, k=1)[0]

            # 部署
            department = random.choices(depts, weights=dept_w, k=1)[0]

            # 職種
            job_type = random.choices(jobs, weights=job_w, k=1)[0]

            # 重症度
            severity = random.choices(severity_options, weights=severity_weights, k=1)[0]

            # 原因（1〜3個）
            n_causes = random.randint(1, 3)
            causes = random.sample(CAUSE_OPTIONS, min(n_causes, len(CAUSE_OPTIONS)))

            # 患者情報
            patient_age = random.choices(
                range(20, 100),
                weights=[1]*30 + [2]*20 + [3]*20 + [2]*10,
                k=1
            )[0]

            # 転倒転落の追加情報
            fall_risk_factors = ""
            fall_assessment_score = ""
            fall_location = ""
            fall_injury = ""

            if category == "転倒転落":
                n_risks = random.randint(1, 4)
                fall_risk_factors = "|".join(random.sample(FALL_RISK_FACTORS, min(n_risks, len(FALL_RISK_FACTORS))))
                fall_assessment_score = random.choice(FALL_ASSESSMENT_SCORES)
                fall_location = random.choice(FALL_LOCATIONS)
                injury_weights = [40, 15, 15, 8, 5, 5, 7, 3, 2]
                fall_injury = random.choices(FALL_INJURIES, weights=injury_weights, k=1)[0]

            # 発生状況
            cat_descriptions = descriptions.get(category, descriptions["その他"])
            description = random.choice(cat_descriptions)

            record = {
                "report_id": f"INC-{month_str}-{report_num:03d}",
                "reported_at": (occurred_date + timedelta(hours=random.randint(1, 8))).isoformat(),
                "occurred_date": occurred_date.strftime("%Y-%m-%d"),
                "occurred_time": f"{hour:02d}:{minute:02d}",
                "shift": derive_shift(hour),
                "weekday": derive_weekday(occurred_date),
                "department": department,
                "job_type": job_type,
                "experience_years": random.choice(EXPERIENCE_YEARS),
                "reporter_role": random.choices(REPORTER_ROLES[:2], weights=[60, 40], k=1)[0],
                "patient_age": patient_age,
                "patient_sex": random.choice(SEX_OPTIONS),
                "patient_disease": random.choice([
                    "肺炎", "大腿骨骨折", "脳梗塞", "心不全", "糖尿病",
                    "COPD", "腰椎圧迫骨折", "胆嚢炎", "尿路感染症", "膝関節症",
                    "大腸癌", "胃潰瘍", "肝硬変", "腎盂腎炎", "変形性股関節症",
                ]),
                "patient_dementia": random.choices(
                    DEMENTIA_OPTIONS, weights=[50, 35, 15], k=1
                )[0],
                "category": category,
                "severity": severity,
                "description": description,
                "causes": "|".join(causes),
                "countermeasure": random.choice(countermeasures),
                "fall_risk_factors": fall_risk_factors,
                "fall_assessment_score": fall_assessment_score,
                "fall_location": fall_location,
                "fall_injury": fall_injury,
            }
            records.append(record)

    df = pd.DataFrame(records, columns=CSV_COLUMNS)
    df["occurred_date"] = pd.to_datetime(df["occurred_date"])
    df["patient_age"] = pd.to_numeric(df["patient_age"])
    return df

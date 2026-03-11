import re
from datetime import datetime
from typing import Dict, List, Any

import pandas as pd

OPTION_COLUMN_CANDIDATES = [
    "옵션",
    "옵션명",
    "상품옵션",
    "상품옵션(기본)",
    "품목명",
    "품목 옵션",
    "상품명(옵션포함)",
    "주문상품명",
    "상품명",
]

COUNT_COLUMN_CANDIDATES = [
    "수량",
    "주문수량",
    "상품수량",
]

STATUS_COLUMN_CANDIDATES = [
    "주문상태",
    "결제상태",
]

PAID_AT_COLUMN_CANDIDATES = [
    "결제일시(입금확인일)",
]

PURCHASE_AMOUNT_COLUMN_CANDIDATES = [
    "상품구매금액(KRW)",
    "상품구매금액",
]

POINT_COLUMN_CANDIDATES = [
    "사용한 적립금액(최종)",
]

COUPON_COLUMN_CANDIDATES = [
    "주문서 쿠폰 할인금액",
]

REFUND_COLUMN_CANDIDATES = [
    "실제 환불금액",
]

EXCLUDE_STATUS_KEYWORDS = [
    "취소",
    "환불",
    "반품",
]


def pick_column(df: pd.DataFrame, candidates: List[str]) -> str | None:
    col_map = {str(c).strip(): c for c in df.columns}
    for c in candidates:
        if c in col_map:
            return col_map[c]
    return None


def to_number(v) -> float:
    if pd.isna(v):
        return 0.0
    s = str(v).strip().replace(",", "").replace("원", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def is_blank(v) -> bool:
    if pd.isna(v):
        return True
    s = str(v).strip()
    return s == "" or s.lower() == "nan"


def normalize_option(option_text: str) -> str:
    if option_text is None:
        return "옵션없음"

    s = str(option_text).strip()
    if not s:
        return "옵션없음"

    s = re.sub(r"\s*수량=\([^)]*\)", "", s).strip()
    s = re.sub(r"\s{2,}", " ", s).strip()
    s = s.rstrip(",/|").strip()

    return s if s else "옵션없음"


def should_exclude_row(status_text: str) -> bool:
    s = str(status_text or "").strip()
    return any(k in s for k in EXCLUDE_STATUS_KEYWORDS)


def analyze_excel(
    excel_path: str,
    product_code: str,
    start_date: str,
    end_date: str,
    fee_rate: float,
    entity_type: str,
) -> Dict[str, Any]:
    if excel_path.lower().endswith(".csv"):
        df = pd.read_csv(excel_path)
    else:
        df = pd.read_excel(excel_path, engine="openpyxl")

    option_col = pick_column(df, OPTION_COLUMN_CANDIDATES)
    qty_col = pick_column(df, COUNT_COLUMN_CANDIDATES)
    status_col = pick_column(df, STATUS_COLUMN_CANDIDATES)

    paid_at_col = pick_column(df, PAID_AT_COLUMN_CANDIDATES)
    purchase_amount_col = pick_column(df, PURCHASE_AMOUNT_COLUMN_CANDIDATES)
    point_col = pick_column(df, POINT_COLUMN_CANDIDATES)
    coupon_col = pick_column(df, COUPON_COLUMN_CANDIDATES)
    refund_col = pick_column(df, REFUND_COLUMN_CANDIDATES)

    if option_col is None:
        raise RuntimeError(f"옵션 컬럼을 찾지 못했습니다. 현재 컬럼: {list(df.columns)}")
    if paid_at_col is None:
        raise RuntimeError(f"'결제일시(입금확인일)' 컬럼을 찾지 못했습니다. 현재 컬럼: {list(df.columns)}")
    if purchase_amount_col is None:
        raise RuntimeError(f"'상품구매금액(KRW)' 컬럼을 찾지 못했습니다. 현재 컬럼: {list(df.columns)}")
    if point_col is None:
        raise RuntimeError(f"'사용한 적립금액(최종)' 컬럼을 찾지 못했습니다. 현재 컬럼: {list(df.columns)}")
    if coupon_col is None:
        raise RuntimeError(f"'주문서 쿠폰 할인금액' 컬럼을 찾지 못했습니다. 현재 컬럼: {list(df.columns)}")
    if refund_col is None:
        raise RuntimeError(f"'실제 환불금액' 컬럼을 찾지 못했습니다. 현재 컬럼: {list(df.columns)}")

    work = df.copy()

    work = work[~work[paid_at_col].apply(is_blank)]

    if status_col is not None:
        work = work[~work[status_col].astype(str).apply(should_exclude_row)]

    work["__option__"] = work[option_col].apply(normalize_option)

    work["__purchase_amount__"] = work[purchase_amount_col].apply(to_number)
    work["__point_amount__"] = work[point_col].apply(to_number)
    work["__coupon_amount__"] = work[coupon_col].apply(to_number)
    work["__refund_amount__"] = work[refund_col].apply(to_number)

    work["__amount__"] = (
        work["__purchase_amount__"]
        - work["__point_amount__"]
        - work["__coupon_amount__"]
        - work["__refund_amount__"]
    )

    if qty_col is not None:
        work["__qty__"] = work.apply(
            lambda r: 0 if r["__refund_amount__"] > 0 else int(to_number(r[qty_col])) if to_number(r[qty_col]) > 0 else 1,
            axis=1
        )
    else:
        work["__qty__"] = work.apply(
            lambda r: 0 if r["__refund_amount__"] > 0 else 1,
            axis=1
        )

    option_rows = []
    grouped = work.groupby("__option__", dropna=False)

    total_payment_amount = float(work["__amount__"].sum())
    total_payment_count = int(work["__qty__"].sum())

    for option_name, g in grouped:
        option_rows.append({
            "option_name": option_name,
            "payment_amount": float(g["__amount__"].sum()),
            "payment_count": int(g["__qty__"].sum()),
        })

    # 옵션명 기준 오름차순 정렬
    option_rows = sorted(option_rows, key=lambda x: x["option_name"])

    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    elapsed_days = (end_dt - start_dt).days + 1

    fee_amount = round(total_payment_amount * (fee_rate / 100.0))
    estimated_settlement_amount = fee_amount

    return {
        "product_code": product_code,
        "start_date": start_date,
        "end_date": end_date,
        "elapsed_days": elapsed_days,
        "fee_rate": fee_rate,
        "entity_type": entity_type,
        "total_payment_amount": total_payment_amount,
        "total_payment_count": total_payment_count,
        "fee_amount": fee_amount,
        "estimated_settlement_amount": estimated_settlement_amount,
        "options": option_rows,
        "source_file": excel_path,
    }
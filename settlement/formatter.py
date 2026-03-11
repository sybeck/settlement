from typing import Dict, Any


def won(v: float) -> str:
    return f"{int(round(v)):,.0f}원"


def format_result_message(result: Dict[str, Any]) -> str:
    lines = []
    lines.append("*✅ 정산 집계 결과*")
    lines.append(f"*기간: {result['start_date']} ~ {result['end_date']} ({result['elapsed_days']}일)*")
    lines.append(
        f"*총 결제 금액: {won(result['total_payment_amount'])} ({result['total_payment_count']:,}건)*"
    )
    lines.append("")

    lines.append("옵션별 결제 금액")
    for row in result["options"]:
        lines.append(
            f"- {row['option_name']}: {won(row['payment_amount'])} ({row['payment_count']:,}건)"
        )

    lines.append("")
    lines.append(
        f"(참고) 수수료율 {result['fee_rate']}% / 수수료 {won(result['fee_amount'])}"
    )
    return "\n".join(lines)
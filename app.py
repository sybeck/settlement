import os
import traceback
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from settlement.slack_views import build_settlement_modal
from settlement.cafe24_downloader import download_cafe24_excel
from settlement.analyzer import analyze_excel
from settlement.formatter import format_result_message

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])


def safe_str(v):
    return "" if v is None else str(v)


@app.command("/settlement")
def handle_settlement_command(ack, body, client, logger):
    ack()

    try:
        client.views_open(
            trigger_id=body["trigger_id"],
            view=build_settlement_modal(
                channel_id=body["channel_id"],
                user_id=body["user_id"],
            ),
        )
    except Exception as e:
        logger.exception("Failed to open modal")
        client.chat_postEphemeral(
            channel=body["channel_id"],
            user=body["user_id"],
            text=f"정산 입력창을 여는 중 오류가 발생했어요.\n```{safe_str(e)}```",
        )


@app.view("settlement_submit")
def handle_settlement_submit(ack, body, view, client, logger):
    ack()

    state_values = view["state"]["values"]

    brand = state_values["brand_block"]["brand_action"]["selected_option"]["value"]
    product_code = state_values["product_code_block"]["product_code_action"]["value"].strip()
    start_date = state_values["start_date_block"]["start_date_action"]["selected_date"]
    end_date = state_values["end_date_block"]["end_date_action"]["selected_date"]
    fee_rate = state_values["fee_rate_block"]["fee_rate_action"]["value"].strip()
    entity_type = state_values["entity_type_block"]["entity_type_action"]["selected_option"]["value"]

    metadata = view.get("private_metadata", "")
    channel_id, user_id = metadata.split("|")

    parent_ts = None

    try:
        parent = client.chat_postMessage(
            channel=channel_id,
            text=(
                f":receipt: 정산 요청 접수\n"
                f"- 브랜드: {brand}\n"
                f"- 상품코드: {product_code}\n"
                f"- 조회기간: {start_date} ~ {end_date}\n"
                f"- 수수료율: {fee_rate}%\n"
                f"- 구분: {entity_type}\n"
                f"- 요청자: <@{user_id}>"
            ),
        )
        parent_ts = parent["ts"]

        client.chat_postMessage(
            channel=channel_id,
            thread_ts=parent_ts,
            text="집계를 시작하겠습니다. 1분정도 소요됩니다.",
        )

        excel_path, meta = download_cafe24_excel(
            brand=brand,
            product_code=product_code,
            start_date=start_date,
            end_date=end_date,
        )

        result = analyze_excel(
            excel_path=excel_path,
            product_code=product_code,
            start_date=start_date,
            end_date=end_date,
            fee_rate=float(fee_rate),
            entity_type=entity_type,
        )

        msg = format_result_message(result)

        client.chat_postMessage(
            channel=channel_id,
            thread_ts=parent_ts,
            text=msg,
        )

    except Exception as e:
        logger.exception("Settlement flow failed")
        tb = traceback.format_exc()[:3500]

        if parent_ts:
            client.chat_postMessage(
                channel=channel_id,
                thread_ts=parent_ts,
                text=f":warning: 정산 처리 중 오류가 발생했어요.\n```{safe_str(e)}```\n```{tb}```",
            )
        else:
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f":warning: 정산 처리 중 오류가 발생했어요.\n```{safe_str(e)}```",
            )


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
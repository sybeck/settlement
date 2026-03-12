def build_settlement_modal(channel_id: str, user_id: str) -> dict:
    return {
        "type": "modal",
        "callback_id": "settlement_submit",
        "title": {
            "type": "plain_text",
            "text": "정산 요청",
        },
        "submit": {
            "type": "plain_text",
            "text": "실행",
        },
        "close": {
            "type": "plain_text",
            "text": "취소",
        },
        "private_metadata": f"{channel_id}|{user_id}",
        "blocks": [

            {
                "type": "input",
                "block_id": "gonggu_name_block",
                "label": {"type": "plain_text", "text": "공구명"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "gonggu_name_action",
                    "placeholder": {"type": "plain_text", "text": "예: 이애람 공구 2차"},
                },
            },

            {
                "type": "input",
                "block_id": "product_name_block",
                "label": {"type": "plain_text", "text": "제품명"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "product_name_action",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "예: 뉴턴젤리",
                    },
                },
            },

            {
                "type": "input",
                "block_id": "brand_block",
                "label": {"type": "plain_text", "text": "브랜드"},
                "element": {
                    "type": "static_select",
                    "action_id": "brand_action",
                    "placeholder": {"type": "plain_text", "text": "브랜드 선택"},
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "부담제로"},
                            "value": "burdenzero",
                        },
                        {
                            "text": {"type": "plain_text", "text": "브레인올로지"},
                            "value": "brainology",
                        },
                    ],
                },
            },

            {
                "type": "input",
                "block_id": "product_code_block",
                "label": {"type": "plain_text", "text": "상품코드"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "product_code_action",
                    "placeholder": {"type": "plain_text", "text": "예: P00000CY"},
                },
            },

            {
                "type": "input",
                "block_id": "start_date_block",
                "label": {"type": "plain_text", "text": "시작 날짜"},
                "element": {
                    "type": "datepicker",
                    "action_id": "start_date_action",
                },
            },

            {
                "type": "input",
                "block_id": "end_date_block",
                "label": {"type": "plain_text", "text": "종료 날짜"},
                "element": {
                    "type": "datepicker",
                    "action_id": "end_date_action",
                },
            },

            {
                "type": "input",
                "block_id": "fee_rate_block",
                "label": {"type": "plain_text", "text": "수수료율(%)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "fee_rate_action",
                    "placeholder": {"type": "plain_text", "text": "예: 20"},
                },
            },

            {
                "type": "input",
                "block_id": "entity_type_block",
                "label": {"type": "plain_text", "text": "회사 / 개인"},
                "element": {
                    "type": "static_select",
                    "action_id": "entity_type_action",
                    "placeholder": {"type": "plain_text", "text": "구분 선택"},
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": "회사"},
                            "value": "company",
                        },
                        {
                            "text": {"type": "plain_text", "text": "개인"},
                            "value": "individual",
                        },
                    ],
                },
            },
        ],
    }
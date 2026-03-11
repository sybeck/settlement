import os
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any

from playwright.sync_api import sync_playwright

from .config import get_brand_credential, get_download_dir, get_headless

LOGIN_URL = "https://eclogin.cafe24.com/Shop/"
ORDER_LIST_URL_TEMPLATE = "https://{admin_id}.cafe24.com/admin/php/shop1/s_new/order_list.php?rows=20&searchSorting=order_desc&btnDate=9999&date_type=order_date&searchSorting=order_desc&memberType=1&shop_no_order=1&orderStatusPayment=all&orderStatusNotPayCancel=N&orderStatusCancel=N&orderSearchCancelStatus=all&orderStatusExchange=N&orderSearchExchangeStatus=all&orderStatusReturn=N&orderStatusRefund=N&orderSearchRefundStatus=all&orderSearchShipStatus=all&orderStatus[]=all&orderStatus[]=N10&orderStatus[]=N20&orderStatus[]=N22&orderStatus[]=N21&orderStatus[]=N30&orderStatus[]=N40&incoming=T&realclick=T&initSearchFlag=T&year1=2026&month1=03&day1=12&year2=2026&month2=03&day2=12&start_date=2026-03-12&end_date=2026-03-12&start_time=00:00&end_time=23:59"


def ensure_dir(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def sleep_3(page=None):
    if page:
        page.wait_for_timeout(3000)
    else:
        time.sleep(3)


def find_first_visible(page, selectors):
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=2000):
                return locator
        except Exception:
            continue
    return None


def login_cafe24(page, admin_id: str, password: str):
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    sleep_3(page)

    id_box = find_first_visible(page, [
        'input[name="mall_id"]',
        'input[name="userid"]',
        'input[type="text"]',
        '#mall_id',
        '#userid',
    ])
    pw_box = find_first_visible(page, [
        'input[name="passwd"]',
        'input[name="password"]',
        'input[type="password"]',
        '#passwd',
        '#password',
    ])

    if id_box is None or pw_box is None:
        raise RuntimeError("Cafe24 로그인 selector를 찾지 못했습니다. 실제 페이지에서 selector를 확인해 주세요.")

    id_box.click()
    id_box.fill(admin_id)

    pw_box.click()
    pw_box.fill(password)

    login_btn = find_first_visible(page, [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("로그인")',
        'a:has-text("로그인")',
    ])
    if login_btn is None:
        raise RuntimeError("로그인 버튼 selector를 찾지 못했습니다.")

    login_btn.click()
    sleep_3(page)


def click_search(page):
    try:
        page.get_by_role("link", name="검색", exact=True).click()
        sleep_3(page)
        return
    except Exception:
        pass

    btn = find_first_visible(page, [
        'a:has-text("검색")',
        'button:has-text("검색")',
        'input[value="검색"]',
    ])
    if btn is None:
        raise RuntimeError("검색 버튼을 찾지 못했습니다.")
    btn.click()
    sleep_3(page)


def click_excel_download_button(page):
    page.wait_for_timeout(5000)
    page.locator("#eExcelDownloadBtn").first.click()
    sleep_3(page)


def request_excel_in_popup(page1):
    page1.locator("#aManagesList").select_option("49")

    def on_dialog(dialog):
        dialog.accept()

    page1.on("dialog", on_dialog)

    page1.get_by_role("link", name="엑셀파일요청").click()
    sleep_3(page1)


def click_first_download_button(page1, save_dir: str) -> str:
    # "다운로드 리스트" 헤딩이 보일 때까지 대기
    page1.get_by_role("heading", name="다운로드 리스트").wait_for(timeout=15000)
    sleep_3(page1)

    # "쇼핑몰" 컬럼헤더가 있는 표를 우선 찾음
    target_table = page1.locator("table").filter(
        has=page1.get_by_role("columnheader", name="쇼핑몰")
    ).first

    if target_table.count() == 0:
        raise RuntimeError("다운로드 리스트에서 '쇼핑몰' 컬럼헤더가 있는 표를 찾지 못했습니다.")

    first_row = target_table.locator("tbody tr").first
    if first_row.count() == 0:
        raise RuntimeError("다운로드 리스트 표에서 첫 번째 데이터 행을 찾지 못했습니다.")

    last_cell = first_row.locator("td").last

    with page1.expect_download() as download_info:
        clicked = False

        # 1순위: 마지막 칸 안의 download_status_* id 버튼/링크
        try:
            btn = last_cell.locator('[id^="download_status_"]').first
            if btn.count() > 0:
                btn.click()
                clicked = True
        except Exception:
            pass

        # 2순위: 마지막 칸 안의 "다운로드" 링크
        if not clicked:
            try:
                btn = last_cell.get_by_role("link", name="다운로드").first
                if btn.count() > 0:
                    btn.click()
                    clicked = True
            except Exception:
                pass

        # 3순위: 마지막 칸 안의 a/button/input 요소
        if not clicked:
            for selector in [
                "a",
                "button",
                'input[type="button"]',
                'input[type="submit"]',
            ]:
                try:
                    btn = last_cell.locator(selector).first
                    if btn.count() > 0:
                        btn.click()
                        clicked = True
                        break
                except Exception:
                    pass

        # 4순위 fallback: 페이지 전체에서 download_status_* 첫 요소
        if not clicked:
            try:
                btn = page1.locator('[id^="download_status_"]').first
                if btn.count() > 0:
                    btn.click()
                    clicked = True
            except Exception:
                pass

        if not clicked:
            raise RuntimeError("다운로드 리스트 첫 번째 행의 마지막 칸에서 다운로드 버튼을 찾지 못했습니다.")

    download = download_info.value
    filename = download.suggested_filename or f"settlement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(save_dir, filename)
    download.save_as(file_path)
    return file_path


def download_cafe24_excel(
    brand: str,
    product_code: str,
    start_date: str,
    end_date: str,
) -> Tuple[str, Dict[str, Any]]:
    cred = get_brand_credential(brand)

    if not cred.admin_id or not cred.password:
        raise RuntimeError(f"{brand} 브랜드의 Cafe24 로그인 정보가 .env에 없습니다.")

    save_dir = ensure_dir(get_download_dir())
    headless = get_headless()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=3000,
        )
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        login_cafe24(page, cred.admin_id, cred.password)

        target_url = ORDER_LIST_URL_TEMPLATE.format(admin_id=cred.admin_id)
        page.goto(target_url, wait_until="domcontentloaded")
        sleep_3(page)

        page.locator("#startDate").click()
        page.locator("#startDate").fill(start_date)

        page.locator("#endDate").click()
        page.locator("#endDate").fill(end_date)

        page.locator('select[name="MSK[]"]').select_option("product_code")

        page.locator("#sBaseSearchBox").click()
        page.locator("#sBaseSearchBox").fill(product_code)

        click_search(page)

        with page.expect_popup() as popup_info:
            click_excel_download_button(page)
        page1 = popup_info.value
        page1.wait_for_load_state("domcontentloaded")
        sleep_3(page1)

        request_excel_in_popup(page1)

        file_path = click_first_download_button(page1, save_dir)

        meta = {
            "brand": brand,
            "admin_id": cred.admin_id,
            "product_code": product_code,
            "start_date": start_date,
            "end_date": end_date,
        }

        context.close()
        browser.close()

    return file_path, meta
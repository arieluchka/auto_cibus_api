import time

from playwright.sync_api import Playwright, sync_playwright
from additional_data import login_page

with sync_playwright() as playwright:

    browser = playwright.chromium.launch(headless=False
                                         )
    context = browser.new_context()
    context.tracing.start(snapshots=True, screenshots=True,sources=True)
    try:
        page = context.new_page()
        page.goto(login_page)
        page.get_by_label("אימייל / מספר נייד / שם משתמש").click()
        page.get_by_label("אימייל / מספר נייד / שם משתמש").fill("ariel.agra@gmail.com")
        page.get_by_label("אימייל / מספר נייד / שם משתמש").press("Enter")
        page.wait_for_selector("#password")

        page.get_by_label("מה הסיסמה?").click()
        page.get_by_label("מה הסיסמה?").fill("CibuSArieL!123")
        page.get_by_label("מה הסיסמה?").press("Enter")
        time.sleep(2)
        storage = context.storage_state()
        print(storage)
        time.sleep(1)
        page.pause()

        # page.get_by_role("button", name="כניסה").click()

        context.close()
        browser.close()
        browser.stop_tracing()

    except(Exception) as e:
            context.tracing.stop(path="trace.zip")
            raise e
from typing import Dict, List, Tuple
from playwright.sync_api import sync_playwright, Page, Browser


def launch_browser() -> Tuple[Browser, Page]:
    """
    Lanza un navegador Chromium en modo headless y devuelve (browser, page).
    """
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    return browser, page


def goto_url(page: Page, url: str) -> None:
    """
    Navega a la URL dada y espera a que la red esté relativamente ociosa.
    """
    page.goto(url, wait_until="networkidle", timeout=30000)


def get_page_snapshot(page: Page) -> Dict:
    """
    Devuelve un snapshot del estado actual de la página:
      - url
      - title
      - visible_text
      - clickable_elements: lista de {index, type, text}
    """
    url = page.url
    title = page.title()

    # Texto visible del body
    try:
        if page.locator("body").count() > 0:
            visible_text = page.inner_text("body")
        else:
            visible_text = ""
    except Exception:
        visible_text = ""

    clickable_elements: List[Dict] = []
    index = 0

    # Enlaces
    try:
        for locator in page.locator("a").all():
            try:
                text = locator.inner_text().strip()
                if text:
                    clickable_elements.append(
                        {"index": index, "type": "link", "text": text}
                    )
                    index += 1
            except Exception:
                continue
    except Exception:
        pass

    # Botones
    try:
        for locator in page.locator("button").all():
            try:
                text = locator.inner_text().strip()
                if text:
                    clickable_elements.append(
                        {"index": index, "type": "button", "text": text}
                    )
                    index += 1
            except Exception:
                continue
    except Exception:
        pass

    return {
        "url": url,
        "title": title,
        "visible_text": visible_text,
        "clickable_elements": clickable_elements,
    }


def click_element_by_index(page: Page, snapshot: Dict, target_index: int) -> None:
    """
    Intenta hacer clic en el elemento clicable cuyo índice coincide con target_index.
    Usa el texto guardado en el snapshot para localizarlo en la página.
    Si no lo encuentra, simplemente no hace nada.
    """
    clickable_elements = snapshot.get("clickable_elements", [])
    if not clickable_elements:
        return

    if target_index < 0 or target_index >= len(clickable_elements):
        return

    target_text = clickable_elements[target_index].get("text", "").strip()
    if not target_text:
        return

    # Recolectamos locators de enlaces y botones
    locators = []
    try:
        locators.extend(page.locator("a").all())
    except Exception:
        pass
    try:
        locators.extend(page.locator("button").all())
    except Exception:
        pass

    # Intentamos encontrar un elemento cuyo texto contenga el texto objetivo
    for loc in locators:
        try:
            txt = loc.inner_text().strip()
            if txt and target_text[:30] in txt:
                loc.click()
                return
        except Exception:
            continue


def scroll_down(page: Page) -> None:
    """
    Hace scroll hacia abajo para intentar cargar más contenido.
    """
    try:
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(1500)
    except Exception:
        pass


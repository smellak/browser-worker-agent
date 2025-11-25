from typing import Dict, List, Tuple
from playwright.sync_api import sync_playwright, Page, Browser, Playwright

def launch_browser() -> Tuple[Playwright, Browser, Page]:
    """Lanza el navegador y retorna playwright, browser y page"""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    return p, browser, page

def goto_url(page: Page, url: str) -> None:
    """Navega a una URL con manejo de errores"""
    try:
        page.goto(url, wait_until="networkidle", timeout=60000)
    except Exception:
        # Intenta con un timeout menos estricto si falla
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            # Si aún falla, intenta sin esperar
            page.goto(url, timeout=60000)

def get_page_snapshot(page: Page) -> Dict:
    """Obtiene un snapshot del estado actual de la página"""
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
    """Hace click en un elemento basándose en su índice del snapshot"""
    clickable_elements = snapshot.get("clickable_elements", [])
    if not clickable_elements:
        return
    if target_index < 0 or target_index >= len(clickable_elements):
        return
    
    target_text = clickable_elements[target_index].get("text", "").strip()
    if not target_text:
        return
    
    locators = []
    try:
        locators.extend(page.locator("a").all())
    except Exception:
        pass
    try:
        locators.extend(page.locator("button").all())
    except Exception:
        pass
    
    for loc in locators:
        try:
            txt = loc.inner_text().strip()
            if txt and target_text[:30] in txt:
                loc.click(timeout=10000)
                page.wait_for_load_state("domcontentloaded", timeout=10000)
                return
        except Exception:
            continue

def scroll_down(page: Page) -> None:
    """Hace scroll hacia abajo en la página"""
    try:
        page.mouse.wheel(0, 2000)
        page.wait_for_timeout(1500)
    except Exception:
        pass

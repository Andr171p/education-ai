import logging
import random

import html_to_markdown
from bs4 import BeautifulSoup
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

FINGERPRINT_SPOOFING_SCRIPT = """
() => {
    // Удаление webdriver property
    delete navigator.__proto__.webdriver;
    // Переопределение plugins
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
        configurable: true
    });
    // Переопределение languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['%s', '%s'],
        configurable: true
    });
    // Переопределение platform
    Object.defineProperty(navigator, 'platform', {
        get: () => '%s',
        configurable: true
    });
    // Переопределение hardwareConcurrency
    Object.defineProperty(navigator, 'hardwareConcurrency', {
        get: () => %d,
        configurable: true
    });
    // Скрытие automation properties
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    // Переопределение permissions
    const originalQuery = navigator.permissions.query;
    navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
    );
    // Маскировка под обычный браузер
    window.chrome = {
        runtime: {},
        loadTimes: function() { return {}; },
        csi: function() { return {}; },
        app: { isInstalled: false }
    };
}
"""

WEBGL_SPOOFING_SCRIPT = """
() => {
    const getParameter = WebGLRenderingContext.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
            return getParameter(parameter);
    };
}
"""

CANVAS_SPOOFING_SCRIPT = """
() => {
    // Canvas fingerprint spoofing
    const toDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        const context = this.getContext('2d');
        if (context) {
            context.fillText('Modified Canvas Fingerprint', 10, 10);
        }
        return toDataURL.call(this, type);
    };
}
"""

# Доступные версии chrome для настройки отпечатков браузера
CHROME_VERSIONS: tuple[str, ...] = (
    "120.0.0.0",
    "119.0.0.0",
    "118.0.0.0",
    "117.0.0.0",
    "116.0.0.0",
    "115.0.0.0",
    "114.0.0.0"
)
# Возможные устройства для создания правдоподобных отпечатков браузера
PLATFORMS: tuple[str, ...] = (
    "Windows NT 10.0; Win64; x64",
    "Windows NT 6.1; Win64; x64",
    "Macintosh; Intel Mac OS X 10_15_7",
    "X11; Linux x86_64",
)
# Человеко-подобные разрешения экранов
SCREEN_RESOLUTIONS: tuple[dict[str, int], ...] = (
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
)
# Доступные языки для браузера
LANGUAGES: tuple[str, ...] = (
    "en-US,en;q=0.9",
    "ru-RU,ru;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "fr-FR,fr;q=0.9,en;q=0.8",
)


def generate_user_agent() -> str:
    """Генерирует пользователя-подробный User-agent заголовки

    :return Сгенерированный User-agent
    """
    return (
        f"Mozilla/5.0 ({random.choice(PLATFORMS)}) AppleWebKit/537.36 "  # noqa: S311
        f"(KHTML, like Gecko) Chrome/{random.choice(CHROME_VERSIONS)} Safari/537.36"  # noqa: S311
    )


def generate_screen_resolution() -> dict[str, int]:
    """Генерирует реалистичного разрешения экрана

    :return Разрешение экрана в формате width и height
    """
    return random.choice(SCREEN_RESOLUTIONS)  # noqa: S311


def generate_accept_language() -> str:
    return random.choice(LANGUAGES)  # noqa: S311


def generate_extra_http_headers() -> dict[str, str]:
    """Генерирует дополнительные заголовки

    :return сгенерированные заголовки
    """
    return {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",  # noqa: E501
        "Accept-Language": generate_accept_language(),
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "DNT": str(random.randint(0, 1)),  # noqa: S311
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }


SCRIPTS: tuple[str, ...] = (
    CANVAS_SPOOFING_SCRIPT,
    FINGERPRINT_SPOOFING_SCRIPT
    % (
        "ru-RU", "ru", random.choice(PLATFORMS), random.choice([4, 8, 12, 16])  # noqa: S311
    ),
    WEBGL_SPOOFING_SCRIPT,
)


async def _create_new_stealth_context(browser: Browser) -> BrowserContext:
    """Создаёт новый контекст для браузера с анти-детекцией ботов.

    :param browser: Текущий асинхронный playwright браузер.
    :return Новый сконфигурированный контекст.
    """
    screen_resolution = generate_screen_resolution()
    context = await browser.new_context(
        viewport=screen_resolution,
        screen=screen_resolution,
        user_agent=generate_user_agent(),
        accept_downloads=False,
        ignore_https_errors=True,
        java_script_enabled=True,
        has_touch=random.choice([True, False]),  # noqa: S311
        is_mobile=False,
        extra_http_headers=generate_extra_http_headers(),
    )
    for script in SCRIPTS:
        await context.add_init_script(script)
    return context


async def _get_current_page(browser: Browser) -> Page:
    """Получает текущую страницу в браузере.

    :param browser: Playwright браузер.
    :return Текущая страница.
    """
    if not browser.contexts:
        context = await _create_new_stealth_context(browser)
        return await context.new_page()
    context = browser.contexts[0]
    if not context.pages:
        return await context.new_page()
    return context.pages[-1]


def _extract_markdown_text(soup: BeautifulSoup) -> str:
    """Извлечение текста со страницы в формате Markdown"""

    for element in soup.find_all({
        "script", "style", "svg", "path", "meta", "link", "nav", "footer", "header"
    }):
        element.decompose()
    body = soup.find("body")
    if body is None:
        return ""
    # Основные семантические элементы в порядке важности
    elements = body.find_all({"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th"})
    return "\n".join([html_to_markdown.convert(str(element)) for element in elements])


async def crawl_web_page(url: str, headless: bool = False) -> str:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        page = await _get_current_page(browser)
        await page.goto(url)
        try:
            await page.wait_for_load_state("networkidle", timeout=5_000)
        except PlaywrightTimeoutError:
            # Fallback в случае неудачного ожидания загрузки страницы
            logger.warning("Networkidle timeout for %s, using domcontentloaded", page.url)
            await page.wait_for_load_state("domcontentloaded")
        page_content = await page.content()
        soup = BeautifulSoup(page_content, "html.parser")
        return _extract_markdown_text(soup)

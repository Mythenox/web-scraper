from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import requests
import asyncio, aiohttp
from typing import TypedDict


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


class AsyncCrawler:
    def __init__(
            self,
            base_url: str,
            base_domain: str,
            page_data: dict[str, PageData],
            max_concurrency: int
    ) -> None:
        self.base_url = base_url
        self.base_domain = base_domain
        self.page_data = page_data
        self.lock = asyncio.Lock()
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrency)
        self.session = aiohttp.ClientSession()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            return normalized_url in self.page_data
        
    async def get_html(self, url: str) -> str:
        async with self.session:
            r = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
            content_header: str | None = r.headers.get('content-type')
            if r.status_code >= 400:
                r.raise_for_status()
            elif content_header is None or 'text/html' not in content_header:
                raise Exception("invalid content type")
            return r.text
    
    async def crawl(
            self,
            base_url: str,
            current_url: str | None = None,
            page_data: dict[str, PageData] | None = None
    ) -> dict[str, PageData]:
        if current_url is None:
            current_url = base_url
        if page_data is None:
            page_data = {}

        base_url_obj = urlparse(base_url)
        current_url_obj = urlparse(current_url)
        if base_url_obj.netloc != current_url_obj.netloc:
            return page_data
        
        normalized_url = normalize_url(current_url)
        if not await self.add_page_visit(normalized_url):
            return page_data
        
        print(f"crawling {normalized_url}")
        current_page_html: str | None = safe_get_html(current_url)
        if current_page_html is None:
            return page_data
        
        async with self.semaphore:
            page_data[normalized_url] = extract_page_data(current_page_html, current_url)
            next_urls: list[str] = page_data[normalized_url]["outgoing_links"]
            tasks = []
            for next_url in next_urls:
                task = asyncio.create_task(self.crawl(base_url, next_url, page_data))
                tasks.append(task)
            await asyncio.gather(*tasks)
            return page_data
    
    
    async def crawl_page(
            self,
            base_url: str
    ):
        return self.crawl(base_url)

async def crawl_site_async():
    pass

def normalize_url(url: str) -> str:
    prefix_split: list[str] = url.split("//", maxsplit=1)
    if len(prefix_split) == 2:
        no_prefix: str = prefix_split[-1]
    else:
        # if len != 2, then len == 1.
        no_prefix: str = prefix_split[0]
    if no_prefix[-1] == "/":
        return no_prefix[:-1]
    return no_prefix


def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    h_tag = soup.find("h1")
    if isinstance(h_tag, Tag):
        return h_tag.get_text(strip=True)
    h_tag = soup.find("h2")
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""


def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    if isinstance(soup.main, Tag):
        p_tag: Tag | None = soup.main.p
        if isinstance(p_tag, Tag):
            return p_tag.get_text(strip=True)
    p_tag: Tag | None = soup.p 
    return p_tag.get_text(strip=True) if isinstance(p_tag, Tag) else ""


def get_urls_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    links = soup.find_all('a')
    full_links = []
    for link in links:
        if isinstance(link, Tag):
            url = link.get('href')
            if isinstance(url, str):
                full_links.append(urljoin(base_url, url))
            else:
                raise Exception("missing href attribute")
        else:
            raise Exception("link borked")
    return full_links


def get_images_from_html(html, base_url) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    images = soup.find_all('img')
    image_links = []
    for image in images:
        if isinstance(image, Tag):
            url = image.get('src')
            if isinstance(url, str):
                image_links.append(urljoin(base_url, url))
            else:
                raise Exception("missing src attribute")
        else:
            raise Exception("image borked")
    return image_links


def extract_page_data(html: str, page_url: str) -> PageData:
    page_data = PageData(
        url = normalize_url(page_url),
        heading = get_heading_from_html(html),
        first_paragraph = get_first_paragraph_from_html(html),
        outgoing_links = get_urls_from_html(html, page_url),
        image_urls = get_images_from_html(html, page_url)
    )
    return page_data


def get_html(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
    content_header: str | None = r.headers.get('content-type')
    if r.status_code >= 400:
        r.raise_for_status()
    elif content_header is None or 'text/html' not in content_header:
        raise Exception("invalid content type")
    return r.text


def safe_get_html(url: str) -> str | None:
    try:
        return get_html(url)
    except Exception as e:
        print(f"{e}")
        return None
    

def crawl_page(
        base_url: str,
        current_url: str | None = None,
        page_data: dict[str, PageData] | None = None
) -> dict[str, PageData]:
    if current_url is None:
        current_url = base_url
    if page_data is None:
        page_data = {}

    base_url_obj = urlparse(base_url)
    current_url_obj = urlparse(current_url)
    if base_url_obj.netloc != current_url_obj.netloc:
        return page_data
    
    normalized_url = normalize_url(current_url)
    if normalized_url in page_data:
        return page_data
    
    print(f"crawling {normalized_url}")
    current_page_html: str | None = safe_get_html(current_url)
    if current_page_html is None:
        return page_data
    
    page_data[normalized_url] = extract_page_data(current_page_html, current_url)

    next_urls: list[str] = page_data[normalized_url]["outgoing_links"]
    for next_url in next_urls:
        crawl_page(base_url, next_url, page_data)
    return page_data
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from typing import TypedDict


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


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
        url = page_url,
        heading = get_heading_from_html(html),
        first_paragraph = get_first_paragraph_from_html(html),
        outgoing_links = get_urls_from_html(html, page_url),
        image_urls = get_images_from_html(html, page_url)
    )
    return page_data
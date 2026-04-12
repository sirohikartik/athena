from scrape import __static__, __dynamic__
import asyncio
from typing import List
import trafilatura

def html_to_text(html):
    return trafilatura.extract(html)

dynamic_semaphore = asyncio.Semaphore(2)


async def process_url(url: str) -> str:
    try:

        html, status = await asyncio.to_thread(__static__, url)


        if status != 200 or not html or "cloudflare" in html.lower():
            async with dynamic_semaphore:
                html = await asyncio.to_thread(__dynamic__, url)

        text = html_to_text(html)
        return text if text else ""

    except Exception:
        return ""


async def run_async(urls: List[str]) -> List[str]:
    tasks = [process_url(url) for url in urls]
    return await asyncio.gather(*tasks)


def run(urls: List[str]) -> List[str]:
    return asyncio.run(run_async(urls))

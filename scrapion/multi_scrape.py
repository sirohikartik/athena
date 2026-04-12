from scrapion import scrape
import asyncio
from typing import List
import trafilatura

def html_to_text(html):
    return trafilatura.extract(html)


dynamic_semaphore = asyncio.Semaphore(2)


global_semaphore = asyncio.Semaphore(10)


async def process_url(url: str) -> str:
    async with global_semaphore:
        try:

            try:
                html, status = await asyncio.wait_for(
                    asyncio.to_thread(scrape.__static__, url),
                    timeout=8
                )
            except asyncio.TimeoutError:
                html, status = "", 0


            if status != 200 or not html or "cloudflare" in html.lower():
                async with dynamic_semaphore:
                    try:
                        html = await asyncio.wait_for(
                            asyncio.to_thread(scrape.__dynamic__, url),
                            timeout=15
                        )
                    except asyncio.TimeoutError:
                        return ""

            text = html_to_text(html)
            return text if text else ""

        except Exception:
            return ""


async def run_async(urls: List[str]) -> List[str]:
    tasks = [process_url(url) for url in urls]
    results = await asyncio.gather(*tasks)


    return [r for r in results if r]


def run(urls: List[str]) -> List[str]:
    return asyncio.run(run_async(urls))

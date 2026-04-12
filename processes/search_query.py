import asyncio
from scrapion import multi_scrape
from seeker import search



async def find(query: str):
    responses = await asyncio.to_thread(search.search, query)

    urls = [i["url"] for i in responses]

    results = await multi_scrape.run_async(urls)

    return (results,urls)

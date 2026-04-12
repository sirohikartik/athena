from scrapion import multi_scrape
from seeker import search
from agents import summarizer

def find(query : str):
   responses = search.search(query)
   responses = [i["url"] for i in responses]
   results = multi_scrape.run(responses)
   # for i in results:
   #     i = summarizer.summarize(i)
   return results

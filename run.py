import time
from scrapion import scrape
from scrapion import render


def time_only(func, url):
    start = time.perf_counter()
    func(url)
    end = time.perf_counter()
    print(f"{func.__name__} took {end - start:.4f} sec")


url = "https://medium.com/javarevisited/40-must-read-engineering-blogs-to-learn-system-design-and-software-architecture-in-2024-aaa7c4f71ee6"

url = "https://medium.com/@brennanbrown/thats-home-that-s-us-0d7ce6bc190b"
url = "https://github.com/sirohikartik/tinygpt"

time_only(scrape.__static__, url)
time_only(scrape.__dynamic__, url)

print(render.html_to_text(scrape.__static__(url)[0]))
print(len(scrape.__dynamic__(url)))

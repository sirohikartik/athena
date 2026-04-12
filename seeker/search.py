from ddgs import DDGS

def search(query, max_results=10):
    try:
        results = DDGS().text(query, max_results=max_results)

        return [
            {
                "title": r.get("title"),
                "url": r.get("href"),
                "content": r.get("body")
            }
            for r in results
        ]

    except Exception as e:
        print("DuckDuckGo failed:", e)
        return []


if __name__ == "__main__":
    results = search("machine learning")

    for r in results[:5]:
        print(f"{r['title']} -> {r['url']}")

Athena is an open-source search agent that combines web search, intelligent scraping, BM25 retrieval, and local LLM reasoning to answer user questions with up-to-date information from the web. Unlike traditional search engines that return lists of links, Athena reads and understands web content to provide direct, well-sourced answers to your questions.


## Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- At least one LLM model pulled (e.g., `gpt-oss:20b-cloud`)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd athena
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Pull an LLM model using Ollama:
   ```bash
   ollama pull gpt-oss:20b-cloud
   ```

4. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

## Usage

Run the application:
```bash
python run.py
```

Enter your question when prompted. Athena will:
1. Use an LLM to break your query into 3-5 diverse search terms
2. Search DuckDuckGo for all queries in parallel
3. Scrape and extract content from the top pages
4. Index all content using a BM25 corpus
5. Retrieve the most relevant information based on your original query
6. Generate an answer using the local LLM
7. Display the response with source attribution
8. Save the query to history

To exit, press `Ctrl+C`. Your conversation history will be saved automatically.

### Example Interaction

```
Ask Athena: What are the latest developments in quantum computing 2024?

[cyan]Analyzing query and generating search terms...[/cyan]
[dim]Queries: quantum computing breakthroughs 2024, latest quantum processor news, etc...[/dim]
[cyan]Searching...[/cyan]

[bold green]Athena:[/bold green]
Quantum computing has seen significant advances in 2024, including...
[answer continues...]

[bold yellow]Sources:[/bold yellow]
1. https://example.com/quantum-computing-2024
2. https://example.org/quantum-news
3. https://example.net/research-updates
```

## How It Works

### Search Phase
1. **Query Expansion**: An LLM agent analyzes the user query and generates 3-5 specialized search queries to ensure comprehensive coverage.
2. **Parallel Search**: All generated queries are processed concurrently using `asyncio`, retrieving results from DuckDuckGo.

### Scraping Phase
2. For each URL:
   - First attempts static scraping using `requests` with proper headers
   - If static scraping fails (non-200 status, Cloudflare protection, etc.):
     - Falls back to dynamic scraping using Selenium in headless mode
   - Uses semaphores to limit concurrent requests (10 global, 2 dynamic)
   - Implements timeouts to prevent hanging requests

### Content Processing
3. HTML content is converted to clean text using Trafilatura
4. Text is split into overlapping chunks (300 words each)
5. A BM25 (Best Matching 25) index is built from all retrieved chunks, providing efficient keyword-based retrieval without the need for heavy embedding models.

### Retrieval & Generation
7. The original user query is used to retrieve the top 5 most relevant text chunks from the BM25 index
8. Context + question + system prompt are formatted for the LLM
9. Ollama generates a response using `gpt-oss:20b-cloud`
10. Response is streamed back to the user in real-time
11. Sources are deduplicated and displayed (top 5 unique URLs)

### Conversation History
- Each query and timestamp is stored in `History/history.json`
- History is loaded on startup and saved on exit

## Configuration

### Model Selection
To change the LLM model, modify:
- In `agent.py`: Change the `model_name` default in `agent()`
- In `run.py`: Change the `model_name` default in `generate_search_queries()` and the `agent()` call in `main()`

### Search Parameters
Adjust these values in the code:
- `max_results` in `seeker/search.py` (default: 10)
- `k` in `run.py` retrieve_bm25 function (default: 5 chunks)
- `chunk_size` in `run.py` (default: 300 words)

### Timeouts & Limits
- Static scrape timeout: 8 seconds
- Dynamic scrape timeout: 15 seconds
- Global concurrency limit: 10 URLs
- Dynamic concurrency limit: 2 URLs

## Dependencies

Key dependencies include:
- `ddgs`: DuckDuckGo search
- `requests` & `selenium`: Web scraping
- `trafilatura`: HTML-to-text conversion
- `rank-bm25`: Probabilistic information retrieval
- `ollama`: LLM interface
- `rich`: Beautiful terminal output

See `requirements.txt` for the complete list.

## Customization

### Adding New Search Engines
Modify `seeker/search.py` to use different search APIs (Google, Bing, etc.) while maintaining the same return format.

### Changing Scraping Behavior
Adjust `scrapion/scrape.py` to:
- Add more headers or cookies
- Implement different waiting strategies for dynamic content
- Add proxy support

### Switching LLM Providers
Modify `utils/model.py` to work with different LLM APIs (OpenAI, Anthropic, etc.) while keeping the same interface.

## Data Privacy

Athena is designed for privacy:
- All processing happens locally on your machine
- No data is sent to external APIs (except for the initial web search)
- LLMs run locally via Ollama
- History is stored only on your local machine
- Scraped content is processed in memory and not persisted

## Troubleshooting

### Common Issues

1. **"No results found"**
   - Check your internet connection
   - Try a different query
   - Verify DuckDuckGo is accessible

2. **"No usable content extracted"**
   - The search results may be from sites that block scraping
   - Try a query likely to return text-heavy results (news, Wikipedia, etc.)

3. **Model loading errors**
   - Ensure Ollama is running: `ollama serve`
   - Verify the model is pulled: `ollama list`
   - Check if you have enough RAM/VRAM for the model

4. **Selenium issues**
   - Ensure Chrome/Chromium is installed
   - Try updating selenium and webdriver-manager

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built with [Ollama](https://ollama.ai/) for local LLM inference
- Retrieval powered by [rank-bm25](https://github.com/dorianpatras/rank_bm25)
- Scraping powered by [requests](https://requests.readthedocs.io/) and [Selenium](https://www.selenium.dev/)
- Content extraction via [trafilatura](https://github.com/adbar/trafilatura)
- Search via [DuckDuckGo Instant Answer API](https://duckduckgo.com/html/)
- Terminal UI enhanced by [Rich](https://rich.readthedocs.io/)

---

Start exploring the web with Athena - your private, intelligent search agent! 🚀

Athena is an open-source search agent that combines web search, intelligent scraping, semantic retrieval, and local LLM reasoning to answer user questions with up-to-date information from the web. Unlike traditional search engines that return lists of links, Athena reads and understands web content to provide direct, well-sourced answers to your questions.


## Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- At least one LLM model pulled (e.g., `gemma3:1b` or `llama3:1b`)

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
   ollama pull gemma3:1b
   # or
   ollama pull llama3:1b
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

You'll see:
```
Initializing sentencepiece...
Ask Athena: 
```

Enter your question when prompted. Athena will:
1. Search DuckDuckGo for relevant results
2. Scrape and extract content from the top pages
3. Find the most relevant information using semantic search
4. Generate an answer using the local LLM
5. Display the response with source attribution
6. Save the query to history

To exit, press `Ctrl+C`. Your conversation history will be saved automatically.

### Example Interaction

```
Ask Athena: What are the latest developments in quantum computing 2024?

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
1. Uses DuckDuckGo (`ddgs` library) to search for the user query
2. Returns top results with URLs, titles, and snippets

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
5. Sentence-transformers (`all-MiniLM-L6-v2`) creates embeddings for all chunks
6. FAISS index is built for efficient similarity search

### Retrieval & Generation
7. The user query is embedded and used to search the FAISS index
8. Top 3 most relevant text chunks are retrieved as context
9. Context + question + system prompt are formatted for the LLM
10. Ollama generates a response using the specified model
11. Response is streamed back to the user in real-time
12. Sources are deduplicated and displayed (top 5 unique URLs)

### Conversation History
- Each query and timestamp is stored in `History/history.json`
- History is loaded on startup and saved on exit
- Currently, history is not used in the LLM prompt but is available for future enhancement

## Configuration

### Model Selection
To change the LLM model, modify these files:
- In `agent.py`: Change the `model_name` parameter in the `agent()` function call
- In `run.py`: Change the model name in the `agent()` call (currently "gemma3:1b")

### Search Parameters
Adjust these values in the code:
- `max_results` in `seeker/search.py` (default: 10)
- `k` in `run.py` retrieve function (default: 3 chunks)
- `chunk_size` in `run.py` (default: 300 words)

### Timeouts & Limits
- Static scrape timeout: 8 seconds
- Dynamic scrape timeout: 15 seconds
- Global concurrency limit: 10 URLs
- Dynamic concurrency limit: 2 URLs (to reduce strain on Selenium)

## Dependencies

Key dependencies include:
- `ddgs`: DuckDuckGo search
- `requests` & `selenium`: Web scraping
- `trafilatura`: HTML-to-text conversion
- `sentence-transformers` & `torch`: Text embeddings
- `faiss-cpu`: Vector similarity search
- `ollama`: LLM interface
- `rich`: Beautiful terminal output
- `numpy`: Numerical operations

See `requirements.txt` for the complete list.

## Customization

### Adding New Search Engines
Modify `seeker/search.py` to use different search APIs (Google, Bing, etc.) while maintaining the same return format.

### Changing Scraping Behavior
Adjust `scrapion/scrape.py` to:
- Add more headers or cookies
- Implement different waiting strategies for dynamic content
- Add proxy support

### Using Different Embedding Models
Change the model in `run.py`:
```python
embed_model = SentenceTransformer("your-model-name")
```

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

5. **CUDA/GPU issues with sentence-transformers**
   - The package uses CPU by default
   - For GPU support, install appropriate PyTorch with CUDA

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built with [Ollama](https://ollama.ai/) for local LLM inference
- Uses [sentence-transformers](https://www.sbert.net/) for embeddings
- Powered by [FAISS](https://github.com/facebookresearch/faiss) for vector search
- Scraping powered by [requests](https://requests.readthedocs.io/) and [Selenium](https://www.selenium.dev/)
- Content extraction via [trafilatura](https://github.com/adbar/trafilatura)
- Search via [DuckDuckGo Instant Answer API](https://duckduckgo.com/html/)
- Terminal UI enhanced by [Rich](https://rich.readthedocs.io/)

---

Start exploring the web with Athena - your private, intelligent search agent! 🚀

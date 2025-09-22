# AI Research Agent

A powerful research agent that combines Ollama/Llama 3 with web search capabilities to generate comprehensive research briefs. The agent automatically plans research tasks, searches the web, and synthesizes findings into structured reports.

## Features

- **Intelligent Task Planning**: Breaks down complex queries into specific research tasks
- **Web Search Integration**: Uses Google Custom Search API for reliable results
- **AI-Powered Analysis**: Leverages Ollama/Llama 3 for content synthesis
- **Structured Output**: Generates professional research briefs with references
- **Clean UI**: Modern Gradio interface with real-time progress tracking
- **Fallback Support**: Works with LLM-only knowledge when web search unavailable

## Quick Start

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- Google Custom Search API credentials (optional but recommended)

### Installation

1. **Install Ollama and Llama 3**
   ```
   # Pull Llama 3 model
   
   ollama pull llama3
   
   # Start Ollama server
   ollama serve
   ```

3. **Install Requirements**

   # Install dependencies
   ```
   pip install gradio requests aiohttp
   ```

4. **Run the Application**
   ```bash
   python research_agent.py
   ```

5. **Access the Interface**
   - Open your browser to `http://localhost:7860`
   - Enter your research query and start researching!

## Configuration

### Google Custom Search API Setup (Recommended)

For best results, configure Google Custom Search API:

1. **Get API Key:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create/select a project
   - Enable "Custom Search API"
   - Create API credentials → API Key

2. **Create Search Engine:**
   - Visit [Google Programmable Search](https://programmablesearchengine.google.com/)
   - Create new search engine
   - Set "Sites to search" to `*` (entire web)
   - Copy the Search Engine ID (CX)

3. **Configure in App:**
   - Use the configuration section in the web interface, OR
   - Edit the code and replace:
     ```python
     GOOGLE_API_KEY = "your_api_key_here"
     GOOGLE_CX = "your_cx_id_here"
     ```

### API Usage Limits
- **Free Tier**: 100 searches/day
- **Paid**: $5 per 1,000 additional searches

##  Usage

### Example Queries

```
Climate change effects on agriculture
Artificial intelligence in healthcare  
Renewable energy trends 2024
Quantum computing applications
Cryptocurrency market analysis
```

### Research Process

1. **Planning**: Agent breaks your query into 3-5 research tasks
2. **Searching**: Executes web searches for each task
3. **Analysis**: Uses Llama 3 to synthesize findings
4. **Output**: Generates structured brief with executive summary

### Sample Output

```
Research Brief: Renewable energy trends
Generated: 2024-01-20 15:30:45

EXECUTIVE SUMMARY
[AI-generated summary of key findings]

RESEARCH TASKS EXECUTED
1. General renewable energy market overview
2. Recent technology developments
3. Policy and regulatory changes

KEY FINDINGS
[Detailed findings for each research task]

REFERENCES
[Web sources and citations]
```

## Architecture

- **Frontend**: Gradio web interface
- **LLM Backend**: Ollama with Llama 3
- **Search**: Google Custom Search API
- **Processing**: Async Python with aiohttp

## Requirements

```
gradio>=4.0.0
requests>=2.31.0
aiohttp>=3.8.0
```

## Troubleshooting

### Common Issues

**Ollama Connection Failed**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve
```

**Search Not Working**
- Verify Google API credentials
- Check API quota limits
- Agent falls back to LLM knowledge if search fails

**Timeout Errors**
- Large queries may take time to process
- Timeouts are set to 120 seconds
- Try shorter, more specific queries


## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Star this repo if you find it useful!**

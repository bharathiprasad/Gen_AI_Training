import gradio as gr
import requests
import json
import re
from typing import List, Dict, Any
from datetime import datetime
import asyncio
import aiohttp
from urllib.parse import quote

class ResearchAgent:
    def __init__(self, ollama_host="http://localhost:11434", google_api_key=None, google_cx=None):
        self.ollama_host = ollama_host
        self.model = "llama3"
        self.google_api_key = google_api_key
        self.google_cx = google_cx
        
    async def call_ollama(self, prompt: str, system_prompt: str = "") -> str:
        """Call Ollama API"""
        try:
            url = f"{self.ollama_host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return f"Error calling Ollama: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def web_search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Web search using Google Custom Search API"""
        if not self.google_api_key or not self.google_cx:
            return self._fallback_search_results(query)
        
        try:
            # Google Custom Search API
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': query,
                'num': min(num_results, 10)  # Max 10 per request
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get('items', []):
                            results.append({
                                "title": item.get('title', 'No title'),
                                "snippet": item.get('snippet', 'No description available'),
                                "url": item.get('link', ''),
                                "source": item.get('displayLink', 'Unknown source')
                            })
                        
                        return results
                    else:
                        print(f"Google Search API error: {response.status}")
                        return self._fallback_search_results(query)
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return self._fallback_search_results(query)
    
    def _fallback_search_results(self, query: str) -> List[Dict[str, str]]:
        """Fallback when web search fails - use LLM knowledge"""
        return [
            {
                "title": f"Knowledge about {query}",
                "snippet": f"Based on training data, here's what we know about {query}",
                "url": "llm://internal-knowledge",
                "source": "LLM Knowledge Base"
            }
        ]
    
    def plan_research_tasks(self, query: str) -> List[str]:
        """Plan research tasks based on the query"""
        planning_prompt = f"""
Given this research query: "{query}"

Break this down into 3-5 specific research tasks that would help answer this question comprehensively.
Each task should be a specific search query or investigation.

Format your response as a simple list, one task per line:
Task 1: [specific search query]
Task 2: [specific search query]
Task 3: [specific search query]
etc.

Keep tasks focused and searchable.
"""
        
        try:
            response = requests.post(f"{self.ollama_host}/api/generate", 
                                   json={"model": self.model, "prompt": planning_prompt, "stream": False},
                                   timeout=120)
            
            if response.status_code == 200:
                plan_text = response.json()["response"]
                # Extract tasks from the response
                tasks = []
                for line in plan_text.split('\n'):
                    if line.strip() and ('Task' in line or line.strip().startswith(('-', '•', '1.', '2.', '3.', '4.', '5.'))):
                        # Clean up the task text
                        task = re.sub(r'^Task \d+:\s*', '', line.strip())
                        task = re.sub(r'^\d+\.\s*', '', task.strip())
                        task = re.sub(r'^[-•]\s*', '', task.strip())
                        if task:
                            tasks.append(task)
                
                return tasks[:5]  # Limit to 5 tasks
            else:
                # Fallback tasks
                return [f"General information about {query}", f"Recent developments in {query}", f"Expert opinions on {query}"]
                
        except Exception as e:
            # Fallback tasks
            return [f"General information about {query}", f"Recent developments in {query}", f"Expert opinions on {query}"]
    
    async def execute_research(self, query: str) -> Dict[str, Any]:
        """Execute the full research process"""
        results = {
            "original_query": query,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tasks": [],
            "findings": [],
            "references": [],
            "summary": ""
        }
        
        # Step 1: Plan research tasks
        tasks = self.plan_research_tasks(query)
        results["tasks"] = tasks
        
        # Step 2: Execute each task
        all_search_results = []
        for i, task in enumerate(tasks):
            search_results = await self.web_search(task, num_results=3)
            task_info = {
                "task": task,
                "results": search_results
            }
            results["findings"].append(task_info)
            all_search_results.extend(search_results)
        
        # Step 3: Collect unique references
        unique_refs = {}
        for result in all_search_results:
            if result["url"] and result["url"] not in unique_refs:
                unique_refs[result["url"]] = {
                    "title": result["title"],
                    "url": result["url"],
                    "source": result["source"]
                }
        results["references"] = list(unique_refs.values())
        
        # Step 4: Generate summary
        summary_prompt = f"""
Based on the following research findings for the query "{query}", write a comprehensive but concise summary:

Research Tasks and Findings:
"""
        for finding in results["findings"]:
            summary_prompt += f"\nTask: {finding['task']}\n"
            for result in finding["results"]:
                summary_prompt += f"- {result['snippet'][:200]}...\n"
        
        summary_prompt += """
Please provide:
1. A clear, comprehensive summary of the key findings
2. Important insights or conclusions
3. Any limitations or areas needing further research

Keep the summary well-structured and informative.
"""
        
        try:
            response = requests.post(f"{self.ollama_host}/api/generate",
                                   json={"model": self.model, "prompt": summary_prompt, "stream": False},
                                   timeout=120)
            
            if response.status_code == 200:
                results["summary"] = response.json()["response"]
            else:
                results["summary"] = "Summary generation failed."
        except Exception as e:
            results["summary"] = f"Error generating summary: {str(e)}"
        
        return results
    
    def format_research_brief(self, results: Dict[str, Any]) -> str:
        """Format results into a structured research brief"""
        brief = f"Research Brief: {results['original_query']}\n"
        brief += f"Generated: {results['timestamp']}\n\n"
        
        brief += "EXECUTIVE SUMMARY\n"
        brief += f"{results['summary']}\n\n"
        
        brief += "RESEARCH TASKS EXECUTED\n"
        for i, task in enumerate(results['tasks'], 1):
            brief += f"{i}. {task}\n"
        
        brief += "\nKEY FINDINGS\n"
        for i, finding in enumerate(results['findings'], 1):
            brief += f"\nTask {i}: {finding['task']}\n"
            for result in finding['results']:
                if result['snippet']:
                    brief += f"- {result['snippet'][:300]}{'...' if len(result['snippet']) > 300 else ''}\n"
        
        brief += "\nREFERENCES\n"
        for i, ref in enumerate(results['references'], 1):
            brief += f"{i}. {ref['title']} - {ref['url']} ({ref['source']})\n"
        
        brief += f"\nResearch completed with {len(results['tasks'])} tasks and {len(results['references'])} references"
        
        return brief

# Global agent instance - Add your Google API credentials here
GOOGLE_API_KEY = "Add_your_own_api_key"  # Get from Google Cloud Console
GOOGLE_CX = "add_cx_id"        # Get from Google Programmable Search Engine

agent = ResearchAgent(google_api_key=GOOGLE_API_KEY, google_cx=GOOGLE_CX)

async def research_query(query: str, progress=gr.Progress()):
    """Main research function for Gradio interface"""
    if not query.strip():
        return "Please enter a research query."
    
    progress(0.1, desc="Planning research tasks...")
    
    try:
        # Test Ollama connection
        test_response = requests.get(f"{agent.ollama_host}/api/tags", timeout=5)
        if test_response.status_code != 200:
            return "Error: Cannot connect to Ollama. Please ensure Ollama is running on localhost:11434"
    except:
        return "Error: Cannot connect to Ollama. Please ensure Ollama is running on localhost:11434"
    
    progress(0.2, desc="Executing research...")
    
    
    results = await agent.execute_research(query)
    
    progress(0.9, desc="Formatting results...")
    

    brief = agent.format_research_brief(results)
    
    progress(1.0, desc="Complete!")
    
    return brief

def create_interface():
    """Create Gradio interface"""
    with gr.Blocks(title="AI Research Agent", theme=gr.themes.Soft()) as interface:
        gr.HTML("<h1>AI Research Agent</h1>")
        
        with gr.Accordion("API Configuration", open=False):
            with gr.Row():
                api_key_input = gr.Textbox(
                    label="Google API Key", 
                    type="password",
                    placeholder="Enter your Google Custom Search API key"
                )
                cx_input = gr.Textbox(
                    label="Google CX ID", 
                    placeholder="Enter your Custom Search Engine ID"
                )
                update_btn = gr.Button("Update API Keys", size="sm")
        
        def update_api_keys(api_key, cx_id):
            global agent
            agent = ResearchAgent(google_api_key=api_key, google_cx=cx_id)
            return "API keys updated successfully!"
        
        update_btn.click(
            fn=update_api_keys,
            inputs=[api_key_input, cx_input],
            outputs=gr.Textbox(visible=False)
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                query_input = gr.Textbox(
                    label="Research Query",
                    placeholder="Enter your research question",
                    lines=2
                )
                
                research_btn = gr.Button("Start Research", variant="primary", size="lg")

            
            with gr.Column(scale=3):
                output = gr.Textbox(
                    label="Research Brief",
                    value="Research results will appear here...",
                    lines=30,
                    max_lines=50
                )
        
        # Event handlers
        research_btn.click(
            fn=research_query,
            inputs=[query_input],
            outputs=[output],
            show_progress=True
        )
        
        query_input.submit(
            fn=research_query,
            inputs=[query_input],
            outputs=[output],
            show_progress=True
        )

    
    return interface

if __name__ == "__main__":
    # Check if running in async context
    import sys
    
    def sync_research_query(query: str):
        """Synchronous wrapper for Gradio"""
        if not query.strip():
            return "Please enter a research query."
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.execute_research(query))
            brief = agent.format_research_brief(result)
            return brief
        finally:
            loop.close()
    
    # Update the interface to use sync function
    with gr.Blocks(title="AI Research Agent", theme=gr.themes.Soft()) as interface:
        gr.HTML("<h1>🔍 AI Research Agent</h1>")
        
        with gr.Row():
            with gr.Column(scale=2):
                query_input = gr.Textbox(
                    label="Research Query",
                    placeholder="Enter your research question",
                    lines=2
                )
                
                research_btn = gr.Button("🔍 Start Research", variant="primary", size="lg")

            
            with gr.Column(scale=3):
                output = gr.Textbox(
                    label="Research Brief",
                    value="Research results will appear here...",
                    lines=30,
                    max_lines=50
                )
        
        # Event handlers
        research_btn.click(
            fn=sync_research_query,
            inputs=[query_input],
            outputs=[output]
        )
        
        query_input.submit(
            fn=sync_research_query,
            inputs=[query_input], 
            outputs=[output]
        )

    
    # Launch the interface
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
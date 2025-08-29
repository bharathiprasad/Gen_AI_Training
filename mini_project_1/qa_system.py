import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
import requests


class PromptLibrary:
    """Configurable prompt templates for different Q&A scenarios"""
    
    def __init__(self, config_path: str = "prompts.json"):
        self.config_path = config_path
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates from config file"""
        default_prompts = {
            "qa": """Based on the following document, answer the question accurately and concisely.

Document:
{document}

Question: {question}

Answer:""",
            
            "summary": """Summarize the following document in a clear and concise manner:

Document:
{document}

Summary:""",
            
            "explain": """Explain the following concept from the document in simple terms:

Document:
{document}

Concept to explain: {question}

Explanation:"""
        }
        
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    loaded_prompts = json.load(f)
                    default_prompts.update(loaded_prompts)
        except Exception as e:
            print(f"Warning: Could not load prompts config: {e}")
        
        return default_prompts
    
    def get_prompt(self, prompt_type: str = "qa") -> str:
        """Get a prompt template by type"""
        return self.prompts.get(prompt_type, self.prompts["qa"])
    
    def save_prompts(self):
        """Save current prompts to config file"""
        with open(self.config_path, 'w') as f:
            json.dump(self.prompts, f, indent=2)


class OllamaQA:
    """Q&A system using Ollama local LLM"""
    
    def __init__(self, model: str = "llama3", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.prompt_lib = PromptLibrary()
    
    def _call_ollama(self, prompt: str) -> str:
        """Make API call to Ollama"""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            return f"Error calling Ollama: {e}"
    
    def load_document(self, file_path: str) -> str:
        """Load document content from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise Exception(f"Error loading document: {e}")
    
    def ask_question(self, document: str, question: str, prompt_type: str = "qa") -> str:
        """Ask a question about the document"""
        prompt_template = self.prompt_lib.get_prompt(prompt_type)
        prompt = prompt_template.format(document=document, question=question)
        return self._call_ollama(prompt)
    
    def interactive_session(self, file_path: str):
        """Start interactive Q&A session"""
        try:
            document = self.load_document(file_path)
            print(f"✓ Loaded document: {file_path}")
            print(f"✓ Using model: {self.model}")
            print("✓ Ready for questions! (type 'quit' to exit, 'help' for commands)\n")
            
            while True:
                question = input("❓ Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                elif question.lower() == 'help':
                    self._show_help()
                    continue
                elif question.lower().startswith('mode:'):
                    mode = question.split(':', 1)[1].strip()
                    if mode in self.prompt_lib.prompts:
                        print(f"✓ Switched to mode: {mode}")
                        prompt_type = mode
                    else:
                        print(f"❌ Unknown mode. Available: {list(self.prompt_lib.prompts.keys())}")
                    continue
                elif not question:
                    continue
                
                print("🤔 Thinking...")
                try:
                    answer = self.ask_question(document, question, prompt_type)
                    print(f"\n💡 Answer:\n{answer}\n")
                except Exception as e:
                    print(f"❌ Error: {e}\n")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    def _show_help(self):
        """Show help information"""
        print("""
Available commands:
• Just type your question normally
• 'mode:qa' - Switch to Q&A mode (default)
• 'mode:summary' - Switch to summary mode
• 'mode:explain' - Switch to explanation mode  
• 'help' - Show this help
• 'quit' - Exit the program
        """)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python qa_system.py <document_file> [model_name]")
        print("Example: python qa_system.py document.txt llama3")
        sys.exit(1)
    
    file_path = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "llama3"
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    qa_system = OllamaQA(model=model)
    qa_system.interactive_session(file_path)


if __name__ == "__main__":
    main()
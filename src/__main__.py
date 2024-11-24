import sys
import os
import time
import requests
# from .Self_Improving_Search import EnhancedSelfImprovingSearch
from .llm_config import get_llm_config
# from .llm_response_parser import UltimateLLMResponseParser
# from .strategic_analysis_parser import StrategicAnalysisParser
from .research_manager import ResearchManager

class ResearchSession:
    
    def __init__(self, query):

        self.query = query
        self.llm_config=None
        self.research_manager = ResearchManager()

        print("Initialized new ResearchSession\n")
        

    def load_preset(self, preset_name):
        """Initialize system with proper error checking"""

        self.llm_config = get_llm_config(preset_name=preset_name)

        print("API server connection test...")

        try:
            response = requests.get(self.llm_config['base_url'], timeout=5)
            if response.status_code != 200:
                raise ConnectionError()
        except requests.exceptions.RequestException:
            raise ConnectionError(
                "\nCannot connect to OpenAI-compatible API server!"
                "\nPlease ensure:"
                "\n1. The server is running"
                "\n2. If running locally, check that the model is loaded and accessible"
                "\n3. If hosted externally, verify the base_url in your configuration file"
            )
        
        print("API server connection successful!\n")
        
    def start_research(self):
        if self.llm_config is None:
            raise ValueError("No API configuration loaded. Please load a preset first.")
        
        # Use ResearchManager to start research
        self.research_manager.start_research(self.query, self.llm_config)

def main():
    print("LLM Researcher\n")

    research_query = input(f"research query: ").strip()
    research_session = ResearchSession(research_query)
    
    print("enter LLM preset name (entering a preset which doesn't exists prompts it's creation)")
    preset_name = input("preset name (default=default): ").strip() or "default"

    print()

    research_session.load_preset(preset_name)
    research_session.start_research()

if __name__ == "__main__":
    main()

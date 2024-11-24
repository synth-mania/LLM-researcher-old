import sys
import os
import time
import requests
# from .Self_Improving_Search import EnhancedSelfImprovingSearch
from .llm_config import get_llm_config
# from .llm_response_parser import UltimateLLMResponseParser
# from .llm_wrapper import LLMWrapper
# from .strategic_analysis_parser import StrategicAnalysisParser
from .research_manager import ResearchManager

class ResearchSession:
    
    def __init__(self, query):

        self.query = query
        self.llm_config=None

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
        
        
        

def handle_research_mode(research_manager, query):
    """Handles research mode operations"""
    print("Initiating research mode...")

    try:
        # Start the research
        research_manager.start_research(query)

        submit_key = "CTRL+Z" if os.name == 'nt' else "CTRL+D"
        print("\nResearch Running. Available Commands:")
        print(f"Type command and press {submit_key}:")
        print("'s' = Show status")
        print("'f' = Show focus")
        print("'q' = Quit research")

        while research_manager.is_active():
            try:
                command = get_multiline_input().strip().lower()
                if command == 's':
                    print("\n" + research_manager.get_progress())
                elif command == 'f':
                    if research_manager.current_focus:
                        print(f"\nCurrent Focus:")
                        print(f"Area: {research_manager.current_focus.area}")
                        print(f"Priority: {research_manager.current_focus.priority}")
                        print(f"Reasoning: {research_manager.current_focus.reasoning}")
                    else:
                        print("\nNo current focus area")
                elif command == 'q':
                    break
            except KeyboardInterrupt:
                break

        # Get final summary first
        summary = research_manager.terminate_research()

        # Ensure research UI is fully cleaned up
        research_manager._cleanup_research_ui()

        # Now in main terminal, show summary
        print(f"\nResearch Summary:")
        print(summary)

        # Only NOW start conversation mode if we have a valid summary
        if research_manager.research_complete and research_manager.research_summary:
            time.sleep(0.5)  # Small delay to ensure clean transition
            research_manager.start_conversation_mode()

        return

    except KeyboardInterrupt:
        print("\nResearch interrupted.")
        research_manager.terminate_research()
    except Exception as e:
        print(f"\nResearch error: {str(e)}")
        research_manager.terminate_research()

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

import os
import sys
import threading
import time
import re
import json
import signal
from typing import List, Dict, Set, Optional, Tuple, Union
from dataclasses import dataclass
from queue import Queue
from datetime import datetime
from io import StringIO
import select
import termios
import tty
from threading import Event
from urllib.parse import urlparse
from pathlib import Path

from .llm_wrapper import LLMWrapper, ChatLLMWrapper # new

@dataclass
class ResearchFocus:
    """Represents a specific area of research focus"""
    area: str
    priority: int
    source_query: str = ""
    timestamp: str = ""
    search_queries: List[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.search_queries is None:
            self.search_queries = []

@dataclass
class AnalysisResult:
    """Contains the complete analysis result"""
    original_question: str
    focus_areas: List[ResearchFocus]
    raw_response: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class StrategicAnalysisParser:
    def __init__(self, llm=None):
        self.llm = llm
        # Simplify patterns to match exactly what we expect
        self.patterns = {
            'priority': [
                r"Priority:\s*(\d+)",  # Match exactly what's in our prompt
            ]
        }

    def strategic_analysis(self, original_query: str) -> Optional[AnalysisResult]:
        """Generate and process research areas with retries until success"""
        max_retries = 3
        try:
            self.logger.info("Starting strategic analysis...")
            prompt = f"""
You must select exactly 5 areas to investigate in order to explore and gather information to answer the research question:
"{original_query}"

You MUST provide exactly 5 areas numbered 1-5. Each must have a priority, YOU MUST ensure that you only assign one priority per area.
Assign priority based on the likelihood of a focus area being investigated to provide information that directly will allow you to respond to "{original_query}" with 5 being most likely and 1 being least.
Follow this EXACT format without any deviations or additional text:

1. [First research topic]
Priority: [number 1-5]

2. [Second research topic]
Priority: [number 1-5]

3. [Third research topic]
Priority: [number 1-5]

4. [Fourth research topic]
Priority: [number 1-5]

5. [Fifth research topic]
Priority: [number 1-5]
"""
            for attempt in range(max_retries):
                response = self.llm.generate(prompt, max_tokens=1000)
                focus_areas = self._extract_research_areas(response)

                if focus_areas:  # If we got any valid areas
                    # Sort by priority (highest first)
                    focus_areas.sort(key=lambda x: x.priority, reverse=True)

                    return AnalysisResult(
                        original_question=original_query,
                        focus_areas=focus_areas,
                        raw_response=response,
                        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                else:
                    print(f"\nRetrying research area generation (Attempt {attempt + 1}/{max_retries})...")

            # If all retries failed, try one final time with a stronger prompt
            prompt += "\n\nIMPORTANT: You MUST provide exactly 5 research areas with priorities. This is crucial."
            response = self.llm.generate(prompt, {"max_tokens": 1000})
            focus_areas = self._extract_research_areas(response)

            if focus_areas:
                focus_areas.sort(key=lambda x: x.priority, reverse=True)
                return AnalysisResult(
                    original_question=original_query,
                    focus_areas=focus_areas,
                    raw_response=response,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )

            return None

        except Exception as e:
            return None

    def _extract_research_areas(self, text: str) -> List[ResearchFocus]:
        """Extract research areas with enhanced parsing to handle priorities in various formats."""
        areas = []
        lines = text.strip().split('\n')

        current_area = None
        current_priority = None

        for i in range(len(lines)):
            line = lines[i].strip()
            if not line:
                continue

            # Check for numbered items (e.g., '1. Area Name')
            number_match = re.match(r'^(\d+)\.\s*(.*)', line)
            if number_match:
                # If we have a previous area, add it to our list
                if current_area is not None:
                    areas.append(ResearchFocus(
                        area=current_area.strip(' -:'),
                        priority=current_priority or 3,
                    ))
                # Start a new area
                area_line = number_match.group(2)

                # Search for 'priority' followed by a number, anywhere in the area_line
                priority_inline_match = re.search(
                    r'(?i)\bpriority\b\s*(?:[:=]?\s*)?(\d+)', area_line)
                if priority_inline_match:
                    # Extract and set the priority
                    try:
                        current_priority = int(priority_inline_match.group(1))
                        current_priority = max(1, min(5, current_priority))
                    except ValueError:
                        current_priority = 3  # Default priority if parsing fails
                    # Remove the 'priority' portion from area_line
                    area_line = area_line[:priority_inline_match.start()] + area_line[priority_inline_match.end():]
                    area_line = area_line.strip(' -:')
                else:
                    current_priority = None  # Priority might be on the next line

                current_area = area_line.strip()

            elif re.match(r'(?i)^priority\s*(?:[:=]?\s*)?(\d+)', line):
                # Extract priority from the line following the area
                try:
                    priority_match = re.match(r'(?i)^priority\s*(?:[:=]?\s*)?(\d+)', line)
                    current_priority = int(priority_match.group(1))
                    current_priority = max(1, min(5, current_priority))
                except (ValueError, IndexError):
                    current_priority = 3  # Default priority if parsing fails

            # Check if this is the last line or the next line is a new area
            next_line_is_new_area = (i + 1 < len(lines)) and re.match(r'^\d+\.', lines[i + 1].strip())
            if next_line_is_new_area or i + 1 == len(lines):
                if current_area is not None:
                    # Append the current area and priority to the list
                    areas.append(ResearchFocus(
                        area=current_area.strip(' -:'),
                        priority=current_priority or 3,
                    ))
                    current_area = None
                    current_priority = None

        return areas

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(\d+\))', r'\1.', text)
        text = re.sub(r'(?i)priority:', 'P:', text)
        return text.strip()

    def _add_area(self, areas: List[ResearchFocus], area: str, priority: Optional[int]):
        """Add area with basic validation"""
        if not area or len(area.split()) < 3:  # Basic validation
            return

        areas.append(ResearchFocus(
            area=area,
            priority=priority or 3,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            search_queries=[]
        ))

    def _normalize_focus_areas(self, areas: List[ResearchFocus]) -> List[ResearchFocus]:
        """Normalize and prepare final list of areas"""
        if not areas:
            return []

        # Sort by priority
        areas.sort(key=lambda x: x.priority, reverse=True)

        # Ensure priorities are properly spread
        for i, area in enumerate(areas):
            area.priority = max(1, min(5, area.priority))

        return areas[:5]

    def format_analysis_result(self, result: AnalysisResult) -> str:
        """Format the results for display"""
        if not result:
            return "No valid analysis result generated."

        formatted = [
            f"\nResearch Areas for: {result.original_question}\n"
        ]

        for i, focus in enumerate(result.focus_areas, 1):
            formatted.extend([
                f"\n{i}. {focus.area}",
                f"   Priority: {focus.priority}"
            ])

        return "\n".join(formatted)


class ResearchManager:
    """Manages the research process including analysis, search, and documentation"""
    def __init__(self, llm_config, search_engine, max_searches_per_cycle: int = 5):
        self.llm_wrapper = LLMWrapper(llm_config)
        self.parser = parser
        self.search_engine = search_engine
        self.max_searches = max_searches_per_cycle
        self.stop_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at'
        }

        # State tracking
        self.searched_urls: Set[str] = set()
        self.current_focus: Optional[ResearchFocus] = None
        self.original_query: str = ""
        self.focus_areas: List[ResearchFocus] = []
        self.is_running = False

        # New conversation mode attributes
        self.research_complete = False
        self.research_summary = ""
        self.conversation_active = False
        self.research_content = ""

        # Initialize document paths
        self.document_path = None
        self.session_files = []

        # Initialize UI and parser
        self.strategic_parser = StrategicAnalysisParser(llm=self.llm_wrapper)

    def print_thinking(self):
        """Display thinking indicator to user"""
        self.ui.update_output("🧠 Thinking...")


    def formulate_search_queries(self, focus_area: ResearchFocus) -> List[str]:
        """Generate search queries for a focus area"""
        try:

            prompt = f"""
In order to research this query/topic:

Context: {self.original_query}

Base a search query to investigate the following research focus, which is related to the original query/topic:

Area: {focus_area.area}

Create a search query that will yield specific, search results thare are directly relevant to your focus area.
Format your response EXACTLY like this:

Search query: [Your 2-5 word query]
Time range: [d/w/m/y/none]

Do not provide any additional information or explanation, note that the time range allows you to see results within a time range (d is within the last day, w is within the last week, m is within the last month, y is within the last year, and none is results from anytime, only select one, using only the corresponding letter for whichever of these options you select as indicated in the response format) use your judgement as many searches will not require a time range and some may depending on what the research focus is.
"""
            response_text = self.llm_wrapper.generate(prompt, max_tokens={"max_tokens": 50})
            query, time_range = self.parse_query_response(response_text)

            if not query:
                self.ui.update_output(f"{Fore.RED}Error: Empty search query. Using focus area as query...{Style.RESET_ALL}")
                return [focus_area.area]

            print(f"Original focus: {focus_area.area}")
            print(f"Formulated query: {query}")
            print(f"Time range: {time_range}")

            return [query]

        except Exception as e:
            logger.error(f"Error formulating query: {str(e)}")
            return [focus_area.area]

    def parse_search_query(self, query_response: str) -> Dict[str, str]:
        """Parse search query formulation response with improved time range detection"""
        try:
            lines = query_response.strip().split('\n')
            result = {
                'query': '',
                'time_range': 'none'
            }

            # First try to find standard format
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if 'query' in key:
                        result['query'] = self._clean_query(value)
                    elif ('time' in key or 'range' in key) and value.strip().lower() in ['d', 'w', 'm', 'y', 'none']:
                        result['time_range'] = value.strip().lower()

            # If no time range found, look for individual characters
            if result['time_range'] == 'none':
                # Get all text except the query itself
                full_text = query_response.lower()
                if result['query']:
                    full_text = full_text.replace(result['query'].lower(), '')

                # Look for isolated d, w, m, or y characters
                time_chars = set()
                for char in ['d', 'w', 'm', 'y']:
                    # Check if char exists by itself (not part of another word)
                    matches = re.finditer(r'\b' + char + r'\b', full_text)
                    for match in matches:
                        # Verify it's not part of a word
                        start, end = match.span()
                        if (start == 0 or not full_text[start-1].isalpha()) and \
                           (end == len(full_text) or not full_text[end].isalpha()):
                            time_chars.add(char)

                # If exactly one time char found, use it
                if len(time_chars) == 1:
                    result['time_range'] = time_chars.pop()

            return result
        except Exception as e:
            return {'query': '', 'time_range': 'none'}

    def _initialize_document(self):
        """Initialize research session document"""
        try:
            # Get all existing research session files
            self.session_files = []
            for file in os.listdir():
                if file.startswith("research_session_") and file.endswith(".txt"):
                    try:
                        num = int(file.split("_")[2].split(".")[0])
                        self.session_files.append(num)
                    except ValueError:
                        continue

            # Determine next session number
            next_session = 1 if not self.session_files else max(self.session_files) + 1
            self.document_path = f"research_session_{next_session}.txt"

            # Initialize the new document
            with open(self.document_path, 'w', encoding='utf-8') as f:
                f.write(f"Research Session {next_session}\n")
                f.write(f"Topic: {self.original_query}\n")
                f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")
                f.flush()

        except Exception as e:
            logger.error(f"Error initializing document: {str(e)}")
            self.document_path = "research_findings.txt"
            with open(self.document_path, 'w', encoding='utf-8') as f:
                f.write("Research Findings:\n\n")
                f.flush()

    def add_to_document(self, content: str, source_url: str, focus_area: str):
        """Add research findings to current session document"""
        try:
            with open(self.document_path, 'a', encoding='utf-8') as f:
                if source_url not in self.searched_urls:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"Research Focus: {focus_area}\n")
                    f.write(f"Source: {source_url}\n")
                    f.write(f"Content:\n{content}\n")
                    f.write(f"{'='*80}\n")
                    f.flush()
                    self.searched_urls.add(source_url)
                    self.ui.update_output(f"Added content from: {source_url}")
        except Exception as e:
            logger.error(f"Error adding to document: {str(e)}")
            self.ui.update_output(f"Error saving content: {str(e)}")

    def _process_search_results(self, results: Dict[str, str], focus_area: str):
        """Process and store search results"""
        if not results:
            return

        for url, content in results.items():
            if url not in self.searched_urls:
                self.add_to_document(content, url, focus_area)

    def _research_loop(self):
        """Main research loop with comprehensive functionality"""
        self.is_running = True
        try:
            self.research_started.set()

            while not self.should_terminate.is_set() and not self.shutdown_event.is_set():
                # Check if research is paused
                if self.research_paused:
                    time.sleep(1)
                    continue

                self.ui.update_output("\nAnalyzing research progress...")

                # Generate focus areas
                self.ui.update_output("\nGenerating research focus areas...")
                analysis_result = self.strategic_parser.strategic_analysis(self.original_query)

                if not analysis_result:
                    self.ui.update_output("\nFailed to generate analysis result. Retrying...")
                    continue

                focus_areas = analysis_result.focus_areas
                if not focus_areas:
                    self.ui.update_output("\nNo valid focus areas generated. Retrying...")
                    continue

                self.ui.update_output(f"\nGenerated {len(focus_areas)} research areas:")
                for i, focus in enumerate(focus_areas, 1):
                    self.ui.update_output(f"\nArea {i}: {focus.area}")
                    self.ui.update_output(f"Priority: {focus.priority}")

                # Process each focus area in priority order
                for focus_area in focus_areas:
                    if self.should_terminate.is_set():
                        break

                    # Check if research is paused
                    while self.research_paused and not self.should_terminate.is_set():
                        time.sleep(1)

                    if self.should_terminate.is_set():
                        break

                    self.current_focus = focus_area
                    self.ui.update_output(f"\nInvestigating: {focus_area.area}")

                    queries = self.formulate_search_queries(focus_area)
                    if not queries:
                        continue

                    for query in queries:
                        if self.should_terminate.is_set():
                            break

                        # Check if research is paused
                        while self.research_paused and not self.should_terminate.is_set():
                            time.sleep(1)

                        if self.should_terminate.is_set():
                            break

                        try:
                            self.ui.update_output(f"\nSearching: {query}")
                            results = self.search_engine.perform_search(query, time_range='none')

                            if results:
                                # self.search_engine.display_search_results(results)
                                selected_urls = self.search_engine.select_relevant_pages(results, query)

                                if selected_urls:
                                    self.ui.update_output("\n⚙️ Scraping selected pages...")
                                    scraped_content = self.search_engine.scrape_content(selected_urls)
                                    if scraped_content:
                                        for url, content in scraped_content.items():
                                            if url not in self.searched_urls:
                                                self.add_to_document(content, url, focus_area.area)

                        except Exception as e:
                            logger.error(f"Error in search: {str(e)}")
                            self.ui.update_output(f"Error during search: {str(e)}")

                    if self.check_document_size():
                        self.ui.update_output("\nDocument size limit reached. Finalizing research.")
                        return

                # After processing all areas, cycle back to generate new ones
                self.ui.update_output("\nAll current focus areas investigated. Generating new areas...")

        except Exception as e:
            logger.error(f"Error in research loop: {str(e)}")
            self.ui.update_output(f"Error in research process: {str(e)}")
        finally:
            self.is_running = False

    def start_research(self, topic: str):
        """Start research with new session document"""
        try:
            self.ui.setup()
            self.original_query = topic
            self._initialize_document()

            self.ui.update_output(f"Starting research on: {topic}")
            self.ui.update_output(f"Session document: {self.document_path}")
            self.ui.update_output("\nCommands available during research:")
            self.ui.update_output("'s' = Show status")
            self.ui.update_output("'f' = Show current focus")
            self.ui.update_output("'p' = Pause and assess the research progress")  # New command
            self.ui.update_output("'q' = Quit research\n")

            # Reset events
            self.should_terminate.clear()
            self.research_started.clear()
            self.research_paused = False  # Ensure research is not paused at the start
            self.awaiting_user_decision = False

            # Start research thread
            self.research_thread = threading.Thread(target=self._research_loop, daemon=True)
            self.research_thread.start()

            # Wait for research to actually start
            if not self.research_started.wait(timeout=10):
                self.ui.update_output("Error: Research failed to start within timeout period")
                self.should_terminate.set()
                return

            while not self.should_terminate.is_set():
                cmd = self.ui.get_input("Enter command: ")
                if cmd is None or self.shutdown_event.is_set():
                    if self.should_terminate.is_set() and not self.research_complete:
                        self.ui.update_output("\nGenerating research summary... please wait...")
                        summary = self.terminate_research()
                        self.ui.update_output("\nFinal Research Summary:")
                        self.ui.update_output(summary)
                    break
                if cmd:
                    self._handle_command(cmd)

        except Exception as e:
            logger.error(f"Error in research process: {str(e)}")
        finally:
            self._cleanup()

    def check_document_size(self) -> bool:
        """Check if document size is approaching context limit"""
        try:
            with open(self.document_path, 'r', encoding='utf-8') as f:
                content = f.read()
            estimated_tokens = len(content.split()) * 1.3
            max_tokens = self.llm_wrapper.llm_config.get('n_ctx', 2048)
            current_ratio = estimated_tokens / max_tokens

            if current_ratio > 0.8:
                logger.warning(f"Document size at {current_ratio*100:.1f}% of context limit")
                self.ui.update_output(f"Warning: Document size at {current_ratio*100:.1f}% of context limit")

            return current_ratio > 0.9
        except Exception as e:
            logger.error(f"Error checking document size: {str(e)}")
            return True

    def pause_and_assess(self):
        """Pause the research and assess if the collected content is sufficient."""
        print("\nPausing research for assessment...")

        # Read the current research content
        if not os.path.exists(self.document_path):
            print("No research data found to assess.")
            return

        with open(self.document_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            print("No research data was collected to assess.")
            return

        # Prepare the prompt for the AI assessment
        assessment_prompt = f"""
Based on the following research content, please assess whether the original query "{self.original_query}" can be answered sufficiently with the collected information.

Research Content:
{content}

Instructions:
1. If the research content provides enough information to answer the original query in detail, respond with: "The research is sufficient to answer the query."
2. If not, respond with: "The research is insufficient and it would be advisable to continue gathering information."
3. Do not provide any additional information or details.

Assessment:
"""

        # Generate the assessment
        assessment = self.llm_wrapper.generate(assessment_prompt, {"max_tokens": 200})

        # Display the assessment
        print("\nAssessment Result:")
        print(assessment.strip())

        # Provide user with options to continue or quit
        print("Enter 'c' to continue the research or 'q' to terminate and generate the summary.")
        self.awaiting_user_decision = True  # Flag to indicate we are waiting for user's decision

    def get_progress(self) -> str:
        """Get current research progress"""
        return f"""
Research Progress:
- Original Query: {self.original_query}
- Sources analyzed: {len(self.searched_urls)}
- Status: {'Active' if self.is_running else 'Stopped'}
- Current focus: {self.current_focus.area if self.current_focus else 'Initializing'}
"""

    def terminate_research(self) -> str:

        print("Initiating research termination...")


        if not os.path.exists(self.document_path):
            self.summary_ready = True
            indicator_thread.join(timeout=1.0)
            self._cleanup()
            return "No research data found to summarize."

        with open(self.document_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            self.research_content = content  # Store for conversation mode


        # Generate summary using LLM
        summary_prompt = f"""
        Analyze the following content to provide a comprehensive research summary and a response to the user's original query "{self.original_query}" ensuring that you conclusively answer the query in detail:

        Research Content:
        {content}

        Important Instructions:
        > Summarize the research findings that are relevant to the Original topic/question: "{self.original_query}"
        > Ensure that in your summary you directly answer the original question/topic conclusively to the best of your ability in detail.
        > Read the original topic/question again "{self.original_query}" and abide by any additional instructions that it contains, exactly as instructed in your summary otherwise provide it normally should it not have any specific instructions

        Summary:
        """

        summary = self.llm_wrapper.generate(summary_prompt, max_tokens=4000)

        # Signal that summary is complete to stop the progress indicator
        self.summary_ready = True
        indicator_thread.join(timeout=1.0)

        # Store summary and mark research as complete
        self.research_summary = summary
        self.research_complete = True

        # Format summary
        formatted_summary = f"""
        {'='*80}
        RESEARCH SUMMARY
        {'='*80}

        Original Query: {self.original_query}
        Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        {summary}

        {'='*80}
        End of Summary
        {'='*80}
        """

        # Write to document
        with open(self.document_path, 'a', encoding='utf-8') as f:
            f.write("\n\n" + formatted_summary)

        return formatted_summary

    def _generate_conversation_response(self, user_query: str) -> str:

        # First verify we have content
        if not self.research_content and not self.research_summary:
            # Try to reload from file if available
            try:
                if os.path.exists(self.document_path):
                    with open(self.document_path, 'r', encoding='utf-8') as f:
                        self.research_content = f.read().strip()
            except Exception as e:
                logger.error(f"Failed to reload research content: {str(e)}")

        # Prepare context, ensuring we have content
        context = f"""
Research Content:
{self.research_content}

Research Summary:
{self.research_summary if self.research_summary else 'No summary available'}
"""

        prompt = f"""
Based on the following research content and summary, please answer this question:

{context}

Question: {user_query}

you have 2 sets of instructions the applied set and the unapplied set, the applied set should be followed if the question is directly relating to the research content whereas anything else other then direct questions about the content of the research will result in you instead following the unapplied ruleset

Applied:

Instructions:
1. Answer based ONLY on the research content provided above if asked a question about your research or that content.
2. If the information requested isn't in the research, clearly state that it isn't in the content you gathered.
3. Be direct and specific in your response, DO NOT directly cite research unless specifically asked to, be concise and give direct answers to questions based on the research, unless instructed otherwise.

Unapplied:

Instructions:

1. Do not make up anything that isn't actually true.
2. Respond directly to the user's question in an honest and thoughtful manner.
3. disregard rules in the applied set for queries not DIRECTLY related to the research, including queries about the research process or what you remember about the research should result in the unapplied ruleset being used.

Answer:
"""

        response = self.llm_wrapper.generate(
            prompt,
            max_tokens=1000,  # Increased for more detailed responses
            temperature=0.7
        )

        if not response or not response.strip():
            return "I apologize, but I cannot find relevant information in the research content to answer your question."

        return response.strip()


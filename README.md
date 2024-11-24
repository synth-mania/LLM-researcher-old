# LLM-researcher-old

## Description
LLM-researcher-old is an automated research assistant that leverages locally-run or cloud hosted large language models to conduct automated online research on any given topic or question. Unlike traditional LLM interactions, this tool actually performs structured research by breaking down queries into focused research areas, systematically investigating via web searching and then scraping of relevant websites each area, and compiling it's findings all saved automatically into a text document with all content found and links for the source of each.

## Here's how it works:

1. You provide a research query (e.g., "What year will global population begin to decrease rather than increase according to research?")
2. The LLM analyzes your query and generates 5 specific research focus areas, each with assigned priorities based on relevance to the topic or question.
3. Starting with the highest priority area, the LLM:
   - Formulates targeted search queries
   - Performs web searches
   - Analyzes search results selecting the most relevant web pages
   - Scrapes and extracts relevant information for selected web pages
   - Documents all content it has found during the research session into a research text file including links to websites that the content was retrieved from
4. After investigating all focus areas, the LLM based on information is found generates new focus areas, and repeating it's research cycle, often finding new relevant focus areas based on findings in research it has previously found leading to interesting and novel research focuses in some cases.
5. You can let it research as long as you would like at any time being able to input a quit command which then stops the research and causes the LLM to review all the content collected so far in full and generate a comprehensive summary to respond to your original query or topic. 
6. Then the LLM will enter a conversation mode where you can ask specific questions about the research findings if desired.

The key distinction is that this isn't just a chatbot - it's an automated research assistant that methodically investigates topics and maintains a documented research trail all from a single question or topic of your choosing, and depending on your system and model can do over a hundred searches and content retrievals in a relatively short amount of time, you can leave it running and come back to a full text document with over a hundred pieces of content from relevant websites, and then have it summarise the findings and then even ask it questions about what it found.

## Features
- Automated research planning with prioritized focus areas
- Systematic web searching and content analysis
- All research content and source URLs saved into a detailed text document
- Research summary generation
- Post-research Q&A capability about findings
- Self-improving search mechanism
- Rich console output with status indicators
- Comprehensive answer synthesis using web-sourced information
- Research conversation mode for exploring findings

## Installation
Clone the repository and cd into the project root

```sh
git clone https://github.com/synth-mania/LLM-researcher-old
cd LLM-researcher-old
```

## Usage

### 1. Start LLM server

If you're running a locally hosted LLM server, ensure it is running and accessible from your machine.

### 2. Run the researcher

Open a terminal window and navigate to the project root directory, then execute the following command:

```sh
./start.sh
```

The program will prompt you to enter the name of an LLM configuration preset. If you enter no name, or if no such preset is found, you'll be prompted to enter the necessary information to connect to an LLM. (base url, model name, API key, etc.)

## Current Status

This is a (nearly) complete rewrite of [TheBlewish/Automated-AI-Web-Researcher-Ollama](https://github.com/TheBlewish/Automated-AI-Web-Researcher-Ollama). I wasn't satisfied with the speed of the progression of that project, and had several improvements in mind, so this hard fork exists to see where I can take the project on my own. At the moment, it is entirely nonfunctional, but I'm actively working on changing that. If you would like to contribute, feel free to open an issue or pull request.

## Dependencies
- Python 3.8 or later
- pip

## Contributing
Contributions are welcome! This is a prototype with room for improvements and new features.

## License
This project is licensed under the MIT License - see the [LICENSE] file for details.

## Acknowledgments
- DuckDuckGo for their search API
- James Warburton (i.e. TheBlewish) for creating the parent project from which this is derived.

## Disclaimer
This project is for educational purposes only. Ensure you comply with the terms of service of all APIs and services used.

# Job Application Automation Project

This project automates the process of fetching job listings, evaluating them using an LLM, and generating tailored motivation letters for the best-scored positions. 

It consists of three main components:

- _net.py_ 
  - Web scraping & parsing job listings

- ai.py 
  - Interacting with a local LLM (Ollama) for evaluation & letter generation

- main.py 
  - Links net and ai

With additional
- run.sh
  -  At root, handles initialization, venv, libraries, launches python, etc. Main entry point.

## Dataflow
```mermaid
graph TD
    subgraph ai.py
        AIClass[AI_Class]
        LLM[Ollama_deepseek-r1:14b]
        AIClass <-->|localhost or SSH tunnel| LLM
    end

    subgraph net.py
        NetparserClass[Netparser_Class]
        HTTP[Duunitori Job listings]
        NetparserClass <--> HTTP
    end

    subgraph Applicant-folder
        CV[Free form CV data] --> AIClass
        instr[AI prompt instructions] --> AIClass
    end

    subgraph Ouput
        OutputLetters
    end

    MainApp[main_py] --> NetparserClass
    MainApp --> AIClass

    NetparserClass --> OutputListings[Job listing JSON]
    AIClass --> OutputLetters[Tailored applications]
    OutputListings --> AIClass

```
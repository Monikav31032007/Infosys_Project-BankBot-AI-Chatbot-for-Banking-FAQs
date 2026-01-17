# BankBot – AI Chatbot for Banking FAQs

![Python](https://img.shields.io/badge/Python-3.x-blue)
![AI](https://img.shields.io/badge/AI-NLP-orange)
![LLM](https://img.shields.io/badge/LLM-Transformer--based-green)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Project Description

**BankBot** is an AI-powered chatbot designed to answer frequently asked banking-related questions efficiently and accurately. The system combines rule-based intent handling with Large Language Model (LLM) capabilities to provide both structured banking responses and intelligent handling of non-banking or open-ended queries.

This project is developed as part of an **Infosys Certification / Academic AI Project**, focusing on Natural Language Processing (NLP), conversational AI pipelines, and LLM integration.

BankBot demonstrates how traditional chatbot architectures can be enhanced using modern transformer-based language models while maintaining data privacy and control for domain-specific queries.

## Features

* Intent recognition and entity classification for banking queries
* Predefined conversational pipelines for core banking services
* SQLite database integration for dynamic responses
* LLM integration for non-banking or unsupported queries
* Modular and scalable architecture
* Admin panel for:

  * Conversation history
  * Analytics and confidence tracking
  * Adding new intents and training examples
* Configurable LLM support (model-agnostic design)

## Techniques Used

### Natural Language Processing (NLP)

* Tokenization and text preprocessing
* Intent classification
* Entity extraction
* Pattern-based and ML-based matching

### Prompt Engineering

* Context-aware prompts
* Controlled response generation
* Domain restriction prompts for safe outputs

### LLM-based Text Generation

* Transformer-based LLM usage
* Fallback mechanism for unknown intents
* Controlled integration to avoid hallucinations in banking data

## Tech Stack

### Programming Language

* Python 3.x

### Libraries / Frameworks

* Flask / Streamlit (for UI and admin dashboard)
* SQLite (database)
* JSON (intent and entity storage)
* Pandas (analytics and reporting)
* Plotly (visual analytics)

### AI / ML Technologies

* Natural Language Processing (NLP)
* Intent Classification
* Named Entity Recognition (NER)
* Transformer-based Language Models

## LLM Details

* Uses **transformer-based Large Language Models (LLMs)**
* LLM is **fully configurable**, allowing:

  * Open-source models (e.g., GPT-style, LLaMA-based models)
  * API-based models (if enabled)
* LLM is invoked **only when queries fall outside banking intents**, ensuring accuracy and reliability for domain-specific responses

## Project Structure

```
Infosys_Project-BankBot-AI-Chatbot-for-Banking-FAQs/
│
├── admin_dashboard.py        # Admin panel and analytics
├── app.py                    # Main chatbot application
├── database/
│   └── bankbot.db            # SQLite database
├── nlu_engine/
│   ├── intents.json          # Banking intents
│   ├── entities.json         # Entity definitions
│   └── nlu_processor.py      # NLP processing logic
├── llm/
│   └── llm_handler.py        # LLM integration layer
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
└── assets/                   # UI assets and resources
```

## Installation Steps

1. Clone the repository:

   ```
   git clone https://github.com/Monikav31032007/Infosys_Project-BankBot-AI-Chatbot-for-Banking-FAQs.git
   ```

2. Navigate to the project directory:

   ```
   cd Infosys_Project-BankBot-AI-Chatbot-for-Banking-FAQs
   ```

3. Create a virtual environment (optional but recommended):

   ```
   python -m venv venv
   ```

4. Activate the virtual environment:

   * Windows:

     ```
     venv\Scripts\activate
     ```
   * Linux / macOS:

     ```
     source venv/bin/activate
     ```

5. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

## How to Run the Project Locally

1. Start the chatbot application:

   ```
   python app.py
   ```

2. Start the admin dashboard (if separate):

   ```
   streamlit run admin_dashboard.py
   ```

3. Open your browser and access:

   * Chatbot UI: `http://localhost:5000` (or specified port)
   * Admin Dashboard: `http://localhost:8501`

## Certification Use Case

This project is suitable for:

* **Infosys Certification Submission**
* Academic AI / NLP Mini Project
* Demonstration of:

  * Conversational AI pipelines
  * NLP and intent-based systems
  * LLM integration in real-world applications
  * AI system design and modular architecture

The project follows industry-aligned practices and showcases applied AI skills relevant to enterprise chatbot development.

## License

This project is licensed under the **MIT License**.
You are free to use, modify, and distribute this project for educational and non-commercial purposes.

---

**Developed for academic and certification purposes – showcasing practical AI, NLP, and LLM integration in banking chatbots.**

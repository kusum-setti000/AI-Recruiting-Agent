# AI Recruiting Agent

A code-first Generative AI recruiting assistant that analyzes candidate resumes against job descriptions and produces a structured, evidence-based candidate assessment.

The project was built from scratch using Python, FastAPI, OpenAI API, Pydantic, and Streamlit.

## Features

- Upload candidate resumes in PDF or DOCX format
- Extract resume text automatically
- Compare resume evidence against a job description
- Identify matching skills
- Identify missing or unverified skills
- Highlight candidate strengths
- Analyze experience alignment
- Identify potential gaps
- Generate recruiter follow-up questions
- Generate an overall candidate assessment
- Calculate a match score
- Flag uncertain information for human review
- Avoid using protected characteristics in candidate evaluation

## Architecture

```text
User
  |
  v
Streamlit Frontend
  |
  | HTTP Request
  v
FastAPI Backend
  |
  +--> Resume Parser
  |
  +--> Screening Prompt
  |
  +--> OpenAI API
  |
  v
Structured Candidate Analysis
  |
  v
Streamlit Results Dashboard
```

## Tech Stack

**Backend**
- Python
- FastAPI
- Pydantic

**Generative AI**
- OpenAI API
- Large Language Models (LLMs)
- Prompt Engineering
- Structured Outputs

**Frontend**
- Streamlit

**Document Processing**
- PDF parsing
- DOCX parsing

**Integration**
- REST API
- Multipart file upload
- JSON responses

## Project Structure

```text
AI-Recruiting-Agent/
│
├── app/
│   ├── main.py
│   ├── models/
│   │   └── schemas.py
│   ├── prompts/
│   │   └── screening_prompt.py
│   └── services/
│       ├── llm_service.py
│       └── resume_parser.py
│
├── frontend/
│   └── streamlit_app.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

## How It Works

1. A recruiter enters a job title and job description.
2. The recruiter uploads a candidate resume.
3. Streamlit sends the information to the FastAPI backend.
4. The backend extracts text from the resume.
5. A structured screening prompt combines the resume evidence with the job requirements.
6. The application sends the prompt to the OpenAI API.
7. The model returns structured candidate analysis.
8. The Streamlit dashboard presents the results to the recruiter.

## Candidate Analysis

The system produces:

- Match Score
- Matching Skills
- Missing / Unverified Skills
- Candidate Strengths
- Experience Alignment
- Potential Gaps
- Recruiter Questions
- Overall Assessment
- Assessment Reasoning

Possible assessments include:

- Strong Match
- Potential Match
- Needs Human Review
- Weak Match

## Responsible AI

The application is designed as a recruiter decision-support tool rather than an autonomous hiring system.

The screening prompt instructs the model to:

- Use only information supported by the candidate's resume
- Avoid assumptions about unverified skills
- Avoid protected characteristics
- Flag uncertain evidence for human review
- Explain the reasoning behind the assessment

Final hiring decisions should always remain with qualified human reviewers.

## Setup

Clone the repository:

```bash
git clone https://github.com/kusum-setti000/AI-Recruiting-Agent.git
cd AI-Recruiting-Agent
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```text
OPENAI_API_KEY=your_openai_api_key
```

Never commit the `.env` file or API keys to GitHub.

## Run the Application

Start the FastAPI backend:

```bash
uvicorn app.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

FastAPI Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Open a second terminal and start Streamlit:

```bash
streamlit run frontend/streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

## Example

For a Generative AI Engineer position, the system can compare requirements such as:

- Python
- LLMs
- RAG
- FastAPI
- LangChain
- Vector databases
- Docker
- Azure
- REST APIs

against evidence contained in the uploaded resume.

The application then presents a structured candidate assessment and identifies requirements that require recruiter verification.

## Future Improvements

- Multi-resume batch screening
- Vector database integration
- RAG-based job and candidate knowledge retrieval
- LangGraph-based agent orchestration
- Candidate ranking
- Evaluation and observability
- Docker containerization
- Cloud deployment
- Authentication and role-based access
- Persistent analysis history

## Disclaimer

This project is intended for demonstration and decision-support purposes. AI-generated assessments may contain errors and should not be used as the sole basis for employment decisions.

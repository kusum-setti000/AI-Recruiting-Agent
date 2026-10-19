# TalentFlow AI

**AI-Powered Candidate Screening with Streamlit, LangGraph, and OpenAI**

TalentFlow AI is a recruiter decision-support application that evaluates candidate resumes against job requirements and produces structured, evidence-based screening assessments.

The application uses Streamlit for its user interface, LangGraph for screening workflow orchestration, and OpenAI for structured candidate analysis.

## Features

- Upload candidate resumes in PDF or DOCX format
- Extract and process resume text
- Compare candidate evidence against job requirements
- Identify matching and missing or unverified skills
- Assess experience alignment, strengths, and gaps
- Generate recruiter follow-up questions
- Produce structured candidate assessments and match scores
- Flag uncertain information for human review
- Avoid evaluating candidates based on protected characteristics

## Architecture

```text
Recruiter
    |
    v
Streamlit UI
    |
    v
LangGraph Screening Workflow
    |
    +--> Input Validation
    |
    +--> Document Loading (PDF/DOCX)
    |
    +--> Candidate Screening (OpenAI)
    |
    +--> Assessment Validation
    |
    v
Structured Screening Results
    |
    v
Streamlit Results Dashboard
```

The Streamlit application invokes the LangGraph screening workflow directly. No separate FastAPI server is required.

## Tech Stack

**Application**
- Python
- Streamlit
- Pydantic

**AI Orchestration**
- LangChain
- LangGraph
- LangChain OpenAI
- OpenAI API

**Document Processing**
- PyMuPDF
- python-docx

**Configuration and Observability**
- python-dotenv
- LangSmith integration, with tracing disabled by default

## Project Structure

```text
AI-Recruiting-Agent/
|
+-- app/
|   +-- agents/
|       +-- config.py
|       +-- document_loader.py
|       +-- graph.py
|       +-- models.py
|       +-- nodes.py
|       +-- observability.py
|       +-- prompts.py
|       +-- schemas.py
|       +-- scoring.py
|
+-- frontend/
|   +-- components/
|   |   +-- screening_form.py
|   |   +-- results.py
|   |   +-- sidebar.py
|   +-- styles/
|   |   +-- main.css
|   +-- streamlit_app.py
|
+-- requirements.txt
+-- README.md
```

## How It Works

1. The recruiter enters the job title and job description.
2. The recruiter uploads a PDF or DOCX resume.
3. Streamlit invokes the LangGraph screening workflow.
4. The workflow validates the input and extracts resume content.
5. The screening node evaluates resume evidence against the job requirements using OpenAI.
6. The assessment is returned as structured data and validated.
7. The Streamlit dashboard displays the screening results.

## Candidate Assessment

The application produces a structured assessment that may include:

- Overall match score
- Matching skills
- Missing or unverified skills
- Candidate strengths
- Experience alignment
- Potential gaps
- Recruiter follow-up questions
- Assessment reasoning
- Human-review indicators

All AI-generated assessments are intended to support, not replace, recruiter judgment.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/kusum-setti000/AI-Recruiting-Agent.git
cd AI-Recruiting-Agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_supported_model
LANGSMITH_TRACING=false
```

Use an OpenAI model supported by your API account and compatible with the application's structured-output workflow.

Never commit API keys or your `.env` file to Git.

## Run the Application

Start Streamlit from the project root:

```bash
streamlit run frontend/streamlit_app.py
```

Open:

```text
http://localhost:8501
```

The screening workflow runs directly inside the Streamlit application. No FastAPI or Uvicorn process is required.

## Debugging

Open the project in VS Code.

Use the **Debug TalentFlow AI (Streamlit)** launch configuration to start the application and debug Python execution with breakpoints.

Relevant workflow modules include:

- `app/agents/graph.py` — workflow definition and execution
- `app/agents/nodes.py` — screening workflow nodes
- `app/agents/document_loader.py` — resume processing
- `app/agents/scoring.py` — scoring logic
- `app/agents/observability.py` — tracing configuration

## Responsible AI

TalentFlow AI is designed as a decision-support system, not an autonomous hiring authority.

The screening workflow is intended to:

- Base assessments on documented resume evidence
- Avoid unsupported assumptions
- Exclude protected characteristics from candidate evaluation
- Identify missing or uncertain evidence
- Support human review of screening outcomes

Final hiring decisions must remain with qualified human reviewers.

## Future Improvements

- Multi-resume batch screening
- Candidate comparison and ranking
- Screening quality evaluation
- Privacy-safe production observability
- Authentication and role-based access
- Persistent screening history
- Docker containerization
- Cloud deployment

## Disclaimer

TalentFlow AI is a demonstration and recruiter decision-support application. AI-generated assessments may contain errors or omissions and should not be used as the sole basis for employment decisions.
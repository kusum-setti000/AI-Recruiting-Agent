import os

from dotenv import load_dotenv
from openai import OpenAI

from app.models.schemas import CandidateAnalysis


# Load variables from the .env file
load_dotenv(override=True)


# Create the OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def analyze_with_llm(prompt: str) -> CandidateAnalysis:
    """
    Send the recruiting prompt to the OpenAI API
    and return structured candidate analysis.
    """

    response = client.responses.parse(
        model="gpt-5.6-luna",
        input=prompt,
        text_format=CandidateAnalysis
    )

    return response.output_parsed
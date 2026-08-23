"""
* Refactored Walid's interview agent module with modular state management and dialogue handling.
* Still temp solution - the goal is to get the front end and back end "working."

Interview Agent Module (Refactored Version)

This module provides a modular implementation of an interview agent using FastAPI. 
The primary focus is on state management and hierarchical question loading, enabling 
personalized and adaptive interview experiences for users.

Key Components:
1. StateManager:
   - Manages user-specific states persistently in a JSON file.
   - Tracks user progress through a series of thoughts (main ideas) and sub-thoughts 
   (nested subtopics).
   - Supports state initialization, updates, and resets, ensuring smooth multi-session continuity.

2. QuestionLoader:
   - Reads and navigates hierarchical question data (thoughts and sub-thoughts) from 
   an external data file.
   - Determines the next question for a user based on their current progress.
   - Implements overflow logic to transition between nested sub-thoughts and thoughts, resetting states when no questions remain.

3. DialogueManager:
   - Integrates with OpenAI's API to dynamically generate refined interview questions.
   - Uses a structured prompt design to produce contextually relevant and concise questions.

4. FastAPI Endpoints:
   - `/get_question/{user_id}`: Retrieves the next question for a user based on their state.
   - `/synthesize_speech`: Converts text to speech using Google Text-to-Speech (gTTS).
   - Root and test endpoints for server health checks.

Features:
- Persistent user state management.
- Dynamic navigation through hierarchical question data.
- Integration of static data with dynamic AI-driven question generation.
- Accessibility support via text-to-speech capabilities.
- Modular and extensible architecture for adding new features.

TODO: Future improvements
Because FastAPI uses Pydantic in its own code, it works REALLY WELL with pydantic models.
If we fully leverage Pydantic models, the StateManager can directly operate on structured data 
in Pydantic models, eliminating unnecessary conversions like model_dump() or intermediate JSON handling. 

Benefits of Pydantic Models
- Direct Validation and Parsing: Load and validate data directly into models for consistency 
and type safety.
- Automatic Serialization/Deserialization: Easily serialize and deserialize models model_dump().
- Simplified Updates: Immutable models prevent accidental state corruption 
(or opt-in for changes with validate_assignment=True).
- Rich Field-Level Validation
"""

from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from pydantic import BaseModel, ValidationError
from io import BytesIO
import base64
import openai
import configparser
import os
import logging
import logging_config
import getpass
from dotenv import load_dotenv
import uvicorn

# Import internal modules
from interviewagent_support import QuestionLoader, StateManager
from project_config import (
    CLAUDE_INDEXED_MODELS_DIR,
    OPENAI_INDEXED_MODELS_DIR,
)

# Set up logging
logger = logging.getLogger(__name__)

# *Data source:
source_file_list = [
    "array_of_thoughts_output_with_index_embedded_software_development_claude.json",
    "array_of_thoughts_output_with_index_embedded_software_development_in_aerospace_claude.json",
    "array_of_thoughts_output_with_index_embedded_software_development_in_automotive_claude.json",
]

array_of_thoughts_file_name = source_file_list[0]  #! pick 0, 1, 2

# Initialize FastAPI app
# - Sets up the FastAPI server with CORS middleware to allow cross-origin requests.
# - Defines routes for fetching questions, synthesizing speech, and performing health checks.
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================== Helper Functions ==================
def get_openai_api_key():
    """Load the OpenAI API key from environment (xf) or configuration file (walid)."""
    current_user = getpass.getuser()
    xf_username = "xzhan"

    if current_user == xf_username:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            logger.info("Loaded API key from .env")
            return api_key

    config = configparser.ConfigParser()
    config.read("/root/backend/config.ini")
    api_key = config.get("settings", "OPENAI_API_KEY", fallback=None)
    if api_key:
        logger.info("Loaded API key from config file")
        return api_key

    raise ValueError("OpenAI API key not found.")


class DialogueManager:
    """
    Uses OpenAI’s API to dynamically generate interview questions based on provided details.

    """

    def __init__(self):
        api_key = get_openai_api_key()
        openai.api_key = api_key
        self.llm_client = openai

    def generate_question(
        self, description: str, importance: str, pleasantry: str = ""
    ):
        """Generate a question using the LLM."""
        prompt = (
            f"{pleasantry}Generate an interview question based on the following details:\n\n"
            f"Description: {description}\n"
            f"Importance: {importance}\n\n"
            "The question should be concise, relevant, and specific to the topic."
        )
        response = self.llm_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an interview agent."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()


# ================== FastAPI Endpoints ==================
@app.get("/")
async def read_root():
    """Root endpoint to verify the server is running."""
    return {"message": "FastAPI server is running!"}


@app.get("/get_question/{user_id}")
async def get_question_async(user_id: str):
    """
    Retrieve the next question for a user based on their state.

    Args:
        user_id (str): The unique identifier for the user.

    Returns:
        dict: JSON response containing the generated question and metadata.
    """
    try:
        state_manager = StateManager()
        question_loader = QuestionLoader(
            data_file=Path(CLAUDE_INDEXED_MODELS_DIR / array_of_thoughts_file_name)
        )  # *This is where the source data is loaded in
        dialogue_manager = DialogueManager()

        question_data = question_loader.get_next_question(user_id, state_manager)
        if "message" in question_data:
            return question_data

        thought = question_data["thought"]
        sub_thought = question_data["sub_thought"]
        pleasantry = (
            "Hello! Let's start with this: "
            if sub_thought["sub_thought_index"] == 0
            else ""
        )
        generated_question = dialogue_manager.generate_question(
            description=sub_thought["description"],
            importance=sub_thought["importance"],
            pleasantry=pleasantry,
        )

        return {
            "question": generated_question,
            "thought_index": state_manager.get_state(user_id)["thought_index"],
            "sub_thought_index": state_manager.get_state(user_id)["sub_thought_index"],
            "thought": thought["thought"],
            "sub_thought_name": sub_thought["name"],
            "description": sub_thought["description"],
            "importance": sub_thought["importance"],
            "connection_to_next": sub_thought.get("connection_to_next"),
        }
    except Exception as e:
        logger.error(f"Error retrieving question for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error retrieving question: {str(e)}"
        )


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


@app.post("/synthesize_speech")
async def synthesize_speech(request: TTSRequest):
    """Convert text to speech and return the audio as a Base64-encoded string."""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        mp3_fp = BytesIO()
        tts = gTTS(text=request.text, lang=request.language, slow=False)
        tts.write_to_fp(mp3_fp)

        mp3_fp.seek(0)
        audio_base64 = base64.b64encode(mp3_fp.read()).decode("utf-8")

        return {"audio": audio_base64, "content_type": "audio/mp3"}
    except Exception as e:
        logger.error(f"Error in TTS processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS processing failed: {str(e)}")


@app.get("/test")
async def test():
    """Test endpoint to verify the server is running."""
    return {"status": "Server is running"}


if __name__ == "__main__":
    uvicorn.run(
        "interviewagent_xf_edit_2:app", host="127.0.0.1", port=8000, reload=True
    )

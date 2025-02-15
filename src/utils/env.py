import os
from dotenv import load_dotenv

def setup_environment():
    load_dotenv()
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    
    if not openai_api_key or not langchain_api_key:
        raise ValueError(
            "Missing environment variables. Please check your .env file.")
    
    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ['LANGCHAIN_API_KEY'] = langchain_api_key
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'

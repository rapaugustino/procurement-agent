from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "Procurement Agent API"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database settings (add when needed)
    database_url: Optional[str] = None
    
    # API Keys (add your specific keys here)
    # openai_api_key: Optional[str] = None
    # langchain_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

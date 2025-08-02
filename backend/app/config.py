from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    model_config = {
        "extra": "ignore",  # Ignore extra environment variables
        "env_file": ".env",
        "case_sensitive": False
    }
    app_name: str = "Procurement Agent API"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Application Settings
    app_env: str = "development"
    secret_key: str = "change_me_in_production"
    
    # Database settings (add when needed)
    database_url: Optional[str] = None
    
    # Azure Active Directory Configuration (removed - no longer needed for RAG-only functionality)
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_api_type: str = "azure"  # or "openai"
    openai_api_version: str = "2024-02-01"
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_chat_deployment_name: Optional[str] = None
    azure_openai_embedding_deployment: Optional[str] = None
    azure_openai_embedding_endpoint: Optional[str] = None
    azure_openai_embedding_api_key: Optional[str] = None
    
    # Azure AI Search Configuration
    azure_search_endpoint: Optional[str] = None
    azure_search_api_key: Optional[str] = None
    azure_search_index_name: Optional[str] = None
    
    # Microsoft Teams Configuration
    teams_app_id: Optional[str] = None
    teams_app_password: Optional[str] = None
    
    # Microsoft Graph API Configuration (removed - no longer needed)
    # graph_api_scope: str = "https://graph.microsoft.com/.default"
    # graph_api_base_url: str = "https://graph.microsoft.com/v1.0"
    # These should be configured in your Azure AD app registration
    
    # Legacy property mappings for backward compatibility
    @property
    def azure_openai_chat_key(self) -> Optional[str]:
        return self.azure_openai_api_key
    
    @property
    def azure_openai_chat_endpoint(self) -> Optional[str]:
        return self.azure_openai_endpoint
    
    @property
    def azure_openai_chat_deployment(self) -> Optional[str]:
        return self.azure_openai_chat_deployment_name
    
    @property
    def azure_openai_api_version(self) -> str:
        return self.openai_api_version
    
    @property
    def azure_openai_embedding_key(self) -> Optional[str]:
        return self.azure_openai_embedding_api_key
    
    @property
    def azure_search_key(self) -> Optional[str]:
        return self.azure_search_api_key
    
    @property
    def azure_search_service(self) -> Optional[str]:
        # Extract service name from endpoint
        if self.azure_search_endpoint:
            # Extract from https://service-name.search.windows.net/
            import re
            match = re.search(r'https://([^.]+)\.search\.windows\.net', self.azure_search_endpoint)
            return match.group(1) if match else None
        return None
    
    @property
    def azure_search_index(self) -> Optional[str]:
        return self.azure_search_index_name
    
    # Configuration moved to model_config above

settings = Settings()

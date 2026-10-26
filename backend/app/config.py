from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "RecoverIQ — AI Revenue Recovery Agent"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "hackathon"
    
    # Financial & Recovery Engine Safety
    SIMULATION_MODE: bool = True
    DEFAULT_CURRENCY: str = "USD"
    MAX_RETRIES: int = 3
    DEFAULT_COOLDOWN_HOURS: int = 24
    REQUIRE_APPROVAL_OVER_AMOUNT_CENTS: int = 50000  # $500.00+ always requires human approval
    
    # Ollama Local LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:e2b"
    OLLAMA_REQUEST_TIMEOUT: float = 45.0  # seconds
    OLLAMA_MAX_CONTEXT_TOKENS: int = 2048
    
    # SQLite Database
    DATABASE_URL: str = "sqlite:///./recoveriq.db"

settings = Settings()

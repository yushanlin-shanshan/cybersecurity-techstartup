from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    data_dir: Path
    cors_origins: tuple[str, ...] = ('http://localhost:3000', 'http://localhost:5173')
    api_token: str = ''
    max_upload_bytes: int = 150 * 1024 * 1024
    max_expanded_bytes: int = 6 * 1024 * 1024 * 1024
    max_alerts: int = 3_000_000
    llm_enabled: bool = False
    openai_api_key: str = ''
    openai_model: str = 'gpt-4o-mini'

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            data_dir=Path(os.getenv('DATA_DIR', './data')).resolve(),
            cors_origins=tuple(x.strip() for x in os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',') if x.strip()),
            api_token=os.getenv('API_TOKEN', ''),
            max_upload_bytes=int(os.getenv('MAX_UPLOAD_MB', '150')) * 1024 * 1024,
            max_expanded_bytes=int(os.getenv('MAX_EXPANDED_MB', '6144')) * 1024 * 1024,
            max_alerts=int(os.getenv('MAX_ALERTS', '3000000')),
            llm_enabled=os.getenv('LLM_ENABLED', 'false').lower() == 'true',
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            openai_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
        )

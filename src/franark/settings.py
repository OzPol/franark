from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    runtime: str = "demo"
    model: str = ""
    api_key: str = ""
    data_dir: Path = Path("data")
    max_calls: int = 10
    max_output_tokens: int = 1400

    def __post_init__(self):
        if self.runtime not in {"demo", "openai"}:
            raise ValueError("FRANARK_RUNTIME must be demo or openai.")
        if not 1 <= self.max_calls <= 20:
            raise ValueError("FRANARK_MAX_CALLS must be between 1 and 20.")
        if not 256 <= self.max_output_tokens <= 8000:
            raise ValueError("FRANARK_MAX_OUTPUT_TOKENS must be between 256 and 8000.")

    @classmethod
    def from_env(cls):
        return cls(
            runtime=os.getenv("FRANARK_RUNTIME", "demo"),
            model=os.getenv("FRANARK_MODEL", ""),
            api_key=os.getenv("OPENAI_API_KEY", ""),
            data_dir=Path(os.getenv("FRANARK_DATA_DIR", "data")),
            max_calls=int(os.getenv("FRANARK_MAX_CALLS", "10")),
            max_output_tokens=int(os.getenv("FRANARK_MAX_OUTPUT_TOKENS", "1400")),
        )

"""Language model providers behind the core LLM protocol."""

from haver.config import Settings
from haver.core.llm import LLM


def build_llm(settings: Settings) -> LLM:
    if settings.llm_provider == "gemini":
        if settings.gemini_api_key is None:
            raise ValueError("LLM_PROVIDER is gemini but GEMINI_API_KEY is not set")
        from haver.providers.gemini import GeminiLLM

        return GeminiLLM(settings.gemini_api_key.get_secret_value(), settings.gemini_model)
    from haver.providers.offline import OfflineLLM

    return OfflineLLM()

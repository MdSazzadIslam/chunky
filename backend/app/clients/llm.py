from openai import AuthenticationError, OpenAI, OpenAIError

from app.core.config import Settings, get_settings
from app.core.exceptions import LLMConfigurationError, LLMProviderError

_client: OpenAI | None = None
_client_fingerprint: str | None = None
REQUEST_TIMEOUT_SECONDS = 60.0
MAX_OUTPUT_TOKENS = 1024


def get_openai_client(settings: Settings | None = None) -> OpenAI:
    global _client, _client_fingerprint
    config = settings or get_settings()
    key = config.openai_api_key.strip()
    if not key or key.startswith("sk-your-key"):
        raise LLMConfigurationError(
            "Set OPENAI_API_KEY in backend/.env before asking questions or uploading PDFs"
        )
    fingerprint = f"{key}:{config.openai_base_url}"
    if _client is None or _client_fingerprint != fingerprint:
        kwargs: dict[str, object] = {"api_key": key, "timeout": REQUEST_TIMEOUT_SECONDS}
        if config.openai_base_url:
            kwargs["base_url"] = config.openai_base_url
        _client = OpenAI(**kwargs)
        _client_fingerprint = fingerprint
    return _client


def embed_texts(texts: list[str], settings: Settings | None = None) -> list[list[float]]:
    if not texts:
        return []
    config = settings or get_settings()
    client = get_openai_client(config)
    embeddings: list[list[float]] = []
    try:
        for start in range(0, len(texts), config.embedding_batch_size):
            batch = texts[start : start + config.embedding_batch_size]
            response = client.embeddings.create(model=config.embedding_model, input=batch)
            embeddings.extend(item.embedding for item in response.data)
    except AuthenticationError as exc:
        raise LLMConfigurationError("Invalid OpenAI API key. Set OPENAI_API_KEY in backend/.env") from exc
    except OpenAIError as exc:
        raise LLMProviderError("The language model request failed") from exc
    return embeddings


def complete_chat(system_prompt: str, user_prompt: str, settings: Settings | None = None) -> str:
    config = settings or get_settings()
    client = get_openai_client(config)
    try:
        response = client.chat.completions.create(
            model=config.openai_model,
            temperature=0.2,
            max_tokens=MAX_OUTPUT_TOKENS,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except AuthenticationError as exc:
        raise LLMConfigurationError("Invalid OpenAI API key. Set OPENAI_API_KEY in backend/.env") from exc
    except OpenAIError as exc:
        raise LLMProviderError("The language model request failed") from exc
    content = response.choices[0].message.content
    return content.strip() if content else ""

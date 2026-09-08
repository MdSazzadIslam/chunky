class AppError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class PayloadTooLargeError(AppError):
    status_code = 413


class UnsupportedMediaError(AppError):
    status_code = 415


class LLMConfigurationError(AppError):
    status_code = 400


class LLMProviderError(AppError):
    status_code = 502

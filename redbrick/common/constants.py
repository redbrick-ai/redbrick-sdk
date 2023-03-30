"""Constants."""


MAX_CONCURRENCY = 30
MAX_FILE_BATCH_SIZE = 5
MAX_RETRY_ATTEMPTS = 3

DEFAULT_URL = "https://api.redbrickai.com"

PEERLESS_ERRORS = (
    KeyboardInterrupt,
    PermissionError,
    TimeoutError,
    ConnectionError,
    ValueError,
    SystemError,
    SystemExit,
)

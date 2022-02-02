"""Constants."""


MAX_CONCURRENCY = 30
MAX_RETRY_ATTEMPTS = 5

DEFAULT_URL = "https://api.redbrickai.com"

ORG_API_HAS_CHANGED = (
    "this api has changed recently, try running help(redbrick.get_org)"
    + " or visiting https://redbrick-sdk.readthedocs.io/en/stable/#redbrick.get_org"
)

PROJECT_API_HAS_CHANGED = (
    "this api has changed recently, try running help(redbrick.get_project)"
    + " or visiting https://redbrick-sdk.readthedocs.io/en/stable/#redbrick.get_project"
)

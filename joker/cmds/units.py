from typing import Dict

# The rest of the codebase uses mojos everywhere.
# Only use these units for user facing interfaces.
units: Dict[str, int] = {
    "joker": 10 ** 8,  # 1 joker (XJK) is 1,000,000,000,000 mojo (1 trillion)
    "mojo": 1,
    "cat": 10 ** 3,  # 1 CAT is 1000 CAT mojos
}

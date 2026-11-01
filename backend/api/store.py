"""Storage boundary for the API skeleton."""


def application_status() -> str:
    """Report the dependency-free store used by the bootstrap service."""
    return "in-memory"


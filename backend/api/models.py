"""Domain model boundary.

Persistent Django models are intentionally deferred until the database task.
Keeping this module as the model boundary lets routers and stores evolve
without coupling the API bootstrap to a database.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    status: str
    service: str


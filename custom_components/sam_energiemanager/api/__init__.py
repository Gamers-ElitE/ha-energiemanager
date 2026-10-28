"""
API package for sam_energiemanager.

Exception hierarchy:
    EnergiemanagerApiClientError (base)
    ├── EnergiemanagerApiClientCommunicationError (network/timeout)
    └── EnergiemanagerApiClientAuthenticationError (401/403)

The coordinator maps them onto ConfigEntryAuthFailed and UpdateFailed; nothing else
in the integration imports this package.
"""

from .client import (
    FAN_SPEEDS,
    EnergiemanagerApiClient,
    EnergiemanagerApiClientAuthenticationError,
    EnergiemanagerApiClientCommunicationError,
    EnergiemanagerApiClientError,
)

__all__ = [
    "FAN_SPEEDS",
    "EnergiemanagerApiClient",
    "EnergiemanagerApiClientAuthenticationError",
    "EnergiemanagerApiClientCommunicationError",
    "EnergiemanagerApiClientError",
]

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from __future__ import annotations
from typing import Any
from .const import DOMAIN
from .api import MarleySpoon, ValueNotFound, AuthFailed
import logging
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

ALLOWED_REGIONS = ["nl", "de", "com"]
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("domain", default="nl"): str,
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


class MarleySpoonHub:
    def __init__(self, domain: str) -> None:
        self.domain = domain

    async def authenticate(self, username: str, password: str) -> bool:
        try:
            async with MarleySpoon(username, password, self.domain) as ms:
                user_id, api_token, api_host = await ms.login()

        except ValueNotFound:
            raise CannotConnect

        except AuthFailed:
            raise InvalidAuth

        return user_id, api_token, api_host


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    if not data["domain"] in ALLOWED_REGIONS:
        raise InvalidDomain

    hub = MarleySpoonHub(data["domain"])
    user_id, api_token, api_host = await hub.authenticate(
        data["username"], data["password"]
    )
    return {
        "title": "MarleySpoon Login",
        "user_id": user_id,
        "api_token": api_token,
        "api_host": api_host,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        try:
            info = await validate_input(self.hass, user_input)

        except CannotConnect:
            errors["base"] = "cannot_connect"

        except InvalidAuth:
            errors["base"] = "invalid_auth"

        except InvalidDomain:
            errors["base"] = "invalid_domain"

        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        else:
            entry_data = {
                "user_id": info["user_id"],
                "api_token": info["api_token"],
                "api_host": info["api_host"],
            }
            return self.async_create_entry(
                title=info["title"], data={**entry_data, **user_input}
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect"""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth"""


class InvalidDomain(HomeAssistantError):
    """Error to indicate there is no valid domain selected"""

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from datetime import timedelta
from .const import DOMAIN
from .api import MarleySpoon
import logging

SCAN_INTERVAL = timedelta(minutes=10)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    api_config = hass.data[DOMAIN][entry.entry_id]
    user_id = api_config["user_id"]
    api_token = api_config["api_token"]
    api_host = api_config["api_host"]

    async def async_update_data():
        all_orders = await MarleySpoon.orders(user_id, api_token, api_host)
        parsed_orders = []
        for index, order in enumerate(reversed(all_orders)):
            order["name"] = f"ms_order_week_{index}"
            parsed_orders.append(order)
        return parsed_orders

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()
    async_add_entities(
        OrderEntity(coordinator, idx) for idx, ent in enumerate(coordinator.data)
    )


class OrderEntity(CoordinatorEntity, Entity):
    """Representation of a MarleySpoon order"""

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.idx = idx

    @property
    def name(self):
        """Return the name of the order."""
        return f"{self.coordinator.data[self.idx]['name']}"

    @property
    def device_state_attributes(self):
        """Return the state attributes of the order."""
        entity_object = self.coordinator.data[self.idx]
        attr = {}
        attr["total_price"] = entity_object["total_price"]
        attr["status"] = entity_object["status"]
        attr["cutoff_days"] = entity_object["cutoff_days"]
        attr["days_until_cutoff"] = entity_object["days_until_cutoff"]
        attr["intended_delivery_date"] = entity_object["intended_delivery_date"]
        attr["delivery_slot"] = entity_object["delivery_slot"]
        attr["recipes"] = entity_object["recipes"]
        return attr

    @property
    def state(self):
        """Return the state of the order."""
        return self.coordinator.data[self.idx].get("state", "N/A")

    async def update(self):
        """Fetch new state data for the order."""
        await self.coordinator.async_request_refresh()

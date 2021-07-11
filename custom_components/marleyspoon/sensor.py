from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from datetime import timedelta
from .const import DOMAIN
from .api import MarleySpoonAPI
import logging

SCAN_INTERVAL = timedelta(minutes=10)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    api_config = hass.data[DOMAIN][entry.entry_id]
    user_id = api_config["user_id"]
    api_token = api_config["api_token"]
    api_host = api_config["api_host"]

    async def async_update_data():
        marley_api = MarleySpoonAPI(api_token, api_host)
        all_orders = await marley_api.orders(user_id)
        parsed_orders = []
        parsed_recipes = []

        for index, order in enumerate(reversed(all_orders)):
            order["name"] = f"ms_order_week_{index}"
            parsed_orders.append(order)

        for index, recipe in enumerate(parsed_orders[0]["recipes"]):
            recipe_details = await marley_api.recipe(recipe["id"])
            parsed_recipes.append(
                {
                    "name": f"ms_order_0_recipe_{index}",
                    "title": recipe["name"],
                    "subtitle": recipe["subtitle"],
                    "quantity": recipe["quantity"],
                    "id": recipe["id"],
                    "meal_type": recipe["meal_type"],
                    "image": recipe["image"]["small"],
                    "calories": recipe_details["calories"],
                    "difficulty": recipe_details["difficulty"],
                    "preparation_time": recipe_details["preparation_time"],
                    "meal_attributes": recipe_details["meal_attributes"],
                    "nutrition": recipe_details["nutrition"],
                    "additional_allergens": recipe_details["additional_allergens"],
                    "steps": recipe_details["steps"],
                    "ingredients": recipe_details["ingredients"],
                    "assumed_ingredients": recipe_details["assumed_ingredients"],
                    "assumed_cooking_utilities": recipe_details[
                        "assumed_cooking_utilities"
                    ],
                    "cooking_tip": recipe_details["cooking_tip"],
                }
            )
        return {"orders": parsed_orders, "recipes": parsed_recipes}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=1200),
    )

    await coordinator.async_config_entry_first_refresh()
    async_add_entities(
        OrderEntity(coordinator, idx)
        for idx, ent in enumerate(coordinator.data["orders"])
    )
    async_add_entities(
        RecipeEntity(coordinator, idx)
        for idx, ent in enumerate(coordinator.data["recipes"])
    )


class RecipeEntity(CoordinatorEntity, Entity):
    """Representation of a MarleySpoon Recipe"""

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.idx = idx

    @property
    def name(self):
        """Return the name of the recipe."""
        return f"{self.coordinator.data['recipes'][self.idx]['name']}"

    @property
    def device_state_attributes(self):
        """Return the state attributes of the recipe."""
        entity_object = self.coordinator.data["recipes"][self.idx]
        attr = {}
        attr["id"] = entity_object["id"]
        attr["title"] = entity_object["title"]
        attr["subtitle"] = entity_object["subtitle"]
        attr["image"] = entity_object["image"]
        attr["quantity"] = entity_object["quantity"]
        attr["meal_type"] = entity_object["meal_type"]
        attr["calories"] = entity_object["calories"]
        attr["difficulty"] = entity_object["difficulty"]
        attr["preparation_time"] = entity_object["preparation_time"]
        attr["nutrition"] = entity_object["nutrition"]
        attr["additional_allergens"] = entity_object["additional_allergens"]
        attr["steps"] = entity_object["steps"]
        attr["ingredients"] = entity_object["ingredients"]
        attr["assumed_ingredients"] = entity_object["assumed_ingredients"]
        attr["assumed_cooking_utilities"] = entity_object["assumed_cooking_utilities"]
        attr["cooking_tip"] = entity_object["cooking_tip"]
        return attr

    @property
    def state(self):
        """Return the state of the recipe."""
        return self.coordinator.data["recipes"][self.idx].get("state", "N/A")

    async def update(self):
        """Fetch new state data for the order."""
        await self.coordinator.async_request_refresh()


class OrderEntity(CoordinatorEntity, Entity):
    """Representation of a MarleySpoon order"""

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.idx = idx

    @property
    def name(self):
        """Return the name of the order."""
        return f"{self.coordinator.data['orders'][self.idx]['name']}"

    @property
    def device_state_attributes(self):
        """Return the state attributes of the order."""
        entity_object = self.coordinator.data["orders"][self.idx]
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
        return self.coordinator.data["orders"][self.idx].get("state", "N/A")

    async def update(self):
        """Fetch new state data for the order."""
        await self.coordinator.async_request_refresh()

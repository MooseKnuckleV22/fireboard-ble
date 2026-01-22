"""Config flow for FireBoard BLE integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_SERIAL, CONF_ENABLE_MQTT

_LOGGER = logging.getLogger(__name__)

# The FireBoard Service UUID we are looking for
FIREBOARD_SERVICE_UUID = "c2f780ec-45e1-452b-a879-327e3140d1f1"

class FireboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FireBoard BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth auto-discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        
        self._discovery_info = discovery_info
        
        name = discovery_info.name
        if not name or name == "Unknown":
            name = f"FireBoard {discovery_info.address}"
            
        self.context["title_placeholders"] = {"name": name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery and ask for options."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name or self._discovery_info.address,
                data={
                    CONF_ADDRESS: self._discovery_info.address,
                    CONF_SERIAL: self._discovery_info.name,
                    CONF_ENABLE_MQTT: user_input.get(CONF_ENABLE_MQTT, False)
                },
            )

        schema = vol.Schema({
            vol.Required(CONF_ENABLE_MQTT, default=False): bool,
        })

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=schema,
            description_placeholders={"name": self._discovery_info.name}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual user entry with a smart dropdown."""
        
        # 1. SCAN FOR DEVICES
        # We look for any device that has "FireBoard" in the name 
        # OR broadcasts our specific UUID.
        current_devices = async_discovered_service_info(self.hass)
        fireboard_devices = {}
        
        for device in current_devices:
            if (
                (device.name and "fireboard" in device.name.lower()) or 
                (FIREBOARD_SERVICE_UUID in device.service_uuids)
            ):
                # Create a nice label: "FireBoard (AA:BB:CC:DD:EE:FF)"
                label = f"{device.name} ({device.address})"
                fireboard_devices[device.address] = label

        # 2. HANDLE SUBMISSION
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            
            # Find the name from our scan list
            name = fireboard_devices.get(address, f"FireBoard {address}")
            
            return self.async_create_entry(
                title=name, 
                data={
                    CONF_ADDRESS: address,
                    CONF_ENABLE_MQTT: user_input.get(CONF_ENABLE_MQTT, False)
                }
            )

        # 3. SHOW THE FORM
        if not fireboard_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                # Dropdown List instead of Text Box
                vol.Required(CONF_ADDRESS): vol.In(fireboard_devices),
                vol.Required(CONF_ENABLE_MQTT, default=False): bool,
            }),
        )
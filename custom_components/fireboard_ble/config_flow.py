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

from .const import DOMAIN, CONF_ENABLE_MQTT

_LOGGER = logging.getLogger(__name__)

class FireboardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FireBoard BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name,
                data={
                    CONF_ADDRESS: self._discovery_info.address,
                    CONF_ENABLE_MQTT: user_input.get(CONF_ENABLE_MQTT, False),
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self._discovery_info.name},
            data_schema=vol.Schema({
                vol.Optional(CONF_ENABLE_MQTT, default=False): bool
            }),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered devices."""
        errors = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            
            return self.async_create_entry(
                title=f"FireBoard {address}",
                data={
                    CONF_ADDRESS: address,
                    CONF_ENABLE_MQTT: user_input.get(CONF_ENABLE_MQTT, False),
                },
            )

        # 1. SCAN FOR DEVICES
        current_addresses = self._async_current_ids()
        discovered_devices = {}
        
        for service_info in async_discovered_service_info(self.hass):
            if service_info.address in current_addresses:
                continue
                
            # Match by UUID OR by Name (More robust)
            if (
                "c2f780ec-45e1-452b-a879-327e3140d1f1" in service_info.service_uuids
                or "FireBoard" in service_info.name
                or "FireBoard" in service_info.advertisement.local_name
            ):
                discovered_devices[service_info.address] = (
                    f"{service_info.name} ({service_info.address})"
                )

        # 2. LOGIC: IF FOUND -> DROPDOWN. IF NOT -> TEXT BOX.
        if discovered_devices:
            return self.async_show_form(
                step_id="user",
                errors=errors,
                data_schema=vol.Schema({
                    vol.Required(CONF_ADDRESS): vol.In(discovered_devices),
                    vol.Optional(CONF_ENABLE_MQTT, default=False): bool,
                }),
            )
        
        # FAILSAFE: Manual Entry
        return self.async_show_form(
            step_id="user",
            errors=errors,
            description_placeholders={"error_info": "No devices found. Enter MAC Manually."},
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS): str,
                vol.Optional(CONF_ENABLE_MQTT, default=False): bool,
            }),
        )
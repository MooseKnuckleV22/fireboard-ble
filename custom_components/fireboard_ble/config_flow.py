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

FIREBOARD_UUID = "c2f780ec-45e1-452b-a879-327e3140d1f1"

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

        # --- NEW NAMING LOGIC FOR 1.4.7.1 ---
        # We calculate the friendly name here so the Discovery Tile 
        # shows "FireBoard-9F:3E" instead of "fireboard_ble"
        address = discovery_info.address
        mac_parts = address.split(":")
        if len(mac_parts) == 6:
            suffix = f"{mac_parts[-2]}:{mac_parts[-1]}"
        else:
            suffix = address[-5:]
        
        friendly_name = f"FireBoard-{suffix}"
        
        # This tells HA to use this name in the Dashboard Tile title
        self.context["title_placeholders"] = {"name": friendly_name}
        # ------------------------------------

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        # Recalculate name for the entry title
        address = self._discovery_info.address
        mac_parts = address.split(":")
        if len(mac_parts) == 6:
            suffix = f"{mac_parts[-2]}:{mac_parts[-1]}"
        else:
            suffix = address[-5:]
        friendly_name = f"FireBoard-{suffix}"

        if user_input is not None:
            return self.async_create_entry(
                title=friendly_name,
                data={
                    CONF_ADDRESS: self._discovery_info.address,
                    CONF_ENABLE_MQTT: user_input.get(CONF_ENABLE_MQTT, False),
                },
            )

        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": friendly_name},
            data_schema=vol.Schema({
                vol.Optional(CONF_ENABLE_MQTT, default=False): bool
            }),
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered devices."""
        errors = {}

        # 1. If user has selected a device (or entered manual ID), create entry
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            
            # Formatting name for Manual/Dropdown Entry
            mac_parts = address.split(":")
            if len(mac_parts) == 6:
                suffix = f"{mac_parts[-2]}:{mac_parts[-1]}"
            else:
                suffix = address[-5:]
            friendly_name = f"FireBoard-{suffix}"
            
            return self.async_create_entry(
                title=friendly_name,
                data={
                    CONF_ADDRESS: address,
                    CONF_ENABLE_MQTT: user_input.get(CONF_ENABLE_MQTT, False),
                },
            )

        # 2. Scan for devices
        current_addresses = self._async_current_ids()
        discovered_devices = {}
        
        for service_info in async_discovered_service_info(self.hass):
            if service_info.address in current_addresses:
                continue
            
            # Robust Filtering: Check UUID or Name (Case Insensitive)
            dev_name = (service_info.name or "").lower()
            local_name = (service_info.advertisement.local_name or "").lower()
            has_uuid = FIREBOARD_UUID in service_info.service_uuids
            
            if has_uuid or "fireboard" in dev_name or "fireboard" in local_name:
                discovered_devices[service_info.address] = (
                    f"{service_info.name} ({service_info.address})"
                )

        # 3. Show Form
        # If no devices found, we allow manual entry (standard HA behavior)
        if not discovered_devices:
            return self.async_show_form(
                step_id="user",
                errors={"base": "no_devices_found"},
                data_schema=vol.Schema({
                    vol.Required(CONF_ADDRESS): str,
                    vol.Optional(CONF_ENABLE_MQTT, default=False): bool,
                }),
            )

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema({
                vol.Required(CONF_ADDRESS): vol.In(discovered_devices),
                vol.Optional(CONF_ENABLE_MQTT, default=False): bool,
            }),
        )
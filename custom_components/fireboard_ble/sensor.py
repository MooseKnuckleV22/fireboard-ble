"""Support for FireBoard BLE sensors (v1.4.8)."""
from __future__ import annotations

import logging
import asyncio
import json
import time
from datetime import timedelta

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_register_callback,
    BluetoothCallbackMatcher,
    BluetoothScanningMode,
    BluetoothChange
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er
from homeassistant.const import (
    UnitOfTemperature, 
    CONF_ADDRESS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN, 
    DATA_CHARACTERISTIC_UUID, 
    CONTROL_CHARACTERISTIC_UUID,
    CONF_SERIAL,
    CONF_ENABLE_MQTT 
)

_LOGGER = logging.getLogger(__name__)

# FINAL TIMEOUT: 30 seconds
TIMEOUT_SECONDS = 30

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FireBoard BLE sensors."""
    address = entry.data[CONF_ADDRESS]
    
    # STARTUP CLEANUP (Thread-Safe)
    try:
        registry = er.async_get(hass)
        entries = [
            e for e in registry.entities.values() 
            if e.config_entry_id == entry.entry_id
        ]
        for entity in entries:
            if "_ch" in entity.unique_id:
                registry.async_remove(entity.entity_id)
    except Exception as e:
        _LOGGER.warning(f"[FireBoard] Cleanup warning: {e}")

    enable_mqtt = entry.data.get(CONF_ENABLE_MQTT, False)
    
    try:
        mac_parts = address.split(":")
        if len(mac_parts) == 6:
            suffix = f"{mac_parts[-2]}:{mac_parts[-1]}"
        else:
            suffix = address[-5:]
        device_name = f"FireBoard-{suffix}"
        mqtt_base_topic = f"FireBoard-BLE-{suffix}"
    except Exception:
        device_name = f"FireBoard-{address}"
        mqtt_base_topic = f"FireBoard-BLE-{address}"

    hub = FireboardHub(hass, entry, address, device_name, enable_mqtt, mqtt_base_topic, async_add_entities)
    
    entities = []
    entities.append(FireboardRSSISensor(hub))
    entities.append(FireboardStatusSensor(hub))
    entities.append(FireboardSourceSensor(hub))
    
    async_add_entities(entities)
    
    entry.async_create_background_task(hass, hub.start(), "fireboard_loop")
    entry.async_on_unload(hub.stop)
    
    # Watchdog runs every 10 seconds
    entry.async_on_unload(
        async_track_time_interval(hass, hub.check_stale_sensors, timedelta(seconds=10))
    )

class FireboardHub:
    """Manages connection, dynamic sensors, and MQTT."""
    def __init__(self, hass, entry, mac, device_name, enable_mqtt, mqtt_base_topic, add_entities_callback):
        self.hass = hass
        self.entry = entry
        self.mac = mac
        self.device_name = device_name
        self.add_entities_callback = add_entities_callback
        self.enable_mqtt = enable_mqtt
        self.mqtt_base_topic = mqtt_base_topic
        
        self.client = None
        self.sensors = {} 
        self.rssi_sensor = None
        self.status_sensor = None
        self.source_sensor = None 
        self._running = True
        self._cancel_callback = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.mac)},
            name=self.device_name,
            manufacturer="FireBoard Labs",
            model=self.mac,
            configuration_url="https://www.fireboard.com"
        )

    def register_rssi_sensor(self, sensor_entity): self.rssi_sensor = sensor_entity
    def register_status_sensor(self, sensor_entity): self.status_sensor = sensor_entity
    def register_source_sensor(self, sensor_entity): self.source_sensor = sensor_entity

    def stop(self):
        self._running = False
        if self._cancel_callback:
            self._cancel_callback()

    def update_status(self, status):
        if self.status_sensor: self.status_sensor.update_status(status)

    async def check_stale_sensors(self, now=None):
        """The Cleaner: Runs on Main Event Loop (Thread-Safe)."""
        current_time = time.time()
        to_remove = []

        for channel, sensor in self.sensors.items():
            age = current_time - sensor.last_update
            if age > TIMEOUT_SECONDS:
                to_remove.append(channel)
        
        for channel in to_remove:
            _LOGGER.warning(f"[FireBoard] Probe {channel} TIMEOUT (> {TIMEOUT_SECONDS}s). REMOVING.")
            sensor = self.sensors.pop(channel)
            
            try:
                # 1. Update state to unavailable FIRST
                sensor.mark_unavailable()
                
                # 2. Force remove from registry
                registry = er.async_get(self.hass)
                if sensor.registry_entry:
                    registry.async_remove(sensor.entity_id)
                else:
                    await sensor.async_remove()
                    
            except Exception as e:
                _LOGGER.error(f"[FireBoard] Removal Error: {e}")

    async def remove_sensor_immediate(self, channel):
        if channel in self.sensors:
            _LOGGER.warning(f"[FireBoard] Probe {channel} Unplugged (0 received). Removing.")
            sensor = self.sensors.pop(channel)
            try:
                 registry = er.async_get(self.hass)
                 if sensor.registry_entry:
                     registry.async_remove(sensor.entity_id)
                 else:
                     await sensor.async_remove()
            except Exception:
                await sensor.async_remove()

    @callback
    def _handle_bluetooth_event(self, service_info, change: BluetoothChange):
        if self.rssi_sensor and service_info.rssi != -100:
            self.rssi_sensor.update_rssi(service_info.rssi)
        
        if self.source_sensor:
            self.source_sensor.update_source(service_info.source)

    async def start(self):
        self._cancel_callback = async_register_callback(
            self.hass,
            self._handle_bluetooth_event,
            BluetoothCallbackMatcher(address=self.mac),
            BluetoothScanningMode.ACTIVE
        )

        while self._running:
            self.client = None
            
            device = async_ble_device_from_address(self.hass, self.mac, connectable=True)
            if not device:
                self.update_status("Scanning...")
                await asyncio.sleep(5)
                continue

            self.update_status("Connecting")
            try:
                self.client = await establish_connection(
                    BleakClient, 
                    device, 
                    self.mac, 
                    disconnected_callback=self._on_disconnect,
                    use_services_cache=True,
                )
                self.update_status("Authenticating")
                
                await self.client.start_notify(DATA_CHARACTERISTIC_UUID, self._handle_notification)
                await self.client.write_gatt_char(CONTROL_CHARACTERISTIC_UUID, b'\x01')
                
                self.update_status("Connected")
                _LOGGER.info(f"[FireBoard] Successfully connected to {self.mac}")
                
                while self._running and self.client and self.client.is_connected:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                error_text = str(e)
                if "connection slot" in error_text or "No backend" in error_text:
                    _LOGGER.error(f"[FireBoard] PROXY FULL: Waiting 60s.")
                    self.update_status("Proxy Full (Waiting 60s)")
                    await asyncio.sleep(60) 
                else:
                    _LOGGER.warning(f"[FireBoard] Connection failed: {error_text}")
                    self.update_status("Retrying (15s)...")
                    await asyncio.sleep(15) 
            
            if self.client:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
                self.client = None

    def _on_disconnect(self, client):
        self.update_status("Disconnected")
        _LOGGER.warning("[FireBoard] Device Disconnected.")

    def _handle_notification(self, sender, data):
        try:
            text = data.decode("utf-8")
            json_data = json.loads(text)
            
            channel = json_data.get("channel")
            temp = json_data.get("temp")
            device_date = json_data.get("date", "Unknown")
            degreetype = json_data.get("degreetype", 2)
            
            if channel:
                if temp is None or temp <= 0:
                    if channel in self.sensors:
                        self.hass.async_create_task(self.remove_sensor_immediate(channel))
                
                elif channel in self.sensors:
                    self.sensors[channel].update_temp(temp, degreetype, device_date)
                else:
                    _LOGGER.info(f"[FireBoard] New probe detected on Channel {channel}.")
                    new_sensor = FireboardProbeSensor(self, channel)
                    self.sensors[channel] = new_sensor
                    self.add_entities_callback([new_sensor])
                    new_sensor.update_temp(temp, degreetype, device_date)

            if self.enable_mqtt and self.hass.services.has_service("mqtt", "publish"):
                specific_topic = f"{self.mqtt_base_topic}/probe{channel}"
                if channel == 0: specific_topic = f"{self.mqtt_base_topic}/ambient"
                payload = str(temp)
                self.hass.create_task(
                    self.hass.services.async_call(
                        "mqtt", "publish", 
                        {"topic": specific_topic, "payload": payload, "qos": 0, "retain": False}
                    )
                )

        except Exception:
            pass

class FireboardProbeSensor(SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_has_entity_name = True
    _attr_icon = "mdi:thermometer"
    
    def __init__(self, hub, channel):
        self._hub = hub
        self._channel = channel
        self._attr_unique_id = f"fireboard_{hub.mac}_ch{channel}"
        self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
        self._attr_name = f"Probe {channel}"
        self._attr_extra_state_attributes = {}
        self._is_available = True
        self.last_update = time.time()
    
    @property
    def available(self) -> bool: return self._is_available

    @property
    def device_info(self) -> DeviceInfo:
        return self._hub.device_info

    def update_temp(self, temp, degreetype, device_date):
        if degreetype == 1:
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        else:
            self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

        self._attr_extra_state_attributes["device_time"] = device_date
        self._attr_native_value = temp
        self._is_available = True
        self.last_update = time.time()
        self.schedule_update_ha_state()
        
    def mark_unavailable(self):
        self._is_available = False
        self.schedule_update_ha_state()

class FireboardRSSISensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_has_entity_name = True
    _attr_name = "Signal Strength"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:bluetooth-audio"

    def __init__(self, hub):
        self._hub = hub
        self._attr_unique_id = f"fireboard_{hub.mac}_rssi"
        self._is_available = False 
        hub.register_rssi_sensor(self)

    @property
    def available(self) -> bool: return True

    @property
    def device_info(self) -> DeviceInfo:
        return self._hub.device_info

    def update_rssi(self, rssi):
        self._attr_native_value = rssi
        self.schedule_update_ha_state()

class FireboardStatusSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:connection"

    def __init__(self, hub):
        self._hub = hub
        self._attr_unique_id = f"fireboard_{hub.mac}_status"
        self._attr_native_value = "Initializing"
        hub.register_status_sensor(self)

    @property
    def device_info(self) -> DeviceInfo:
        return self._hub.device_info

    def update_status(self, status):
        if self._attr_native_value != status:
            self._attr_native_value = status
            self.schedule_update_ha_state()

class FireboardSourceSensor(SensorEntity):
    """Shows which Bluetooth adapter (or Proxy) is seeing the device."""
    _attr_has_entity_name = True
    _attr_name = "Connected Via"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:router-wireless"

    def __init__(self, hub):
        self._hub = hub
        self._attr_unique_id = f"fireboard_{hub.mac}_source"
        self._attr_native_value = "Unknown"
        hub.register_source_sensor(self)

    @property
    def device_info(self) -> DeviceInfo:
        return self._hub.device_info

    def update_source(self, source):
        if self._attr_native_value != source:
            self._attr_native_value = source
            self.schedule_update_ha_state()
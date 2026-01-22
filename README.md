FIREBOARD BLE CUSTOM INTEGRATION
Current Version: 1.4.0
Status: Stable / Production
Last Updated: January 21, 2026

=============================================================================
PURPOSE & SCOPE
=============================================================================
The primary purpose of this integration is to enable 100% LOCAL, private, and fast temperature monitoring for FireBoard devices via Bluetooth. 

It bypasses the FireBoard Cloud API entirely, ensuring that your automations work even if your internet goes down or the FireBoard servers have an outage.

This "Local-First" approach comes with specific trade-offs:
1. LIMITED DATA: The FireBoard hardware only broadcasts real-time temperature data via Bluetooth. It does not broadcast Battery Level, Drive Fan Speed, or Session Data.
2. LIMITED CONNECTION: The device can only maintain one Bluetooth connection at a time.

If you require historical session data, battery levels, or fan control, please use the cloud-based "Fireboard2MQTT" integration available from the community, which utilizes the official FireBoard REST API.

=============================================================================
VERSION HISTORY
=============================================================================

Version 1.4.0
-------------
- ADDED: Zero-Configuration Discovery. The integration now scans for nearby FireBoards and presents a dropdown list during setup. No MAC address entry required.
- ADDED: Dynamic "Plug-and-Play" Probes. Sensors are created in Home Assistant immediately when a probe is plugged in and are removed 30 seconds after being unplugged.
- ADDED: Split MQTT Publishing. If enabled, data is published to granular topics (e.g., `.../probe1`, `.../ambient`) for easier consumption by other tools.
- ADDED: Proxy Exhaustion Handler. Intelligent back-off logic when connecting via full ESPHome proxies.

Version 1.3.0
-------------
- ADDED: Smart Units. Automatically detects if the device is set to Celsius or Fahrenheit.
- ADDED: Device Time attribute for data freshness verification.
- FIXED: Device Naming logic.

Version 1.2.0
-------------
- ADDED: Full support for ESPHome Bluetooth Proxies with automatic roaming.
- IMPROVED: Connection stability and retry logic.

Version 1.1.0
-------------
- ADDED: Config Flow support.
- REMOVED: Hardcoded dependencies.

Version 1.0.0
-------------
- Initial release. Proof of concept for local Bluetooth polling.

=============================================================================
TROUBLESHOOTING & LIMITATIONS
=============================================================================

1. THE "CONNECTION SLOT" ERROR (ESPHome Proxies)
   If you use ESPHome Bluetooth Proxies to extend range, be aware that the ESP32 hardware has a physical limit of 3 simultaneous active connections. 
   
   If your proxy is already connected to 3 other devices (e.g., SwitchBot, Toothbrush, Plant Monitor), it physically cannot connect to the FireBoard. 
   
   Fix: Add an additional Bluetooth Proxy to your network to handle the load. This integration supports "Roaming" and will automatically find the free proxy.

2. THE "ONE CONNECTION" RULE
   The FireBoard device accepts only ONE active Bluetooth connection.
   - If your phone's FireBoard app connects via Bluetooth, Home Assistant will be blocked.
   - If Home Assistant connects, your phone app will fail to connect via Bluetooth (but will still work via WiFi/Cloud).
   
   Fix: If the integration gets stuck on "Initializing" or "Retrying", turn off Bluetooth on your phone and power cycle the FireBoard unit.

3. "GHOST" SENSORS
   If you unplug a probe, the sensor should disappear from Home Assistant within 30 seconds. If it does not, check the Logs. The integration requires a running Watchdog timer (updates every 10s) to perform this cleanup.
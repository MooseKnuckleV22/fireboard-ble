# FireBoard BLE Custom Integration

**Current Version:** 1.4.4
**Status:** Stable / Production
**Last Updated:** January 22, 2026

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/MooseKnuckleV22/fireboard-ble)

---

### Purpose & Scope
The primary purpose of this integration is to enable 100% LOCAL, private, and fast temperature monitoring for FireBoard devices via Bluetooth.

It bypasses the FireBoard Cloud API entirely, ensuring that your automations work even if your internet goes down or the FireBoard servers have an outage.

This "Local-First" approach comes with specific trade-offs:
1. **Limited Data:** The FireBoard hardware only broadcasts real-time temperature data via Bluetooth. It does not broadcast Battery Level, Drive Fan Speed, or Session Data.
2. **Limited Connection:** The device can only maintain one Bluetooth connection at a time.

If you require historical session data, battery levels, or fan control, please use the cloud-based "Fireboard2MQTT" integration available from the community, which utilizes the official FireBoard REST API.

---

### Version History

**Version 1.4.4**
* **IMPROVED:** Discovery logic is now case-insensitive, ensuring devices broadcasting "fireboard" (lowercase) or other variations are correctly detected in the setup list.

**Version 1.4.3**
* **FIXED:** Resolved "500 Internal Server Error" crash during setup caused by nearby Bluetooth devices broadcasting without a name.

**Version 1.4.2**
* **ADDED:** Failsafe Manual Entry. If the automatic Bluetooth scan fails to find a device, the setup screen now provides a text box to manually enter the MAC address.
* **IMPROVED:** Enhanced Discovery Logic. The scanner now searches for devices broadcasting the name "FireBoard" in addition to the strict Service UUID, improving detection reliability.

**Version 1.4.1**
* **FIXED:** Added missing `config_flow: true` to manifest, allowing installation via the Home Assistant UI.
* **IMPROVED:** Refined Config Flow logic for smoother Bluetooth scanning during setup.

**Version 1.4.0**
* **ADDED:** Zero-Configuration Discovery. The integration now scans for nearby FireBoards and presents a dropdown list during setup.
* **ADDED:** Dynamic "Plug-and-Play" Probes. Sensors are created in Home Assistant immediately when a probe is plugged in and are removed 30 seconds after being unplugged.
* **ADDED:** Split MQTT Publishing. If enabled, data is published to granular topics (e.g., `.../probe1`, `.../ambient`) for easier consumption by other tools.
* **ADDED:** Proxy Exhaustion Handler. Intelligent back-off logic when connecting via full ESPHome proxies.

**Version 1.3.0**
* **ADDED:** Smart Units. Automatically detects if the device is set to Celsius or Fahrenheit.
* **ADDED:** Device Time attribute for data freshness verification.
* **FIXED:** Device Naming logic.

**Version 1.2.0**
* **ADDED:** Full support for ESPHome Bluetooth Proxies with automatic roaming.
* **IMPROVED:** Connection stability and retry logic.

**Version 1.1.0**
* **ADDED:** Config Flow support.
* **REMOVED:** Hardcoded dependencies.

**Version 1.0.0**
* Initial release. Proof of concept for local Bluetooth polling.
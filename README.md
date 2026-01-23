# FireBoard BLE Integration for Home Assistant

**Monitor your FireBoard thermometer locally, privately, and instantly.**

This Custom Integration connects your **FireBoard** meat thermometer directly to **Home Assistant** using Bluetooth (BLE). It is completely **Local-First**, meaning it works 100% offline. No cloud account, no API keys, and no internet connection required.

Whether you are smoking a brisket in the backyard or monitoring a sous vide station, this integration ensures your temperature data stays private and your automations run instantly—even if your internet goes down.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/MooseKnuckleV22/fireboard-ble)

---

### 🚀 Why Go Local? (Cloud vs. Bluetooth)

**1. No API Limits**
The official FireBoard Cloud API limits users to **200 requests per hour**. This restricts other integrations (like *Fireboard2MQTT*) to updating your temperature data only once every **20-40 seconds**.
* **FireBoard BLE:** Zero limits. We listen to the Bluetooth advertisements directly, giving you **real-time updates** (often every 3-5 seconds) as fast as the device broadcasts them.

**2. Instant Automations**
Because we don't wait for a cloud polling interval, your automations run instantly.
* *Example:* If your smoker spikes in temperature due to a grease fire, Home Assistant will know immediately—not 40 seconds later when it's too late.

**3. Privacy & Stability**
Your data never leaves your house. If your internet goes down during a long cook, your local dashboard and alerts keep working perfectly.

---

### ✅ Supported Devices
This integration works with any FireBoard device that broadcasts temperature data via Bluetooth Low Energy (BLE), including:
* **FireBoard 2** (Drive & Pro)
* **FireBoard Spark**
* **FireBoard 1** (Original)
* *Any other FireBoard model broadcasting standard BLE advertisements*

---

### ⚡ Key Features
* **100% Local Control:** Bypasses the FireBoard Cloud API entirely.
* **Auto-Discovery:** Automatically detects FireBoard devices nearby for "Plug-and-Play" setup.
* **Plug-and-Play Probes:** Sensors are created dynamically when you plug in a probe and cleaned up automatically when unplugged.
* **Smart Units:** Automatically detects if your device is set to Fahrenheit or Celsius.
* **ESPHome Ready:** Fully supports ESPHome Bluetooth Proxies to extend your range to the backyard or patio.

---

### 📡 MQTT Forwarding (Optional)
This integration includes an advanced feature to forward raw temperature data directly to your MQTT broker. This is useful if you want to ingest the data into other systems (like Node-RED or a custom dashboard) without relying on Home Assistant entities.

* **How to Enable:** Check the "Enable MQTT Publishing" box during device setup.
* **Topic Format:** `FireBoard-BLE-{MAC_SUFFIX}/{channel}`
    * Example Ambient: `FireBoard-BLE-9F:3E/ambient`
    * Example Probe 1: `FireBoard-BLE-9F:3E/probe1`
* **Payload:** Raw numeric temperature value (e.g., `225.5`).

---

### 🔎 Pre-Installation Checklist
Before installing, ensure your FireBoard is visible to Home Assistant:

1.  **Check for Visibility:** Ensure your Home Assistant host (or ESPHome Proxy) is within range of the FireBoard.
    * *Tip:* If the Auto-Discovery tile does not appear, you can verify visibility by checking the **Bluetooth** integration in Home Assistant to see if it lists the device in the "Recently Seen" or debug logs.
2.  **Free up the Connection:** The FireBoard can only talk to **one** Bluetooth device at a time.
    * **The "Bluetooth Icon" Test:** Open the official FireBoard app on your phone. Look at the dashboard status icons (WiFi, Battery, etc.).
    * ❌ **If you see a Bluetooth symbol:** Your phone is holding the connection. Home Assistant **cannot** connect. **Turn off your phone's Bluetooth** to release the device.
    * ✅ **If the Bluetooth symbol is missing (WiFi only):** The connection slot is free, and Home Assistant can grab it.

---

### Installation

**Method 1: HACS (Recommended)**
1. Open HACS in Home Assistant.
2. Click **Integrations** > **Three Dots (Top Right)** > **Custom Repositories**.
3. Add URL: `https://github.com/MooseKnuckleV22/fireboard-ble`
4. Category: **Integration**.
5. Click **Add**, then search for "FireBoard BLE" and install.
6. Restart Home Assistant.

**Method 2: Manual**
1. Copy the `custom_components/fireboard_ble` folder to your HA config directory.
2. Restart Home Assistant.

---

### Scope & Limitations
This integration follows a "Local-First" philosophy. It reads exactly what the device broadcasts over the air.
* **Data:** It provides Real-Time Temperatures, Signal Strength, and Connection Diagnostics.
* **Missing Data:** The FireBoard hardware *does not* broadcast Battery Level, Fan Speed, or Session History via Bluetooth.
* **Single Connection:** As mentioned above, if you connect with this integration, the official FireBoard app will not be able to connect via Bluetooth (but will still work via WiFi).

If you absolutely need Fan Control or Battery data, please use the cloud-based **[Fireboard2MQTT](https://github.com/gordlea/fireboard2mqtt)** integration, which uses the official REST API (subject to the 200 req/hr limit).

---

### Troubleshooting

#### 1. Device Not Found / Stuck on "Initializing"
* **Check the App:** Open the official FireBoard app. If you see the **Bluetooth Icon**, your phone is "hogging" the connection. Turn off Bluetooth on your phone and restart the FireBoard integration in Home Assistant.
* **Check Range:** Ensure the device is within 10-15 feet of your HA host or Proxy.

#### 2. The "Connection Slot" Error (ESPHome Proxies)
ESPHome Proxies have a physical limit of 3 simultaneous active connections. If your proxy is busy with other devices (SwitchBot, Toothbrush, etc.), it cannot connect to the FireBoard.
* **Fix:** Add an additional Bluetooth Proxy to your network. This integration supports "Roaming" and will automatically find the free proxy.

#### 3. "Ghost" Sensors
If you unplug a probe, the sensor should disappear from Home Assistant within 30 seconds. If it does not, check your logs to ensure the Watchdog timer is running.

---

### Version History

**Version 1.4.8.1**
* **FIXED:** Configuration Dialog Text. Switched translation method to `translations/en.json` ensuring the "Enable MQTT" option is properly capitalized and the description text appears correctly for all users.

**Version 1.4.8**
* **IMPROVED:** Device Info Page. The device model field now displays the full MAC address for easier identification. Added a direct "Visit Device" link to the FireBoard website.
* **POLISHED:** Config Flow. Improved text and descriptions for the "Enable MQTT" option to clarify its advanced usage.

**Version 1.4.7.1**
* **IMPROVED:** Discovery Tile Naming. The Home Assistant discovery tile will now explicitly name the device found (e.g., `FireBoard-9F:3E`) instead of showing the generic integration ID.

**Version 1.4.7**
* **RESTORED:** Native Auto-Discovery. Updated logic to include devices broadcasting as `FIREBOARD` (all caps), `fireboard` (lowercase), or `FireBoard` (mixed case).
* **IMPROVED:** Renamed the Diagnostic Sensor to **"Connected Via"**. Clearly indicates which device (e.g., `local` Raspberry Pi or `esphome-proxy-kitchen`) is bridging the connection.

**Version 1.4.6**
* **ADDED:** Diagnostic Sensor backend support.

**Version 1.4.5**
* **IMPROVED:** Discovery logic is now case-insensitive.

**Version 1.4.4**
* **FIXED:** Resolved "500 Internal Server Error" crash during setup caused by nearby Bluetooth devices broadcasting without a name.

**Version 1.4.3**
* **ADDED:** Failsafe Manual Entry.
* **IMPROVED:** Enhanced Discovery Logic.

**Version 1.4.2**
* **FIXED:** Added missing `config_flow: true` to manifest.

**Version 1.4.1**
* **IMPROVED:** Refined Config Flow logic.

**Version 1.4.0**
* **ADDED:** Zero-Configuration Discovery & Dynamic Probes.
* **ADDED:** Split MQTT Publishing & Proxy Exhaustion Handling.

**Version 1.3.0**
* **ADDED:** Smart Units (F/C detection) & Device Time.

**Version 1.2.0**
* **ADDED:** Full support for ESPHome Bluetooth Proxies.

**Version 1.0.0**
* Initial release.

---

### 💡 Cook Book: Automation Examples
Because this integration provides **real-time** data, you can create safety and convenience automations that react instantly.

<details>
<summary><strong>Click to expand Automation YAML examples</strong></summary>

#### 1. The "Grease Fire" Alarm (Flare-Up Detection)
*Why this works:* If your pit temperature spikes suddenly, you need to know **now**, not in 45 seconds.

```yaml
alias: "BBQ: Critical Flare-Up Warning"
description: "Flash kitchen lights RED if smoker temp jumps above 400°F"
trigger:
  - platform: numeric_state
    entity_id: sensor.fireboard_ambient
    above: 400
action:
  - service: light.turn_on
    target:
      entity_id: light.kitchen_lights
    data:
      color_name: "red"
      flash: "long"
  - service: tts.google_translate_say
    entity_id: media_player.living_room_speaker
    data:
      message: "Warning! The smoker temperature is critically high. Check for fire."
```

#### 2. The "Stall" Buster (Voice Announcement)
*Why this works:* Uses Home Assistant's trend logic to detect when your brisket stops rising.

```yaml
alias: "BBQ: Meat Stall Detected"
description: "Announce when meat temperature hasn't risen for 30 minutes"
trigger:
  - platform: state
    entity_id: binary_sensor.brisket_rising_trend
    to: "off"
    for: "00:30:00"
action:
  - service: notify.mobile_app_iphone
    data:
      message: "The brisket has hit the stall at {{ states('sensor.fireboard_probe_1') }}°. Time to wrap?"
  - service: tts.cloud_say
    entity_id: media_player.kitchen_echo
    data:
      message: "Attention. The brisket has stalled. You might want to check the fire."
```

#### 3. The "Dinner's Ready" Broadcast
*Why this works:* Perfect timing for serving steaks.

```yaml
alias: "BBQ: Steak is Medium Rare"
trigger:
  - platform: numeric_state
    entity_id: sensor.fireboard_probe_1
    above: 130
action:
  - service: media_player.play_media
    target:
      entity_id: media_player.whole_house
    data:
      media_content_id: "[http://homeassistant.local:8123/local/dinner_bell.mp3](http://homeassistant.local:8123/local/dinner_bell.mp3)"
      media_content_type: "music"
  - service: notify.alexa_media
    data:
      message: "The steaks have reached 130 degrees. Please remove them from the grill."
      target: media_player.patio_dot
```

</details>
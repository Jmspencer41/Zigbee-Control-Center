---
marp: true
backgroundImage: url('images/CircuitBoard-LtGrey-Wide.jpg')
---
<style>
h1, h2, h3, h4, h5, h6 {
  text-align: center;
}
</style>

# Smart Home Control Center
## CSC 494 Project - Progress Update
### Spring 2026

---

# Project Overview

This project creates a **local, self-hosted smart home control center** using a Raspberry Pi and ESP32-C6 with Zigbee protocol for reliable, cloud-independent home automation.

### Key Advantages
- ✅ **Local Control** - No cloud dependency
- ✅ **Unified Interface** - Single control point
- ✅ **Low-Power Mesh** - Preserves WiFi bandwidth
- ✅ **Open Source** - Full control over your data

---

# Core Technologies

- **Raspberry Pi 4** - Main hardware platform
- **Python 3** - Application logic
- **PyQt6** - Local graphical interface
- **pigpio** - GPIO and I2C communication
- **ESP-IDF** - ESP32 firmware framework
- **Zigbee Protocol** - Low-power mesh networking
- **ESP32-C6** - Zigbee coordinator hardware

---

# Hardware Components

| Component | Purpose | Interface | Status |
|-----------|---------|-----------|--------|
| Raspberry Pi 4 | Control Center | - | ✅ Ready |
| SHT41 | Temp/Humidity | I2C | ✅ Working |
| LD2410C | Presence Detection | UART | 🔄 In Progress |
| ESP32-C6 | Zigbee Coordinator | Serial | ⏳ Setup Phase |
| Pi Camera v2 | Visual Monitoring | CSI | ⏳ Planned |
| End Devices | Smart Controls | Zigbee | ⏳ Planned |

---

# Sprint 1: Raspberry Pi Sensor Interface
## Duration: 5 Weeks | Status: ✅ COMPLETE

### Deliverables Completed
- ✅ Python3 application on Raspberry Pi OS
- ✅ PyQt6-based graphical user interface
- ✅ SHT41 temperature/humidity sensor integration
- ✅ Real-time sensor data display
- ✅ Multi-threaded sensor reading with QThread
- ✅ Local data storage capability

### Success Criteria Met
- ✅ All implemented sensors provide accurate readings
- ✅ GUI displays sensor data clearly in real-time
- ✅ Application runs stably on Raspberry Pi OS
- ✅ Responsive UI with no freezing during sensor reads

---

# Sprint 1: Key Achievements

### Technical Accomplishments
- **PyQt6 GUI Framework** - Responsive main window with data display
- **SHT41 Integration** - Full I2C communication with CRC validation
- **Threading Model** - Asynchronous sensor reading prevents UI blocking
- **Error Handling** - Graceful failure modes for sensor disconnection
- **Library Integration** - Successfully combined pigpio, PyQt6, and serial communication

### Time Investment & Learning
> This sprint took longer than expected due to the learning curve of PyQt6 and embedded systems libraries, but a strong, stable foundation is now in place for future development.

**Key Skills Developed:**
- PyQt6 signal/slot architecture
- I2C protocol implementation
- GPIO and UART configuration
- Python threading and QThread
- CRC checksum validation

---

# Sprint 1: Current Capabilities

### ✅ What Works Now
- Real-time temperature and humidity display
- Sensor data updates every configurable interval
- Clean, responsive graphical interface
- Multi-threaded architecture prevents UI freezing
- Stable long-term operation


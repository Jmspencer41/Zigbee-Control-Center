# Zigbee-Control-Center

This project aims to create a local, self-hosted smart home control center using a Raspberry Pi and ESP32-C6. The system will leverage Zigbee protocol to provide reliable, cloud-independent home automation with unified control.

## Project Description

This project aims to create a local, self-hosted smart home control center using a Raspberry Pi and ESP32-C6. The system will leverage Zigbee protocol to provide reliable, cloud-independent home automation with unified control.

A **local, unified Zigbee control center** that operates independently of cloud services, consolidates device control, and uses dedicated low-power mesh networking to preserve WiFi bandwidth.


## Problem Domain
### Critical Issues with Current Smart Home Devices

1. **Cloud Dependency**

2. **Poor Integration**

3. **App Dependencies**

4. **WiFi Bandwidth Saturation**

## Features & Requirements

A **local, unified Zigbee control center** that operates independently of cloud services, consolidates device control, and uses dedicated low-power mesh networking to preserve WiFi bandwidth.

### Core Technologies

- **Raspberry Pi OS** - Primary operating system
- **Python 3** - Application logic and sensor management
- **TKinter** - Local graphical user interface
- **ESP-IDF** - ESP32 firmware development framework
- **VS Code** - Development environment
- **Zigbee Protocol** - Low-power mesh networking
- **ESP32-C6** - Zigbee coordinator hardware
- **Raspberry Pi 4** - Hardware

## Architecture

<center>
<img src="images/diagram.png" width=750>
</center>


## Schedule & Milestones
### Sprint 1: Raspberry Pi Sensor Interface Development

**Duration:** 5 Weeks
**Goal:** Create functional local control interface with integrated sensors

**Deliverables:**
- Python3 application running on Raspberry Pi OS
- TKinter-based graphical user interface
- Integration of three sensor systems:
  - **DHT22** - Temperature and humidity monitoring
  - **LD2410C** - Presence detection
  - **Pi Camera Module v2** - Visual monitoring (WNYHRI 9132664)
- Real-time sensor data display
- Local data logging capabilities

**Success Criteria:**
- All sensors provide accurate real-time readings
- GUI displays all sensor data clearly
- Application runs stably on Raspberry Pi OS
- Proper sensor calibration
- Error handling for sensor disconnections
- Responsive UI updates



## Raspberry Pi Requiresments:
  - PyQt6
    - sudo apt 
  

  - DHT22 Info:
    - https://medium.com/@zordakal171/dht-22-interfacing-in-raspberry-pi-without-using-library-7ca61e8af4b8
---
marp: true
theme: default
style: |
  section {
    background-color: #1a1a2e;
    color: #eaeaea;
  }
  h1 {
    color: #00d4ff;
    font-size: 2.5em;
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  }
  h2 {
    color: #00d4ff;
    font-size: 2em;
    border-bottom: 3px solid #00d4ff;
    padding-bottom: 10px;
  }
  h3 {
    color: #ffd700;
    font-size: 1.5em;
  }
  li {
    font-size: 1.2em;
    margin: 10px 0;
  }
  code {
    background-color: #16213e;
    padding: 2px 6px;
    border-radius: 4px;
    color: #00ff88;
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
paginate: true
---

# Raspberry Pi IoT Gateway Controller Center

### MQTT-Based Smart Home Automation System
(Originally Zigbee)

CSC 494 - Final Project Presentation

---

## Problem Statement

### Initial Challenge: Zigbee Gateway Control
- **Goal**: Create a centralized control system for Zigbee IoT devices
- **Requirements**:
  - Monitor and control multiple connected devices
  - Real-time sensor data collection (temperature, humidity, presence detection)
  - User-friendly graphical interface for Raspberry Pi
  - Network management and device pairing capabilities

---

### Key Constraints
- Time limitations for project completion
- Hardware compatibility issues with Zigbee libraries
- Extensive Code required for Zigbee 
- Need for rapid prototyping and iteration

---

## Solution: MQTT-Based Architecture

### Why MQTT Over Zigbee?
- **Faster Implementation**: MQTT protocol is more straightforward to integrate
- **Flexibility**: Decoupled messaging allows easier device management
- **Scalability**: Can easily extend to include new IoT devices and sensors
- **Proven Reliability**: Widely used in production IoT systems
- **Development Speed**: Leverages existing MQTT broker infrastructure

---

### Core Functionality
- MQTT broker communication for device messaging
- Real-time temperature and humidity monitoring via SHT41 sensor
- Presence detection via LD2410C radar sensor
- User interface for device control and monitoring
- Network status management and device discovery

---

## Technology Stack

### Backend Components
- **Language**: Python 3
- **MQTT**: Eclipse Mosquitto Broker
- **Threading**: Multi-threaded architecture for concurrent operations
- **Sensors**: 
  - SHT41 (Temperature/Humidity via I2C)

---

### Frontend Components
- **GUI Framework**: PyQt6
- **Design Pattern**: MVC (Model-View-Controller)
- **Styling**: Custom theme system with responsive layouts

---

### Hardware
- **Platform**: Raspberry Pi (4GB+ RAM recommended) x2
- **Connectivity**: Ethernet/WiFi for MQTT communication
- **I/O Interfaces**: GPIO, I2C, Serial UART
- SHT41 Sensor
- SG 90 Servo

---

## GUI Components

### Main Window Interface
- **Full-screen PyQt6 application** optimized for Raspberry Pi touchscreen
- **Top-layer control buttons** for quick access to functions
- **Dynamic status indicators** for network connectivity
- **Responsive layout** adapting to screen resolution

---


### Key UI Panels
1. **Device Panel**: Lists and controls all connected IoT devices
2. **Environment Panel**: Displays real-time sensor readings
   - Temperature and humidity from SHT41
   - Presence detection status
   - Light control interface
3. **Network Status Widget**: Shows gateway connection and coordination status
4. **Status Panel**: Overall system health and device count

---


### Dialog Interfaces
- **Configure Gateway Dialog**: Zero-config ESP32 setup
- **Device Dialog**: Individual device information and control
- **Pair Devices Dialog**: Add new devices to network
- **Settings Dialog**: User preferences and configurations
- **Logs Dialog**: System event history

---

## Core Components Deep Dive

### Device Manager (`device_manager.py`)
- **Responsibilities**:
  - Manages device lifecycle (add, remove, update)
  - Coordinates communication between GUI and hardware
  - Emits Qt signals for UI synchronization
  - Handles sensor data collection and updates

---

### MQTT Manager (`mqtt_manager.py`)
- **Functionality**:
  - Connection management to MQTT broker
  - Message parsing and routing
  - Topic subscription and publishing
  - Reconnection logic with exponential backoff

---

### Sensor Integration
- **SHT41 Temperature/Humidity Sensor**:
  - I2C communication (Address: 0x44)
  - High-precision measurements every 15 seconds
  - Threaded updates via Qt signals

---

## Implementation Progress

### Completed Features ✓
- **MQTT Architecture**:
  - Broker connection and message handling
  - Device discovery and registration
  - Real-time state synchronization
  
---

- **GUI Framework**:
  - Main window with full-screen support
  - Responsive panel layouts
  - Dialog system for device management
  - Theme customization with dark mode

---

- **Sensor Integration**:
  - SHT41 driver implementation
  - Temperature/humidity data collection
  - Real-time sensor display in UI

---

- **Device Management**:
  - Device model and state tracking
  - Signal-based architecture for loose coupling
  - Network status monitoring

---

## Challenges & Solutions

### Challenge 1: PyQt6 Cross-Platform GUI Development
**Problem**: Creating responsive UI for different screen sizes
**Solution**: Implemented dynamic layout scaling based on screen geometry
```python
height = screen.geometry().height()
titleSize = int(height * 0.04)
spacingSize = int(height * 0.03)
```

---

### Challenge 2: Sensor Integration Complexity
**Problem**: Multiple communication protocols (I2C, Serial, MQTT)
**Solution**: Abstracted through driver classes and threaded architecture
- Separate threads for sensor polling
- Signal-based event propagation
- Non-blocking UI updates

---

### Challenge 3: Zigbee to MQTT Transition
**Problem**: Initial Zigbee-based approach faced library compatibility and time constraints
**Solution**: Pivoted to MQTT architecture


---

## Learning with AI: Topic 1 - ZigBee and MQTT Communication Protocols
---

### What I Learned
**Comparing wireless IoT communication protocols**:
- **ZigBee Protocol**: Low-power mesh networking with complex coordinator setup and extensive library dependencies
- **MQTT Protocol**: Lightweight pub/sub messaging with simple broker architecture and minimal overhead
- **Protocol Trade-offs**: ZigBee offers direct device-to-device mesh, MQTT requires central broker but provides flexibility
- **Real-time Messaging**: Understanding topic-based subscriptions vs device-direct communication models


---
### 
**Choosing the right communication protocol is fundamentally about understanding your project constraints and timeline.** 

- Switching to MQTT for easier group efforts.


---

## Learning with AI: Topic 2 - PyQt6 GUI Building for Desktop Applications

---

### What I Learned
**Building responsive desktop GUIs with PyQt6**:
- **Layout Management**: Responsive design using dynamic calculations based on screen geometry and DPI
- **Widget Hierarchies**: Organizing complex UIs through parent-child relationships and layout nesting
- **Event-Driven Architecture**: Signals and slots for decoupled communication between UI components
- **Styling and Theming**: Custom stylesheets (QSS) for consistent dark themes and professional appearance

---

**Building production-quality GUIs requires thinking about both aesthetics and architecture.** My experience developing this Raspberry Pi control interface taught me a lot.

---

## Technical Achievements

### Code Quality & Best Practices
✓ Modular architecture with clear separation of concerns
✓ Signal-based event propagation (loose coupling)
✓ Threading for responsive UI (non-blocking operations)
✓ Configuration management system
✓ Comprehensive project structure for scalability

---

### Architecture Decisions
✓ MQTT broker for device communication
✓ PyQt6 for native desktop GUI
✓ Python for rapid development and prototyping
✓ Object-oriented design with inheritance and composition

---

### User Experience Features
✓ Full-screen interface optimized for Raspberry Pi
✓ Real-time sensor data visualization
✓ Network status monitoring
✓ Responsive touch-friendly controls
✓ Dark theme for low-light environments

---

## Project Results & Deliverables

### Working System Components
- ✓ MQTT-based device communication framework
- ✓ PyQt6 GUI with responsive design
- ✓ SHT41 temperature/humidity sensor integration
- ✓ Device manager with state synchronization
- ✓ Network status monitoring and display
- ✓ Servo End Device
---

### Code Repository Structure
- **Main application**: `main.py` entry point
- **Core modules**: 3 main managers (device, MQTT, zigbee gateway)
- **GUI components**: 15+ UI classes for panels and dialogs
- **Sensor drivers**: Modular sensor interfaces
- **Configuration**: Centralized settings management

---

## Q&A

Thank you!

**Project Repository**: 
ZIGBEE: https://github.com/Jmspencer41/Zigbee-Control-Center
MQTT: https://github.com/Jmspencer41/pi-home


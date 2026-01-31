---
marp: true
backgroundImage: url('/home/josh/Nextcloud/School/Spring_2026/CSC_494/Project/images/CircuitBoard-LtGrey-Wide.jpg')
---
<style>
h1, h2, h3, h4, h5, h6 {
  text-align: center;
}
</style>

# Project Plan Presentation
## Zigbee Control Center with Raspberry Pi & ESP32


This project aims to create a local, self-hosted smart home control center using a Raspberry Pi and ESP32-C6. The system will leverage Zigbee protocol to provide reliable, cloud-independent home automation with unified control.

---

# Critical Issues with Current Smart Home Devices

1. **Cloud Dependency**

2. **Poor Integration**

3. **App Dependencies**

4. **WiFi Bandwidth Saturation**

### My Solution

A **local, unified Zigbee control center** that operates independently of cloud services, consolidates device control, and uses dedicated low-power mesh networking to preserve WiFi bandwidth.

---
# Project Architecture

<center>
<img src="/home/josh/Nextcloud/School/Spring_2026/CSC_494/Project/images/diagram.png" width=750>
</center>

---

# Core Technologies

- **Raspberry Pi OS** - Primary operating system
- **Python 3** - Application logic and sensor management
- **TKinter** - Local graphical user interface
- **ESP-IDF** - ESP32 firmware development framework
- **VS Code** - Development environment
- **Zigbee Protocol** - Low-power mesh networking
- **ESP32-C6** - Zigbee coordinator hardware
- **Raspberry Pi 4** - Hardware
---

## Sprint Definitions

### Sprint 1: Raspberry Pi Sensor Interface Development

**Duration:** 
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
- No cloud dependencies for sensor functionality

**Technical Requirements:**
- Python libraries: RPi.GPIO, Adafruit DHT, PiCamera2, TKinter
- Proper sensor calibration
- Error handling for sensor disconnections
- Responsive UI updates (no blocking operations)

---

### Sprint 2: Zigbee Network Integration

**Duration:** TBD  
**Goal:** Establish Zigbee network communication between Pi and ESP32-C6

**Deliverables:**
- ESP32-C6 firmware using ESP-IDF
- Zigbee coordinator configuration
- Communication protocol between Raspberry Pi and ESP32
- Network discovery and device pairing functionality
- Integration of Zigbee control into TKinter interface

**Success Criteria:**
- ESP32-C6 successfully acts as Zigbee coordinator
- Raspberry Pi can send commands to ESP32
- Device discovery works reliably
- Interface displays connected Zigbee devices
- Commands execute with minimal latency (<500ms)

**Technical Requirements:**
- ESP-IDF Zigbee library implementation
- Serial or network communication protocol (Pi ↔ ESP32)
- Zigbee network formation and management
- Device pairing workflow
- Status monitoring and error reporting

---

### Sprint 3: Zigbee Device Development & Control

**Duration:** TBD  
**Goal:** Create controllable Zigbee end device(s)

**Primary Option: Smart Vent (Temperature-Controlled)**

**Deliverables:**
- Zigbee-enabled vent control device
- Servo or motor control for vent opening/closing
- Temperature-based automation logic
- Manual override controls in interface

**Vent Control Features:**
- **Manual Mode:** Open/close on demand via interface
- **Automatic Mode:** Temperature-based control
  - Set target temperature threshold
  - Close vent when temperature ≥ threshold
  - Reopen when temperature drops 5°F below threshold
  - Hysteresis prevents rapid cycling
- Real-time vent position feedback
- Safety overrides (manual always takes precedence)

**Alternative Option: LED Light Strip**
- Zigbee-controlled LED strip
- On/off control
- Brightness adjustment
- Color control (if RGB)
- Serves as simpler initial test device

**Success Criteria:**
- Device successfully joins Zigbee network
- Commands from interface control device reliably
- Automatic temperature control functions as specified
- Manual override works immediately
- Device maintains connection and responds to coordinator

**Technical Requirements:**
- Zigbee end device firmware (ESP-IDF)
- Actuator control (servo for vent or LED driver)
- Temperature threshold logic with hysteresis
- Device state persistence
- Low-power operation considerations

---

## Initial Product Backlog

### High Priority (Sprint 1-3 Scope)

- [ ] Set up Raspberry Pi development environment
- [ ] Install and configure Python 3 with required libraries
- [ ] Wire DHT22 temperature/humidity sensor
- [ ] Wire LD2410C presence sensor
- [ ] Connect Pi Camera Module v2
- [ ] Develop TKinter GUI framework
- [ ] Implement sensor data collection routines
- [ ] Create real-time data display widgets
- [ ] Add data logging functionality
- [ ] Set up ESP-IDF development environment in VS Code
- [ ] Configure ESP32-C6 as Zigbee coordinator
- [ ] Implement Pi-to-ESP32 communication protocol
- [ ] Develop Zigbee network formation code
- [ ] Create device pairing workflow
- [ ] Integrate Zigbee controls into TKinter interface
- [ ] Design smart vent hardware assembly
- [ ] Develop Zigbee end device firmware
- [ ] Implement vent servo/motor control
- [ ] Create temperature-based automation logic
- [ ] Add manual override functionality
- [ ] Test full system integration

### Medium Priority (Future Enhancements)

- [ ] Add historical data visualization (graphs/charts)
- [ ] Implement automation scheduling (time-based rules)
- [ ] Create scene/preset configurations
- [ ] Add notification system for alerts
- [ ] Develop mobile-friendly web interface
- [ ] Implement backup and restore functionality
- [ ] Create device grouping capabilities
- [ ] Add energy usage monitoring
- [ ] Implement zone-based controls

### Low Priority (Nice-to-Have Features)

- [ ] Voice control integration (local only)
- [ ] API for third-party integration
- [ ] Advanced analytics and reporting
- [ ] Multi-user access with permissions
- [ ] Integration with local weather data
- [ ] Geofencing capabilities (local network-based)
- [ ] Firmware OTA update system
- [ ] Custom automation scripting language

### Technical Debt & Infrastructure

- [ ] Comprehensive error handling across all components
- [ ] Unit testing for critical functions
- [ ] Documentation for setup and configuration
- [ ] Code refactoring for maintainability
- [ ] Security hardening (authentication, encryption)
- [ ] Performance optimization
- [ ] Resource usage monitoring
- [ ] Automated testing framework

---

## Technical Specifications

### Hardware Components

**Raspberry Pi Setup:**
- Raspberry Pi (Model TBD)
- DHT22 Temperature/Humidity Sensor
- LD2410C Presence Sensor
- Pi Camera Module v2 (Western New York Heritage Institute 9132664)
- Power supply
- microSD card with Raspberry Pi OS

**ESP32 Setup:**
- ESP32-C6 development board
- Power supply
- USB connection for programming

**Smart Vent Components (Sprint 3):**
- Servo motor or linear actuator
- Power regulation circuitry
- Mounting hardware
- Temperature sensor (if independent from DHT22)

**LED Strip Alternative (Sprint 3):**
- Addressable LED strip
- Power supply
- MOSFET or LED driver circuit

### Software Stack

**Raspberry Pi:**
- OS: Raspberry Pi OS (Debian-based)
- Language: Python 3.x
- GUI Framework: TKinter
- Sensor Libraries: Adafruit_DHT, PiCamera2, custom LD2410C library
- Communication: pySerial or socket-based protocol

**ESP32-C6:**
- Framework: ESP-IDF
- Zigbee Stack: ESP-IDF Zigbee library
- Development IDE: VS Code with PlatformIO or ESP-IDF extension

### Network Architecture

- **Control Layer:** Raspberry Pi (Python application)
- **Coordinator Layer:** ESP32-C6 (Zigbee coordinator)
- **Device Layer:** Zigbee end devices (vent, lights, etc.)
- **Protocol:** Zigbee 3.0 for mesh networking
- **Communication:** Serial (UART) or WiFi between Pi and ESP32

---

## Project Timeline

### Phase 1: Foundation (Sprint 1)
- Raspberry Pi interface development
- Sensor integration and testing
- Local control interface completion

### Phase 2: Network Infrastructure (Sprint 2)
- ESP32-C6 Zigbee coordinator setup
- Pi-ESP32 communication protocol
- Network formation and device discovery

### Phase 3: Device Development (Sprint 3)
- Zigbee end device creation
- Smart vent or LED control implementation
- Full system integration and testing

### Phase 4: Future Expansion (Post-Sprint 3)
- Additional device types
- Advanced automation features
- System refinement and optimization

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation Strategy |
|------|--------|-------------------|
| Zigbee library compatibility issues | High | Early testing, community support research, fallback to alternative libraries |
| Sensor communication failures | Medium | Robust error handling, redundant sensors, watchdog timers |
| ESP32-Pi communication latency | Medium | Optimize protocol, consider faster communication methods |
| Power stability for sensors | Low | Proper power regulation, capacitors, separate power rails |
| Zigbee mesh reliability | High | Follow best practices, proper antenna placement, network monitoring |

### Project Risks

| Risk | Impact | Mitigation Strategy |
|------|--------|-------------------|
| Scope creep | Medium | Strict sprint boundaries, backlog prioritization |
| Component availability | Low | Order early, identify alternative components |
| Learning curve (ESP-IDF) | Medium | Allocate extra time, leverage documentation and examples |
| Integration complexity | High | Incremental testing, modular architecture |

---

## Success Metrics

### Sprint 1 Success Metrics
- All three sensors operational with <5% reading error
- GUI responsive with <100ms update latency
- System uptime >99% during testing period
- User interface intuitively displays all sensor data

### Sprint 2 Success Metrics
- Zigbee network forms within 30 seconds
- Device discovery success rate >95%
- Command execution latency <500ms
- Network maintains stability for 24+ hours

### Sprint 3 Success Metrics
- Device joins network within 60 seconds
- Vent responds to commands with <2 second latency
- Temperature automation works within ±1°F accuracy
- Manual override functions immediately
- Zero missed temperature threshold events

### Overall Project Success Metrics
- Complete elimination of cloud dependency
- Single unified interface for all devices
- Zero WiFi devices added (all use Zigbee)
- System operational without internet connectivity
- Expandable to 10+ Zigbee devices without performance degradation

---

## Dependencies

### External Dependencies
- Raspberry Pi OS updates and compatibility
- ESP-IDF framework updates
- Python library availability
- Hardware component availability

### Internal Dependencies
- Sprint 2 depends on Sprint 1 (interface must exist before integration)
- Sprint 3 depends on Sprint 2 (network must exist before devices)
- Vent automation depends on temperature sensor from Sprint 1

### Knowledge Dependencies
- ESP-IDF proficiency
- Zigbee protocol understanding
- Python GUI development
- Electronic circuit design (for end devices)
- Raspberry Pi GPIO programming

---

## Resources Required

### Development Tools
- VS Code with ESP-IDF extension
- Python 3 development environment
- Git for version control
- Multimeter for hardware debugging
- Logic analyzer (optional but recommended)

### Documentation Resources
- ESP-IDF Zigbee API documentation
- Raspberry Pi GPIO pinout reference
- Sensor datasheets (DHT22, LD2410C)
- Zigbee 3.0 specification
- TKinter documentation

### Hardware Tools
- Soldering iron and supplies
- Breadboard and jumper wires
- Power supply (adjustable voltage)
- USB cables for programming
- Wire strippers and cutters

---

## Next Steps

1. **Immediate Actions:**
   - Procure all hardware components for Sprint 1
   - Set up development environments (Raspberry Pi, VS Code, ESP-IDF)
   - Begin Sprint 1 development

2. **Sprint 1 Kickoff:**
   - Wire all sensors to Raspberry Pi
   - Initialize Git repository
   - Create basic TKinter window structure
   - Test individual sensor readings

3. **Documentation:**
   - Maintain development journal
   - Document wiring diagrams
   - Create setup instructions
   - Log issues and solutions

4. **Continuous Activities:**
   - Monitor backlog and adjust priorities
   - Research Zigbee best practices
   - Participate in relevant forums/communities
   - Plan for Sprint 2 requirements

---

## Appendix

### Glossary
- **Zigbee:** Low-power wireless mesh networking protocol
- **ESP-IDF:** Espressif IoT Development Framework for ESP32
- **Coordinator:** Central hub in a Zigbee network that manages device connections
- **End Device:** Zigbee device controlled by coordinator
- **Mesh Network:** Self-healing network where devices relay messages
- **TKinter:** Python's standard GUI toolkit

### References
- ESP32-C6 Datasheet
- Zigbee 3.0 Specification
- DHT22 Sensor Documentation
- LD2410C mmWave Radar Sensor Guide
- Raspberry Pi Camera Module v2 Documentation
- ESP-IDF Programming Guide

### Contact Information
- Project Lead: [Your Name]
- Project Start Date: January 29, 2026
- Repository: [TBD]
- Documentation Wiki: [TBD]

---

**End of Project Plan Presentation**
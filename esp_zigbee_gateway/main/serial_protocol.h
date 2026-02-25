/*
 * serial_protocol.h
 *
 * Public interface for sending JSON messages to the Raspberry Pi over serial.
 *
 * All communication from ESP32 → Pi goes through these functions.
 * Every message is a single line of JSON terminated with '\n'.
 *
 * ── MESSAGE REFERENCE ─────────────────────────────────────────────────────────
 *
 *  {"cmd":"GATEWAY_READY","pan_id":"0x1A2B","channel":13,"addr":"0x0000"}
 *  {"cmd":"NETWORK_OPEN","seconds":180}
 *  {"cmd":"NETWORK_CLOSED"}
 *  {"cmd":"DEVICE_JOINED","addr":"0x3C4D","ieee":"aa:bb:cc:dd:ee:ff:00:11"}
 *  {"cmd":"DEVICE_DESCRIPTOR","addr":"0x3C4D","endpoint":1,"clusters":[6,8,768]}
 *  {"cmd":"ATTR_REPORT","addr":"0x3C4D","endpoint":1,"cluster":6,"attr":0,"type":"bool","value":1}
 *  {"cmd":"CMD_ACK","status":"ok","detail":"network_opened"}
 *  {"cmd":"ERROR","detail":"something_went_wrong"}
 */

#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "esp_zigbee_core.h"

/* Size of the shared JSON build buffer. 1024 bytes covers all our message types. */
#define SERIAL_BUF_SIZE 1024

/*
 * serial_send_gateway_ready()
 *
 * Sent once after the Zigbee network is fully formed and open for business.
 * Reads PAN ID, channel, and coordinator address directly from the Zigbee stack.
 *
 *  PAN ID:       16-bit network identifier (like a Wi-Fi SSID but numeric).
 *  Channel:      2.4GHz channel in use (Zigbee uses channels 11–26).
 *  Short address: Coordinator is always 0x0000.
 */
void serial_send_gateway_ready(void);

/*
 * serial_send_network_open()
 *
 * Sent when the pairing window opens. Tells the Pi how many seconds it will stay open.
 */
void serial_send_network_open(uint8_t seconds);

/*
 * serial_send_network_closed()
 *
 * Sent when the pairing window closes (timed out or manually closed).
 */
void serial_send_network_closed(void);

/*
 * serial_send_device_joined()
 *
 * Sent the moment a new device announces itself on the network.
 *
 *  short_addr: 16-bit address assigned by the coordinator — used for all future commands.
 *  ieee_addr:  64-bit permanent hardware address — like a MAC address, never changes.
 */
void serial_send_device_joined(uint16_t short_addr, esp_zb_ieee_addr_t ieee_addr);

/*
 * serial_send_descriptor()
 *
 * Sent after ZDO discovery completes for a device.
 * Lists the ZCL cluster IDs the device supports on one endpoint.
 * The Pi looks up each cluster ID in CLUSTER_DEFINITIONS to learn what variables exist.
 *
 *  cluster_list:  array of 16-bit cluster IDs
 *  cluster_count: number of entries in the array
 */
void serial_send_descriptor(uint16_t short_addr, uint8_t endpoint,
                             uint16_t *cluster_list, uint8_t cluster_count);

/*
 * serial_send_attr_report()
 *
 * Sent whenever a device reports an attribute value — either spontaneously
 * (e.g., a sensor on a schedule) or in response to a READ_ATTR command.
 *
 *  type_str: ZCL data type as a string — "bool", "uint8", "uint16", "int16", "raw"
 *  value:    Raw integer value (the Pi will scale/convert it based on the cluster definition)
 */
void serial_send_attr_report(uint16_t short_addr, uint8_t endpoint,
                              uint16_t cluster_id, uint16_t attr_id,
                              const char *type_str, int32_t value);

/*
 * serial_send_ack()
 *
 * Sent in response to every Pi command to confirm receipt and execution status.
 *
 *  ok:     true if the action was successfully initiated, false on error.
 *  detail: short snake_case string describing the result (e.g., "network_opened").
 */
void serial_send_ack(bool ok, const char *detail);

/*
 * serial_send_error()
 *
 * Sent when something fails internally on the ESP32.
 */
void serial_send_error(const char *detail);

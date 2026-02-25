/*
 * zcl_handler.h
 *
 * Public interface for the ZCL (Zigbee Cluster Library) attribute handler.
 *
 * ── WHAT IS ZCL? ──────────────────────────────────────────────────────────────
 *
 *  ZCL is the "application layer" of Zigbee — this is where actual smart home
 *  control happens. While ZDO deals with network management and device discovery,
 *  ZCL deals with real data: temperature readings, light states, dimmer levels.
 *
 *  A ZCL "cluster" is a standardized group of related attributes and commands.
 *  For example, the On/Off cluster (0x0006) has:
 *    Attributes: on_off (bool) — is the device currently on?
 *    Commands:   On, Off, Toggle — things we can tell the device to do
 *
 *  An "attribute" is a value the device stores and we can read or write.
 *  A "command" is an action we trigger (like pressing a button remotely).
 *
 * ── WHEN THIS FIRES ───────────────────────────────────────────────────────────
 *
 *  zb_attribute_handler() is registered with the stack via:
 *    esp_zb_core_action_handler_register(zb_attribute_handler)
 *
 *  It fires for:
 *    - Attribute Reports: device pushes a value to us without us asking
 *      (e.g., a temperature sensor reports every 60 seconds)
 *    - Read Attribute Responses: device replies to our READ_ATTR command
 *
 *  In both cases, we extract the value, determine its type, and forward it
 *  to the Pi via serial_send_attr_report().
 */

#pragma once

#include "esp_err.h"
#include "esp_zigbee_core.h"

/*
 * zb_attribute_handler()
 *
 * ZCL action callback — registered with esp_zb_core_action_handler_register().
 * The Zigbee stack calls this for every incoming ZCL attribute message.
 *
 * Do NOT call this directly. Pass it to esp_zb_core_action_handler_register()
 * during initialization and the stack will call it automatically.
 *
 *  callback_id: Which type of ZCL event occurred.
 *               ESP_ZB_CORE_REPORT_ATTR_CB_ID         = unsolicited attribute report
 *               ESP_ZB_CORE_CMD_READ_ATTR_RESP_CB_ID  = response to READ_ATTR command
 *
 *  message: Void pointer — cast to the appropriate struct based on callback_id.
 *           ESP_ZB_CORE_REPORT_ATTR_CB_ID        → esp_zb_zcl_report_attr_message_t*
 *           ESP_ZB_CORE_CMD_READ_ATTR_RESP_CB_ID → esp_zb_zcl_cmd_read_attr_resp_message_t*
 */
esp_err_t zb_attribute_handler(esp_zb_core_action_callback_id_t callback_id,
                                const void *message);

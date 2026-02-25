/*
 * zdo_discovery.h
 *
 * Public interface for ZDO (Zigbee Device Object) device discovery.
 *
 * ── WHAT IS ZDO? ──────────────────────────────────────────────────────────────
 *
 *  ZDO is the "directory service" layer of Zigbee. It lets you ask a device
 *  network-management questions like:
 *    "Which endpoints do you have?"
 *    "What clusters are on endpoint 1?"
 *
 *  This is purely discovery — you learn WHAT a device can do, but you don't
 *  actually control it yet. Control happens via ZCL (see zcl_handler.h).
 *
 * ── DISCOVERY FLOW ────────────────────────────────────────────────────────────
 *
 *  When a device joins and announces itself, call query_device_descriptor().
 *  Internally this fires a two-step callback chain:
 *
 *    query_device_descriptor()
 *      └─ sends Active Endpoint Request to device
 *           └─ active_ep_cb() fires when device replies
 *                └─ sends Simple Descriptor Request for each endpoint
 *                     └─ simple_desc_cb() fires for each endpoint
 *                          └─ calls serial_send_descriptor() → Pi receives cluster list
 *
 *  After the chain completes, the Pi has enough information to render the
 *  correct UI controls for the device.
 */

#pragma once

#include <stdint.h>

/*
 * query_device_descriptor()
 *
 * Kick off the ZDO discovery chain for a newly joined device.
 * Call this from esp_zb_app_signal_handler when ESP_ZB_ZDO_SIGNAL_DEVICE_ANNCE fires.
 *
 * This function returns immediately. The actual descriptor data arrives
 * asynchronously via callbacks (active_ep_cb → simple_desc_cb), which will
 * automatically call serial_send_descriptor() when complete.
 *
 *  short_addr: The 16-bit network address from the device announce signal.
 */
void query_device_descriptor(uint16_t short_addr);

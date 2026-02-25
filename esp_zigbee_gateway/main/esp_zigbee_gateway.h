/*
 * SPDX-FileCopyrightText: 2021-2024 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: LicenseRef-Included
 *
 * esp_zigbee_gateway.h
 *
 * Central configuration header for the ESP32-C6 Zigbee coordinator.
 * This is the ONLY file you need to edit when flashing a new room unit.
 *
 * ── SETUP FOR A NEW ROOM ──────────────────────────────────────────────────────
 *
 *  1. Set GATEWAY_ROOM_NAME  to a short string identifying the room.
 *  2. Set GATEWAY_PAN_ID     to a unique 16-bit hex value for this room.
 *  3. Set GATEWAY_CHANNEL    to one of 15, 20, or 25 (see channel guide below).
 *
 *  Flash the ESP32, and that's it. Everything else is automatic.
 *
 * ── CHANNEL SELECTION GUIDE ───────────────────────────────────────────────────
 *
 *  Zigbee uses 2.4GHz channels 11–26. Three of these sit in the gaps between
 *  the most common Wi-Fi channels (1, 6, 11) and should be preferred:
 *
 *    Channel 15  →  use for Room 1   (mask: 0x00008000)
 *    Channel 20  →  use for Room 2   (mask: 0x00100000)
 *    Channel 25  →  use for Room 3   (mask: 0x02000000)
 *
 *  If you have more than 3 rooms, these are acceptable secondary choices
 *  (more Wi-Fi overlap but usually fine in practice):
 *
 *    Channel 11  →  Room 4           (mask: 0x00000800)
 *    Channel 17  →  Room 5           (mask: 0x00020000)
 *    Channel 22  →  Room 6           (mask: 0x00400000)
 *    Channel 26  →  Room 7           (mask: 0x04000000)
 *
 *  NEVER put two rooms on the same channel — they will interfere with each
 *  other even through walls.
 *
 * ── PAN ID SELECTION GUIDE ────────────────────────────────────────────────────
 *
 *  PAN ID is a 16-bit network identifier (like a Wi-Fi SSID but numeric).
 *  Rules:
 *    - Must be unique per room (two coordinators with the same PAN ID on
 *      the same channel will cause devices to join the wrong network)
 *    - Avoid 0x0000 (reserved) and 0xFFFF (broadcast address)
 *    - The suggested scheme below uses 0x1A01, 0x1A02, etc. — the 0x1A
 *      prefix is arbitrary, just a way to group your own networks together
 *
 * ═════════════════════════════════════════════════════════════════════════════
 *  EDIT THESE THREE LINES FOR EACH ROOM UNIT
 * ═════════════════════════════════════════════════════════════════════════════ */

/*
 * Human-readable name for this room.
 * Sent to the Pi in the GATEWAY_READY message so the GUI can display it.
 * Keep it short — it appears as a label on the touchscreen.
 */
#define GATEWAY_ROOM_NAME   "Living Room"

/*
 * Unique 16-bit PAN ID for this room's Zigbee network.
 * Every room unit must have a different value.
 *
 * Suggested assignments:
 *   Living Room:  0x1A01
 *   Kitchen:      0x1A02
 *   Bedroom 1:    0x1A03
 *   Bedroom 2:    0x1A04
 *   Bathroom:     0x1A05
 *   Office:       0x1A06
 *   etc.
 */
#define GATEWAY_PAN_ID      0x1A01

/*
 * Zigbee channel for this room (11–26).
 * Every room unit should use a different channel from its neighbours.
 * See the channel selection guide above.
 *
 * Suggested assignments:
 *   Living Room:  15
 *   Kitchen:      20
 *   Bedroom 1:    25
 *   Bedroom 2:    11
 *   Bathroom:     17
 *   Office:       22
 */
#define GATEWAY_CHANNEL     15

/* ═════════════════════════════════════════════════════════════════════════════
 *  DO NOT EDIT BELOW THIS LINE UNLESS YOU KNOW WHAT YOU ARE DOING
 * ═════════════════════════════════════════════════════════════════════════════ */

/*
 * Convert GATEWAY_CHANNEL (integer 11-26) to the bitmask format the
 * Zigbee stack expects. ESP_ZB_PRIMARY_CHANNEL_MASK is used in esp_zb_task()
 * to restrict the coordinator to exactly one channel.
 *
 * e.g. channel 15 → (1 << 15) → 0x00008000
 */
#define ESP_ZB_PRIMARY_CHANNEL_MASK     (1l << GATEWAY_CHANNEL)

/* ── Zigbee network configuration ────────────────────────────────────────── */

#define MAX_CHILDREN                    10      /* Max devices that can join this network */
#define INSTALLCODE_POLICY_ENABLE       false   /* Install code security — disabled for now */
#define ESP_ZB_GATEWAY_ENDPOINT         1       /* Our coordinator's endpoint number */
#define APP_PROD_CFG_CURRENT_VERSION    0x0001  /* Production config version */

/* ── Coordinator identity ─────────────────────────────────────────────────── */

/*
 * ESP_MANUFACTURER_CODE: 16-bit code assigned by the CSA to your organisation.
 * 0x131B is Espressif's code — fine to use during development.
 * If you ever certify a product, you'd register your own code at csa-iot.org.
 */
#define ESP_MANUFACTURER_CODE           0x131B

/*
 * ESP_MANUFACTURER_NAME and ESP_MODEL_IDENTIFIER are ZCL Basic cluster strings.
 * The leading \x09 / \x07 bytes are the ZCL string length prefix (required by spec).
 * CONFIG_IDF_TARGET expands to the chip name, e.g. "esp32c6".
 */
#define ESP_MANUFACTURER_NAME           "\x09""ESPRESSIF"
#define ESP_MODEL_IDENTIFIER            "\x07"CONFIG_IDF_TARGET

/* ── RCP UART pin definitions (only used if not using native radio) ────────── */

#define HOST_RX_PIN_TO_RCP_TX           4
#define HOST_TX_PIN_TO_RCP_RX           5

/* ── Coordinator config macro ─────────────────────────────────────────────── */

/*
 * ESP_ZB_ZC_CONFIG() builds the esp_zb_cfg_t struct used in esp_zb_task().
 * ZC = Zigbee Coordinator — the one and only network boss.
 */
#define ESP_ZB_ZC_CONFIG()                                                  \
    {                                                                       \
        .esp_zb_role          = ESP_ZB_DEVICE_TYPE_COORDINATOR,             \
        .install_code_policy  = INSTALLCODE_POLICY_ENABLE,                  \
        .nwk_cfg.zczr_cfg = {                                               \
            .max_children     = MAX_CHILDREN,                               \
        },                                                                  \
    }

/* ── Radio config macros ──────────────────────────────────────────────────── */

/*
 * ESP32-C6 has a native 802.15.4 radio built into the same chip.
 * CONFIG_ZB_RADIO_NATIVE should be enabled in menuconfig for the C6.
 * The UART_RCP branch is for boards where the Zigbee radio is a separate chip
 * connected via UART (e.g. ESP32 + CC2652).
 */
#if CONFIG_ZB_RADIO_NATIVE
#define ESP_ZB_DEFAULT_RADIO_CONFIG()                   \
    {                                                   \
        .radio_mode = ZB_RADIO_MODE_NATIVE,             \
    }
#else
#define ESP_ZB_DEFAULT_RADIO_CONFIG()                           \
    {                                                           \
        .radio_mode = ZB_RADIO_MODE_UART_RCP,                   \
        .radio_uart_config = {                                  \
            .port = 1,                                          \
            .uart_config = {                                    \
                .baud_rate          = 460800,                   \
                .data_bits          = UART_DATA_8_BITS,         \
                .parity             = UART_PARITY_DISABLE,      \
                .stop_bits          = UART_STOP_BITS_1,         \
                .flow_ctrl          = UART_HW_FLOWCTRL_DISABLE, \
                .rx_flow_ctrl_thresh = 0,                       \
                .source_clk         = UART_SCLK_DEFAULT,        \
            },                                                  \
            .rx_pin = HOST_RX_PIN_TO_RCP_TX,                    \
            .tx_pin = HOST_TX_PIN_TO_RCP_RX,                    \
        },                                                      \
    }
#endif

#define ESP_ZB_DEFAULT_HOST_CONFIG()                            \
    {                                                           \
        .host_connection_mode = ZB_HOST_CONNECTION_MODE_NONE,   \
    }

/* ── Required includes ────────────────────────────────────────────────────── */

#include "esp_err.h"
#include "esp_zigbee_core.h"

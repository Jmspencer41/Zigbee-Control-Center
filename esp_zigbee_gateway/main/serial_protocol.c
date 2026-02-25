/*
 * serial_protocol.c
 *
 * Implements all JSON message formatting and serial output to the Raspberry Pi.
 *
 * Design rule: serial_send_raw() is the ONLY place that actually writes to stdout.
 * All other functions in this file format a JSON string into s_serial_buf and
 * then call serial_send_raw(). This makes it easy to swap the transport later
 * (e.g., switch from USB serial to UART pins) by changing just one function.
 */

#include <stdio.h>
#include <string.h>
#include "serial_protocol.h"
#include "esp_zigbee_core.h"
#include "esp_zigbee_gateway.h"  /* For GATEWAY_ROOM_NAME, GATEWAY_PAN_ID, GATEWAY_CHANNEL */

/* ── Shared JSON build buffer ─────────────────────────────────────────────────
 * We build JSON strings here before writing to serial.
 * This is a module-level static — only code in this file can touch it directly.
 * All serial_send_*() functions write into this buffer then call serial_send_raw(). */
static char s_serial_buf[SERIAL_BUF_SIZE];

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_raw()  [PRIVATE]
 *
 * The single point of output. Writes a JSON string to stdout followed by '\n'.
 * stdout is mapped to USB Serial JTAG (or UART) by the console init code in
 * esp_zigbee_gateway.c.
 *
 * fflush() is called after every write to ensure the data is actually transmitted
 * immediately rather than sitting in a C library buffer.
 * ───────────────────────────────────────────────────────────────────────────── */
static void serial_send_raw(const char *json_str)
{
    printf("%s\n", json_str);
    fflush(stdout);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_gateway_ready()
 *
 * Reads the coordinator's own network info from the Zigbee stack and sends it.
 * Called once from esp_zb_app_signal_handler when ESP_ZB_BDB_SIGNAL_STEERING
 * fires successfully — meaning the network is formed and open for devices.
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_send_gateway_ready(void)
{
    uint16_t pan_id     = esp_zb_get_pan_id();
    uint8_t  channel    = esp_zb_get_current_channel();
    uint16_t short_addr = esp_zb_get_short_address(); /* Always 0x0000 for coordinator */

    /*
     * GATEWAY_ROOM_NAME is defined in esp_zigbee_gateway.h.
     * The Pi uses this to label the connection in the GUI and in future
     * MQTT messages to Home Assistant (topic prefix, device name, etc.)
     */
    snprintf(s_serial_buf, SERIAL_BUF_SIZE,
             "{\"cmd\":\"GATEWAY_READY\","
             "\"room\":\"%s\","
             "\"pan_id\":\"0x%04X\","
             "\"channel\":%d,"
             "\"addr\":\"0x%04X\"}",
             GATEWAY_ROOM_NAME, pan_id, channel, short_addr);

    serial_send_raw(s_serial_buf);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_network_open()
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_send_network_open(uint8_t seconds)
{
    snprintf(s_serial_buf, SERIAL_BUF_SIZE,
             "{\"cmd\":\"NETWORK_OPEN\",\"seconds\":%d}", seconds);
    serial_send_raw(s_serial_buf);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_network_closed()
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_send_network_closed(void)
{
    serial_send_raw("{\"cmd\":\"NETWORK_CLOSED\"}");
}

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_device_joined()
 *
 * IEEE address note: Zigbee stores the 64-bit IEEE address in little-endian order
 * (byte[0] is the least significant byte). We print bytes [7..0] so the output
 * matches the conventional big-endian display used by most Zigbee tools.
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_send_device_joined(uint16_t short_addr, esp_zb_ieee_addr_t ieee_addr)
{
    snprintf(s_serial_buf, SERIAL_BUF_SIZE,
             "{\"cmd\":\"DEVICE_JOINED\","
             "\"addr\":\"0x%04X\","
             "\"ieee\":\"%02x:%02x:%02x:%02x:%02x:%02x:%02x:%02x\"}",
             short_addr,
             ieee_addr[7], ieee_addr[6], ieee_addr[5], ieee_addr[4],
             ieee_addr[3], ieee_addr[2], ieee_addr[1], ieee_addr[0]);

    serial_send_raw(s_serial_buf);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_descriptor()
 *
 * Builds a JSON array of cluster IDs incrementally using an offset pointer
 * into s_serial_buf. This avoids needing a second buffer for the array.
 *
 * The (SERIAL_BUF_SIZE - 20) guard on the loop leaves room for the closing "]}"
 * even if we're near the end of the buffer.
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_send_descriptor(uint16_t short_addr, uint8_t endpoint,
                              uint16_t *cluster_list, uint8_t cluster_count)
{
    int offset = 0;

    offset += snprintf(s_serial_buf + offset, SERIAL_BUF_SIZE - offset,
                       "{\"cmd\":\"DEVICE_DESCRIPTOR\","
                       "\"addr\":\"0x%04X\","
                       "\"endpoint\":%d,"
                       "\"clusters\":[",
                       short_addr, endpoint);

    for (int i = 0; i < cluster_count && offset < SERIAL_BUF_SIZE - 20; i++) {
        if (i > 0) {
            offset += snprintf(s_serial_buf + offset, SERIAL_BUF_SIZE - offset, ",");
        }
        offset += snprintf(s_serial_buf + offset, SERIAL_BUF_SIZE - offset,
                           "%d", cluster_list[i]);
    }

    snprintf(s_serial_buf + offset, SERIAL_BUF_SIZE - offset, "]}");
    serial_send_raw(s_serial_buf);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_attr_report()
 *
 * 'value' is always sent as a plain integer. The Pi side uses the type_str
 * field and its CLUSTER_DEFINITIONS dict to interpret the raw number correctly
 * (e.g., int16 value 2150 → temperature 21.50°C after dividing by 100).
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_send_attr_report(uint16_t short_addr, uint8_t endpoint,
                               uint16_t cluster_id, uint16_t attr_id,
                               const char *type_str, int32_t value)
{
    snprintf(s_serial_buf, SERIAL_BUF_SIZE,
             "{\"cmd\":\"ATTR_REPORT\","
             "\"addr\":\"0x%04X\","
             "\"endpoint\":%d,"
             "\"cluster\":%d,"
             "\"attr\":%d,"
             "\"type\":\"%s\","
             "\"value\":%ld}",
             short_addr, endpoint, cluster_id, attr_id, type_str, (long)value);

    serial_send_raw(s_serial_buf);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_ack()
 *
 * Uses a ternary to pick "ok"/"error" string so the Pi can do a simple
 * string compare: if msg["status"] == "ok"
 *
 * detail can be NULL — we guard against that with the conditional.
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_send_ack(bool ok, const char *detail)
{
    snprintf(s_serial_buf, SERIAL_BUF_SIZE,
             "{\"cmd\":\"CMD_ACK\",\"status\":\"%s\",\"detail\":\"%s\"}",
             ok ? "ok" : "error",
             detail ? detail : "");

    serial_send_raw(s_serial_buf);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_send_error()
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_send_error(const char *detail)
{
    snprintf(s_serial_buf, SERIAL_BUF_SIZE,
             "{\"cmd\":\"ERROR\",\"detail\":\"%s\"}",
             detail ? detail : "unknown");

    serial_send_raw(s_serial_buf);
}

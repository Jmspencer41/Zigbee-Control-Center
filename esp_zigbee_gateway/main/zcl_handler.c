/*
 * zcl_handler.c
 *
 * Handles incoming ZCL attribute data from end devices.
 *
 * The core job here is type decoding: ZCL sends raw bytes with a type code,
 * and we need to read those bytes correctly and forward a named type string
 * to the Pi so it knows how to interpret the integer value.
 *
 * ── ZCL TYPE CODES ────────────────────────────────────────────────────────────
 *
 *  The Zigbee spec defines ~30 data types. We handle the most common:
 *
 *   ESP_ZB_ZCL_ATTR_TYPE_BOOL  (0x10) — 1 byte, 0x00=false, 0x01=true
 *   ESP_ZB_ZCL_ATTR_TYPE_U8   (0x20) — 1 byte unsigned, 0–255
 *   ESP_ZB_ZCL_ATTR_TYPE_U16  (0x21) — 2 byte unsigned, 0–65535
 *   ESP_ZB_ZCL_ATTR_TYPE_S16  (0x29) — 2 byte signed, used for temperature
 *                                        (raw value / 100 = degrees Celsius)
 *
 *  To add more types (e.g., U32 for energy meters), add a case to the
 *  decode_attr_value() helper in this file.
 *
 * ── SHARED DECODE LOGIC ───────────────────────────────────────────────────────
 *
 *  Both callback cases (attribute report and read response) need identical
 *  type-decoding logic. We factor this into decode_attr_value() so we
 *  don't duplicate the switch statement.
 */

#include "esp_log.h"
#include "esp_zigbee_core.h"
#include "zcl_handler.h"
#include "serial_protocol.h"

static const char *TAG = "ZCL_HANDLER";

/* ─────────────────────────────────────────────────────────────────────────────
 * decode_attr_value()  [PRIVATE HELPER]
 *
 * Reads a raw ZCL attribute value from a void* pointer.
 * Sets *type_str_out to a string name for the type.
 * Sets *value_out    to the decoded integer value.
 *
 * The void* data pointer is from the Zigbee stack — we cast it to the correct
 * type based on the ZCL type code. Getting the cast wrong (e.g., reading a
 * 2-byte value with a 1-byte cast) would produce garbage, so this table must
 * match the ZCL spec exactly.
 *
 * Returns true if the type was recognized, false for unknown types.
 * ───────────────────────────────────────────────────────────────────────────── */
static bool decode_attr_value(esp_zb_zcl_attr_type_t zcl_type,
                               const void *data_ptr,
                               const char **type_str_out,
                               int32_t     *value_out)
{
    switch (zcl_type) {

    case ESP_ZB_ZCL_ATTR_TYPE_BOOL:
        /*
         * Boolean: 1 byte. Spec says 0x00 = false, 0x01 = true.
         * We cast to uint8_t* and read the byte.
         */
        *type_str_out = "bool";
        *value_out    = *(const uint8_t *)data_ptr;
        return true;

    case ESP_ZB_ZCL_ATTR_TYPE_U8:
        /*
         * Unsigned 8-bit: 1 byte, range 0–254 (0xFF = invalid/undefined in ZCL).
         * Used for: brightness level (0–254), hue (0–254), saturation (0–254).
         */
        *type_str_out = "uint8";
        *value_out    = *(const uint8_t *)data_ptr;
        return true;

    case ESP_ZB_ZCL_ATTR_TYPE_U16:
        /*
         * Unsigned 16-bit: 2 bytes little-endian, range 0–65534.
         * Used for: color temperature in mireds (153–500 typical range).
         */
        *type_str_out = "uint16";
        *value_out    = *(const uint16_t *)data_ptr;
        return true;

    case ESP_ZB_ZCL_ATTR_TYPE_S16:
        /*
         * Signed 16-bit: 2 bytes little-endian, range -32768 to 32767.
         * Used for: temperature measurement (value / 100 = °C).
         * e.g., 0x0866 = 2150 = 21.50°C
         */
        *type_str_out = "int16";
        *value_out    = *(const int16_t *)data_ptr;
        return true;

    default:
        /*
         * Unknown type — read the first byte as a raw fallback and warn.
         * If you see "raw" coming out of the Pi, add the type here.
         * Check esp_zigbee_zcl_common.h for the full list of type constants.
         */
        ESP_LOGW(TAG, "Unhandled ZCL attr type: 0x%02X — sending first byte as raw", zcl_type);
        *type_str_out = "raw";
        *value_out    = *(const uint8_t *)data_ptr;
        return false;
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
 * zb_attribute_handler()  [PUBLIC — registered as ZCL action callback]
 *
 * Dispatches to the correct handler based on callback_id.
 *
 * The Zigbee stack passes a different struct type in 'message' for each
 * callback_id. We must cast to the right type or we'll read garbage.
 * ───────────────────────────────────────────────────────────────────────────── */
esp_err_t zb_attribute_handler(esp_zb_core_action_callback_id_t callback_id,
                                const void *message)
{
    esp_err_t ret = ESP_OK;

    switch (callback_id) {

    /* ── Case 1: Unsolicited Attribute Report ──────────────────────────────────
     *
     * A device is pushing data to us without us asking.
     * This is the normal operating mode for sensors and state-change devices:
     *   - Temperature sensor: reports every 60 seconds
     *   - Light switch:       reports immediately when physically toggled
     *   - Occupancy sensor:   reports when motion is detected/cleared
     *
     * Cast message → esp_zb_zcl_report_attr_message_t
     * ─────────────────────────────────────────────────────────────────────── */
    case ESP_ZB_CORE_REPORT_ATTR_CB_ID: {
        const esp_zb_zcl_report_attr_message_t *report =
            (const esp_zb_zcl_report_attr_message_t *)message;

        ESP_LOGI(TAG, "Attr report: src=0x%04X ep=%d cluster=0x%04X attr=0x%04X type=0x%02X",
                 report->src_address.u.short_addr,
                 report->src_endpoint,
                 report->cluster,
                 report->attribute.id,
                 report->attribute.data.type);

        const char *type_str = "unknown";
        int32_t     int_val  = 0;
        decode_attr_value(report->attribute.data.type,
                          report->attribute.data.value,
                          &type_str, &int_val);

        serial_send_attr_report(report->src_address.u.short_addr,
                                report->src_endpoint,
                                report->cluster,
                                report->attribute.id,
                                type_str,
                                int_val);
        break;
    }

    /* ── Case 2: Read Attribute Response ───────────────────────────────────────
     *
     * Response to a READ_ATTR command we sent from pi_commands.c.
     * Same data, but packaged differently:
     *   - It's a linked list of variable records (resp->variables)
     *   - Each record has its own status code (some attrs may fail individually)
     *   - We only forward records where status == SUCCESS
     *
     * Cast message → esp_zb_zcl_cmd_read_attr_resp_message_t
     * ─────────────────────────────────────────────────────────────────────── */
    case ESP_ZB_CORE_CMD_READ_ATTR_RESP_CB_ID: {
        const esp_zb_zcl_cmd_read_attr_resp_message_t *resp =
            (const esp_zb_zcl_cmd_read_attr_resp_message_t *)message;

        /*
         * Walk the linked list of attribute records in the response.
         * resp->variables points to the first node.
         * Each node has a ->next pointer; the list ends when next == NULL.
         */
        esp_zb_zcl_read_attr_resp_variable_t *var = resp->variables;
        while (var != NULL) {

            if (var->status == ESP_ZB_ZCL_STATUS_SUCCESS) {
                const char *type_str = "unknown";
                int32_t     int_val  = 0;
                decode_attr_value(var->attribute.data.type,
                                  var->attribute.data.value,
                                  &type_str, &int_val);

                serial_send_attr_report(resp->info.src_address.u.short_addr,
                                        resp->info.src_endpoint,
                                        resp->info.cluster,
                                        var->attribute.id,
                                        type_str,
                                        int_val);
            } else {
                ESP_LOGW(TAG, "Read attr response: attr 0x%04X status 0x%02X",
                         var->attribute.id, var->status);
            }

            var = var->next;
        }
        break;
    }

    default:
        /* Not every ZCL callback is handled here. Others (write responses,
           command responses) can be added as cases above when needed. */
        ESP_LOGD(TAG, "Unhandled ZCL callback ID: 0x%x", callback_id);
        break;
    }

    return ret;
}

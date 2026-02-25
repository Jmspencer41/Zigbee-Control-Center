/*
 * pi_commands.c
 *
 * Receives JSON commands from the Raspberry Pi and executes them as Zigbee operations.
 *
 * This file has two layers:
 *
 *   Layer 1 — JSON parsing utilities (json_find_value, json_get_string, json_get_int)
 *     Minimal hand-rolled parser. We don't use a JSON library to keep the binary small.
 *     Works only for our known message format — not a general-purpose parser.
 *
 *   Layer 2 — Command dispatch (process_pi_command)
 *     Reads the "cmd" field and routes to the correct Zigbee API call.
 *     All Zigbee API calls happen here (safe because this runs in the Zigbee task).
 *
 * ── MEMORY OWNERSHIP ──────────────────────────────────────────────────────────
 *
 *  cmd_queue_push() heap-allocates a copy of each command string.
 *  process_pi_command() is responsible for free()ing it before returning.
 *  This is noted at every early-return path — don't add a return without free().
 */

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "esp_log.h"
#include "esp_zigbee_core.h"
#include "pi_commands.h"
#include "serial_protocol.h"
#include "esp_zigbee_gateway.h"   /* For ESP_ZB_GATEWAY_ENDPOINT */

static const char *TAG = "PI_COMMANDS";

/* The queue handle — module-level so process_cmd_queue_alarm can access it */
static QueueHandle_t s_cmd_queue = NULL;


/* ═════════════════════════════════════════════════════════════════════════════
 * SECTION A: JSON PARSING UTILITIES
 * ═════════════════════════════════════════════════════════════════════════════ */

/*
 * json_find_value()  [PRIVATE]
 *
 * Locates the value portion of a key-value pair in a JSON string.
 * Searches for the pattern "key": and returns a pointer to the character
 * immediately after the colon (skipping any whitespace).
 *
 * Example:
 *   json    = {"cmd":"SET_ATTR","addr":"0x1A2B"}
 *   key     = "addr"
 *   returns → pointer to '"' before '0x1A2B'
 *
 * Returns NULL if the key is not found.
 * The caller reads the value from the returned pointer based on expected type.
 */
static const char *json_find_value(const char *json, const char *key)
{
    /* Pattern to search for: "key": (including the quotes around the key) */
    char pattern[64];
    snprintf(pattern, sizeof(pattern), "\"%s\":", key);

    const char *pos = strstr(json, pattern);
    if (!pos) return NULL;

    pos += strlen(pattern);

    /* Skip any whitespace between the colon and the value */
    while (*pos == ' ' || *pos == '\t') pos++;

    return pos;
}

/*
 * json_get_string()  [PRIVATE]
 *
 * Extracts a quoted string value: "key":"value" → copies value into out_buf.
 *
 * The value is everything between the first '"' after the key's ':' and
 * the next '"'. We stop at the buffer size limit to prevent overflow.
 *
 * Returns true on success, false if the key wasn't found or value isn't a string.
 */
static bool json_get_string(const char *json, const char *key,
                              char *out_buf, size_t buf_size)
{
    const char *val = json_find_value(json, key);
    if (!val || *val != '"') return false;

    val++; /* Step past the opening quote */
    size_t i = 0;
    while (*val && *val != '"' && i < buf_size - 1) {
        out_buf[i++] = *val++;
    }
    out_buf[i] = '\0';
    return true;
}

/*
 * json_get_int()  [PRIVATE]
 *
 * Extracts a numeric value: "key":42 → returns 42.
 *
 * Uses strtol with base 0, which auto-detects decimal, hex (0x prefix), and octal.
 * Returns 0 if the key is not found.
 *
 * Limitation: if 0 is a valid value, you can't distinguish "key not found" from
 * "key is 0". For our use case this is acceptable — all our zero values are valid.
 */
static int32_t json_get_int(const char *json, const char *key)
{
    const char *val = json_find_value(json, key);
    if (!val) return 0;
    return (int32_t)strtol(val, NULL, 0);
}

/*
 * parse_hex_addr()  [PRIVATE]
 *
 * Parses a hex address string like "0x1A2B" or "0x001A" into a uint16_t.
 *
 * Returns 0xFFFF on invalid input. This is safe to use as a sentinel because
 * 0xFFFF is the Zigbee broadcast address — never a valid unicast target.
 */
static uint16_t parse_hex_addr(const char *str)
{
    if (!str || str[0] == '\0') return 0xFFFF;
    uint32_t val = strtoul(str, NULL, 0); /* base 0 = auto-detect 0x prefix */
    return (uint16_t)(val & 0xFFFF);
}


/* ═════════════════════════════════════════════════════════════════════════════
 * SECTION B: COMMAND HANDLERS
 * One static function per command type. Each receives the raw JSON string,
 * extracts its parameters, calls the Zigbee API, and sends an ACK.
 * ═════════════════════════════════════════════════════════════════════════════ */

/*
 * handle_open_network()  [PRIVATE]
 *
 * {"cmd":"OPEN_NETWORK","duration":180}
 *
 * Opens the Zigbee network so new devices can join.
 * duration: seconds to stay open (1–254). 255 = open forever (use with care).
 * Default is 180 seconds (3 minutes) if duration is missing or out of range.
 */
static void handle_open_network(const char *cmd_json)
{
    int32_t duration = json_get_int(cmd_json, "duration");
    if (duration <= 0 || duration > 255) {
        duration = 180; /* 3-minute default */
    }

    esp_err_t err = esp_zb_bdb_open_network((uint8_t)duration);
    if (err == ESP_OK) {
        serial_send_network_open((uint8_t)duration);
        serial_send_ack(true, "network_opened");
    } else {
        ESP_LOGE(TAG, "esp_zb_bdb_open_network failed: %s", esp_err_to_name(err));
        serial_send_ack(false, "failed_to_open_network");
    }
}

/*
 * handle_close_network()  [PRIVATE]
 *
 * {"cmd":"CLOSE_NETWORK"}
 *
 * Immediately stops accepting new devices.
 * There's no return value from esp_zb_bdb_close_network — it always succeeds.
 */
static void handle_close_network(const char *cmd_json)
{
    (void)cmd_json; /* No parameters to read */
    esp_zb_bdb_close_network();
    serial_send_network_closed();
    serial_send_ack(true, "network_closed");
}

/*
 * handle_set_attr()  [PRIVATE]
 *
 * {"cmd":"SET_ATTR","addr":"0x1A2B","endpoint":1,"cluster":6,"attr":0,"type":"bool","value":1}
 *
 * Writes an attribute value to a device. This is how we control things:
 *   cluster=6, attr=0, type=bool, value=1  → turn light ON
 *   cluster=8, attr=0, type=uint8, value=128 → set brightness to ~50%
 *   cluster=768, attr=0, type=uint8, value=0  → set hue to red
 *
 * ── HOW ZCL WRITE ATTRIBUTE WORKS ────────────────────────────────────────────
 *
 *  esp_zb_zcl_write_attr_cmd_t bundles:
 *    - Who to send to (address + endpoint)
 *    - Which cluster and attribute
 *    - The new value (typed bytes)
 *
 *  The tricky part is the attribute value: ZCL expects the raw bytes in a
 *  specific format. We use a local variable for each type (bool_val, u8_val, etc.)
 *  and point attr_field.data.value at it.
 *
 *  WARNING: attr_field.data.value must point to valid memory when
 *  esp_zb_zcl_write_attr_cmd_req() is called. Since we call it before
 *  the function returns, local variables on the stack are fine here.
 */
static void handle_set_attr(const char *cmd_json)
{
    char addr_str[16] = {0};
    char type_str[16] = {0};

    if (!json_get_string(cmd_json, "addr", addr_str, sizeof(addr_str)) ||
        !json_get_string(cmd_json, "type", type_str, sizeof(type_str))) {
        serial_send_ack(false, "set_attr_missing_fields");
        return;
    }

    uint16_t target_addr = parse_hex_addr(addr_str);
    if (target_addr == 0xFFFF) {
        serial_send_ack(false, "set_attr_invalid_address");
        return;
    }

    uint8_t  endpoint   = (uint8_t) json_get_int(cmd_json, "endpoint");
    uint16_t cluster_id = (uint16_t)json_get_int(cmd_json, "cluster");
    uint16_t attr_id    = (uint16_t)json_get_int(cmd_json, "attr");
    int32_t  value      =           json_get_int(cmd_json, "value");

    /*
     * esp_zb_zcl_write_attr_cmd_t: ZCL Write Attribute command structure.
     *
     *  zcl_basic_cmd.dst_addr_u.addr_short: target device's 16-bit address
     *  zcl_basic_cmd.dst_endpoint:          which endpoint on the target
     *  zcl_basic_cmd.src_endpoint:          our gateway endpoint (defined in header)
     *  address_mode: ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT means "use short address + endpoint"
     *  clusterID:    which ZCL cluster to write to
     */
    esp_zb_zcl_write_attr_cmd_t write_cmd = {
        .zcl_basic_cmd = {
            .dst_addr_u.addr_short = target_addr,
            .dst_endpoint          = endpoint,
            .src_endpoint          = ESP_ZB_GATEWAY_ENDPOINT,
        },
        .address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT,
        .clusterID    = cluster_id,
    };

    /*
     * esp_zb_zcl_attribute_t: holds the attribute ID and value to write.
     * We set the ZCL type code and point data.value at a local typed variable.
     */
    esp_zb_zcl_attribute_t attr_field;
    attr_field.id = attr_id;

    /* Local storage for each possible value type.
     * Only one of these is used per call, but we declare all so the compiler
     * knows their size on the stack. */
    uint8_t  bool_val, u8_val;
    uint16_t u16_val;
    int16_t  s16_val;

    if (strcmp(type_str, "bool") == 0) {
        attr_field.data.type  = ESP_ZB_ZCL_ATTR_TYPE_BOOL;
        bool_val = (uint8_t)(value ? 1 : 0);
        attr_field.data.value = &bool_val;

    } else if (strcmp(type_str, "uint8") == 0) {
        attr_field.data.type  = ESP_ZB_ZCL_ATTR_TYPE_U8;
        u8_val = (uint8_t)(value & 0xFF);
        attr_field.data.value = &u8_val;

    } else if (strcmp(type_str, "uint16") == 0) {
        attr_field.data.type  = ESP_ZB_ZCL_ATTR_TYPE_U16;
        u16_val = (uint16_t)(value & 0xFFFF);
        attr_field.data.value = &u16_val;

    } else if (strcmp(type_str, "int16") == 0) {
        attr_field.data.type  = ESP_ZB_ZCL_ATTR_TYPE_S16;
        s16_val = (int16_t)(value & 0xFFFF);
        attr_field.data.value = &s16_val;

    } else {
        ESP_LOGW(TAG, "SET_ATTR: unknown type string '%s'", type_str);
        serial_send_ack(false, "set_attr_unknown_type");
        return;
    }

    write_cmd.attr_number = 1;
    write_cmd.attr_field  = &attr_field;

    esp_zb_zcl_write_attr_cmd_req(&write_cmd);
    serial_send_ack(true, "set_attr_sent");
}

/*
 * handle_read_attr()  [PRIVATE]
 *
 * {"cmd":"READ_ATTR","addr":"0x1A2B","endpoint":1,"cluster":6,"attr":0}
 *
 * Asks a device to report the current value of an attribute.
 * The response arrives asynchronously — the Zigbee stack will call
 * zb_attribute_handler() in zcl_handler.c with ESP_ZB_CORE_CMD_READ_ATTR_RESP_CB_ID,
 * which then calls serial_send_attr_report() to forward the value to the Pi.
 *
 * ── esp_zb_zcl_read_attr_cmd_t ────────────────────────────────────────────────
 *  attr_number: how many attributes to request in one ZCL message (we always send 1)
 *  attr_field:  pointer to an array of attribute IDs to read
 *               (we read a single uint16_t on the stack — it stays valid until the call returns)
 */
static void handle_read_attr(const char *cmd_json)
{
    char addr_str[16] = {0};

    if (!json_get_string(cmd_json, "addr", addr_str, sizeof(addr_str))) {
        serial_send_ack(false, "read_attr_missing_addr");
        return;
    }

    uint16_t target_addr = parse_hex_addr(addr_str);
    if (target_addr == 0xFFFF) {
        serial_send_ack(false, "read_attr_invalid_address");
        return;
    }

    uint8_t  endpoint   = (uint8_t) json_get_int(cmd_json, "endpoint");
    uint16_t cluster_id = (uint16_t)json_get_int(cmd_json, "cluster");
    uint16_t attr_id    = (uint16_t)json_get_int(cmd_json, "attr");

    esp_zb_zcl_read_attr_cmd_t read_cmd = {
        .zcl_basic_cmd = {
            .dst_addr_u.addr_short = target_addr,
            .dst_endpoint          = endpoint,
            .src_endpoint          = ESP_ZB_GATEWAY_ENDPOINT,
        },
        .address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT,
        .clusterID    = cluster_id,
        .attr_number  = 1,
        .attr_field   = &attr_id,
    };

    esp_zb_zcl_read_attr_cmd_req(&read_cmd);
    serial_send_ack(true, "read_attr_sent");
}


/* ═════════════════════════════════════════════════════════════════════════════
 * SECTION C: QUEUE INFRASTRUCTURE
 * ═════════════════════════════════════════════════════════════════════════════ */

/*
 * process_pi_command()  [PRIVATE]
 *
 * Parses the "cmd" field and dispatches to the matching handler above.
 * Called only from process_cmd_queue_alarm(), which runs inside the Zigbee task.
 *
 * Takes ownership of cmd_json and always frees it before returning.
 * If you add a new early-return path, make sure to call free(cmd_json) first.
 */
static void process_pi_command(char *cmd_json)
{
    char cmd_type[32] = {0};

    if (!json_get_string(cmd_json, "cmd", cmd_type, sizeof(cmd_type))) {
        ESP_LOGE(TAG, "No 'cmd' field in JSON: %s", cmd_json);
        serial_send_error("missing_cmd_field");
        free(cmd_json);
        return;
    }

    ESP_LOGI(TAG, "Executing Pi command: %s", cmd_type);

    if      (strcmp(cmd_type, "OPEN_NETWORK")  == 0) handle_open_network(cmd_json);
    else if (strcmp(cmd_type, "CLOSE_NETWORK") == 0) handle_close_network(cmd_json);
    else if (strcmp(cmd_type, "SET_ATTR")      == 0) handle_set_attr(cmd_json);
    else if (strcmp(cmd_type, "READ_ATTR")     == 0) handle_read_attr(cmd_json);
    else {
        ESP_LOGW(TAG, "Unknown command from Pi: '%s'", cmd_type);
        serial_send_error("unknown_command");
    }

    free(cmd_json); /* Always free — handlers must NOT free it themselves */
}

/*
 * process_cmd_queue_alarm()  [PRIVATE — Zigbee scheduler callback]
 *
 * Scheduled by cmd_queue_push() using esp_zb_scheduler_alarm().
 * Runs INSIDE the Zigbee task — the only safe context to call Zigbee APIs.
 *
 * Processes up to 4 commands per invocation to avoid monopolizing the stack.
 * If more commands remain, re-schedules itself for 100ms later.
 *
 * param: ignored (scheduler alarm callbacks take a uint8_t param we don't use)
 */
static void process_cmd_queue_alarm(uint8_t param)
{
    (void)param;

    char *cmd_json  = NULL;
    int   processed = 0;

    while (processed < 4 && xQueueReceive(s_cmd_queue, &cmd_json, 0) == pdTRUE) {
        process_pi_command(cmd_json); /* frees cmd_json */
        processed++;
    }

    /* If there are still commands waiting, check again in 100ms */
    if (uxQueueMessagesWaiting(s_cmd_queue) > 0) {
        esp_zb_scheduler_alarm(process_cmd_queue_alarm, 0, 100);
    }
}

/*
 * cmd_queue_init()  [PUBLIC]
 *
 * Creates the FreeRTOS queue. Call once from app_main() before task creation.
 * sizeof(char*): each slot holds a pointer to a heap-allocated string, not the string itself.
 */
QueueHandle_t cmd_queue_init(void)
{
    s_cmd_queue = xQueueCreate(CMD_QUEUE_SIZE, sizeof(char *));
    if (!s_cmd_queue) {
        ESP_LOGE(TAG, "FATAL: Failed to create command queue");
    }
    return s_cmd_queue;
}

/*
 * cmd_queue_push()  [PUBLIC]
 *
 * Called from the serial reader task (serial_reader.c) when a complete line arrives.
 *
 * We heap-allocate a copy of the line because:
 *   - line points into line_buf, which is on the serial reader task's stack
 *   - The Zigbee task will read the copy later — the stack would be invalid by then
 *   - malloc gives us memory that persists until we explicitly free() it
 *
 * If the queue is full (queue is full if 8 commands are pending), the copy is
 * immediately freed and the command is silently dropped. The Pi will notice the
 * missing ACK and can retry.
 */
void cmd_queue_push(const char *line, int line_len)
{
    char *cmd_copy = malloc(line_len + 1);
    if (!cmd_copy) {
        ESP_LOGE(TAG, "malloc failed for command copy");
        return;
    }

    memcpy(cmd_copy, line, line_len + 1); /* +1 to include null terminator */

    if (xQueueSend(s_cmd_queue, &cmd_copy, 0) != pdTRUE) {
        ESP_LOGW(TAG, "Command queue full — dropping command: %s", line);
        free(cmd_copy);
        return;
    }

    /*
     * Schedule the Zigbee task to drain the queue.
     * 50ms delay gives the Zigbee stack time to finish whatever it's doing.
     * The alarm fires process_cmd_queue_alarm() inside the Zigbee task context.
     */
    esp_zb_scheduler_alarm(process_cmd_queue_alarm, 0, 50);
}

/*
 * pi_commands.h
 *
 * Public interface for receiving and executing commands from the Raspberry Pi.
 *
 * ── THREADING PROBLEM & SOLUTION ─────────────────────────────────────────────
 *
 *  The Zigbee API functions (esp_zb_bdb_open_network, esp_zb_zcl_write_attr_cmd_req,
 *  etc.) are NOT thread-safe. They can ONLY be called from inside the Zigbee task
 *  (the task running esp_zb_stack_main_loop()).
 *
 *  But commands arrive from the serial reader task (a completely different FreeRTOS
 *  task). We can't call Zigbee APIs directly from there.
 *
 *  The solution is a two-part bridge:
 *
 *    1. serial_reader_task reads a JSON line and calls cmd_queue_push()
 *       → This puts a heap-allocated copy of the string into a FreeRTOS queue
 *       → Also schedules a Zigbee stack alarm (process_cmd_queue_alarm)
 *
 *    2. process_cmd_queue_alarm() runs INSIDE the Zigbee task (that's what
 *       esp_zb_scheduler_alarm guarantees — callbacks fire in the Zigbee context)
 *       → It dequeues and executes the commands safely
 *
 * ── COMMANDS HANDLED ──────────────────────────────────────────────────────────
 *
 *   OPEN_NETWORK  {"cmd":"OPEN_NETWORK","duration":180}
 *   CLOSE_NETWORK {"cmd":"CLOSE_NETWORK"}
 *   SET_ATTR      {"cmd":"SET_ATTR","addr":"0x1A2B","endpoint":1,"cluster":6,"attr":0,"type":"bool","value":1}
 *   READ_ATTR     {"cmd":"READ_ATTR","addr":"0x1A2B","endpoint":1,"cluster":6,"attr":0}
 */

#pragma once

#include <stdint.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"

/* Maximum length of a single JSON command line from the Pi */
#define CMD_LINE_MAX   512

/* Number of command slots in the queue before we start dropping */
#define CMD_QUEUE_SIZE 8

/*
 * cmd_queue_init()
 *
 * Creates the FreeRTOS queue used to pass commands from the serial reader
 * task to the Zigbee task. Must be called BEFORE starting either task.
 *
 * Call this from app_main() before xTaskCreate().
 * Returns the queue handle (also stored internally — callers don't need to keep it).
 */
QueueHandle_t cmd_queue_init(void);

/*
 * cmd_queue_push()
 *
 * Called from the serial reader task when a complete JSON line has been received.
 * Makes a heap-allocated copy of the line and puts it in the queue.
 * Also schedules a Zigbee task alarm to process it.
 *
 * Thread-safe: can be called from any task.
 * The heap copy is freed by process_pi_command() after the command runs.
 *
 *  line:     Null-terminated JSON string (the raw line from the Pi)
 *  line_len: Length of the string (not including null terminator)
 */
void cmd_queue_push(const char *line, int line_len);

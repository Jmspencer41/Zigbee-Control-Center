/*
 * serial_reader.h
 *
 * Public interface for the serial reader FreeRTOS task.
 *
 * This task runs forever in the background, reading characters from stdin
 * one at a time. Stdin is mapped to USB Serial JTAG (or UART) by the console
 * init code in esp_zigbee_gateway.c, so reading from stdin means reading from
 * the Raspberry Pi.
 *
 * When a complete JSON line (ending with '\n' or '\r') is assembled, it's
 * handed off to cmd_queue_push() in pi_commands.c for execution.
 *
 * ── WHY CHARACTER-BY-CHARACTER? ───────────────────────────────────────────────
 *
 *  fgets() with a blocking read would hang the task if no data arrives.
 *  Instead we use fgetc() in non-blocking mode (set in esp_zb_gateway_console_init).
 *  When there's no data, fgetc() returns EOF immediately and we yield with
 *  vTaskDelay(10ms) so other tasks can run.
 */

#pragma once

/*
 * serial_reader_task()
 *
 * FreeRTOS task entry point. Reads characters from stdin, accumulates them
 * into a line buffer, and dispatches complete lines to cmd_queue_push().
 *
 * Pass this directly to xTaskCreate() — do not call it yourself.
 *
 *   xTaskCreate(serial_reader_task, "serial_reader", 4096, NULL, 4, NULL);
 *
 * Stack size note: 4096 bytes is needed for the CMD_LINE_MAX (512 byte)
 * line buffer plus FreeRTOS task overhead.
 *
 * Priority note: Use 4 (one below the Zigbee task at 5) so the Zigbee
 * stack gets scheduling priority when both tasks are ready to run.
 *
 * pvParameters: unused.
 */
void serial_reader_task(void *pvParameters);

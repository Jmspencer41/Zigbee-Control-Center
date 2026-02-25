/*
 * serial_reader.c
 *
 * FreeRTOS task that continuously reads JSON lines from the Raspberry Pi over serial.
 *
 * This is purely an I/O task — it does NOT execute any Zigbee commands directly.
 * When a complete line arrives, it hands it to cmd_queue_push() and immediately
 * goes back to reading. The Zigbee task picks up and executes commands from the queue.
 *
 * ── LINE ASSEMBLY ─────────────────────────────────────────────────────────────
 *
 *  Characters accumulate in line_buf[] until '\n' or '\r' is seen.
 *  At that point the buffer is null-terminated and passed to cmd_queue_push().
 *  The buffer index resets to 0 for the next line.
 *
 *  If the line exceeds CMD_LINE_MAX bytes, it's silently discarded and the
 *  buffer resets. This prevents a malformed or excessively long message from
 *  blocking valid commands.
 */

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "serial_reader.h"
#include "pi_commands.h"   /* For CMD_LINE_MAX and cmd_queue_push() */

static const char *TAG = "SERIAL_READER";

/* ─────────────────────────────────────────────────────────────────────────────
 * serial_reader_task()  [PUBLIC — FreeRTOS task entry point]
 * ───────────────────────────────────────────────────────────────────────────── */
void serial_reader_task(void *pvParameters)
{
    (void)pvParameters; /* Unused */

    /*
     * line_buf: accumulates incoming characters until a newline is seen.
     * line_pos: index of the next character to write into line_buf.
     * Both are local (stack-allocated) — fine because this task never returns.
     */
    char line_buf[CMD_LINE_MAX];
    int  line_pos = 0;

    ESP_LOGI(TAG, "Serial reader started — listening for Pi commands on stdin");

    while (1) {
        /*
         * fgetc(stdin) reads one character from the serial input.
         *
         * Non-blocking mode is enabled in esp_zb_gateway_console_init()
         * via fcntl(F_SETFL, O_NONBLOCK). In non-blocking mode:
         *   - If a character is available: returns the character (0–255)
         *   - If no character is available: returns EOF (-1) immediately
         *
         * We yield for 10ms on EOF so we're not busy-spinning at 100% CPU
         * while waiting for the Pi to send something.
         */
        int c = fgetc(stdin);

        if (c == EOF || c < 0) {
            /* No data right now — yield so other tasks can run */
            vTaskDelay(pdMS_TO_TICKS(10));
            continue;
        }

        if (c == '\n' || c == '\r') {
            /*
             * End-of-line detected. If we have any content, dispatch it.
             *
             * We check line_pos > 0 to ignore blank lines (e.g., a lone '\r'
             * from Windows-style CRLF line endings after we already processed '\n').
             */
            if (line_pos > 0) {
                line_buf[line_pos] = '\0'; /* Null-terminate before passing out */

                ESP_LOGI(TAG, "Received from Pi (%d bytes): %s", line_pos, line_buf);

                /*
                 * Hand off to the command queue.
                 * cmd_queue_push() makes its own heap copy — line_buf is still ours.
                 */
                cmd_queue_push(line_buf, line_pos);

                line_pos = 0; /* Reset for next line */
            }

        } else {
            /*
             * Normal character — append to the buffer.
             *
             * We guard against (CMD_LINE_MAX - 1) to always leave room for
             * the null terminator we add above.
             */
            if (line_pos < CMD_LINE_MAX - 1) {
                line_buf[line_pos++] = (char)c;
            } else {
                /*
                 * Buffer overflow — the incoming line is longer than CMD_LINE_MAX.
                 * Discard everything accumulated so far and start fresh.
                 * The Pi will notice the missing ACK and can retry.
                 */
                ESP_LOGW(TAG, "Line too long (>%d bytes) — discarding", CMD_LINE_MAX);
                line_pos = 0;
            }
        }
    }
    /* Never reached — FreeRTOS tasks must not return */
}

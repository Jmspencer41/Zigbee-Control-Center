/*
 * esp_zigbee_gateway.c
 *
 * Top-level file for the ESP32-C6 Zigbee coordinator firmware.
 *
 * This file is intentionally kept small. Its only responsibilities are:
 *   1. app_main()              — hardware init and task creation
 *   2. esp_zb_task()           — Zigbee stack init (registers our endpoint and callbacks)
 *   3. esp_zb_app_signal_handler() — Zigbee network event state machine
 *
 * All actual logic lives in the modules it calls:
 *   serial_protocol.c  — JSON formatting and serial output to Pi
 *   zdo_discovery.c    — Device descriptor querying (what can a new device do?)
 *   zcl_handler.c      — Receiving attribute data from devices
 *   pi_commands.c      — Parsing and executing commands from the Pi
 *   serial_reader.c    — FreeRTOS task that reads from the Pi over serial
 *
 * ── ZIGBEE BOOT STATE MACHINE ─────────────────────────────────────────────────
 *
 *  First boot (factory new, NVS empty):
 *    SKIP_STARTUP → DEVICE_FIRST_START → FORMATION → STEERING → gateway_ready
 *
 *  Subsequent boots (network config saved in NVS):
 *    SKIP_STARTUP → DEVICE_REBOOT → (network restored) → open_network briefly
 *
 * ── THREADING OVERVIEW ────────────────────────────────────────────────────────
 *
 *  Two FreeRTOS tasks are created in app_main():
 *
 *    "Zigbee_main" (priority 5):
 *      Runs esp_zb_stack_main_loop() forever.
 *      All Zigbee API calls must happen in this task context.
 *      Signals arrive here via esp_zb_app_signal_handler().
 *      ZCL data arrives here via zb_attribute_handler() (registered in esp_zb_task).
 *      Pi commands arrive here via process_cmd_queue_alarm() (scheduled from serial task).
 *
 *    "serial_reader" (priority 4):
 *      Reads characters from stdin (USB serial to Pi).
 *      Pushes complete JSON lines into the command queue.
 *      Does NOT call any Zigbee APIs.
 */

#include <fcntl.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/uart.h"
#include "driver/usb_serial_jtag.h"
#include "esp_check.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "esp_event.h"
#include "esp_vfs_dev.h"
#include "esp_vfs_usb_serial_jtag.h"
#include "nvs_flash.h"
#include "esp_zigbee_gateway.h"   /* Config macros: ESP_ZB_ZC_CONFIG, channel mask, etc. */
#include "zb_config_platform.h"

/* Our own modules */
#include "serial_protocol.h"
#include "zdo_discovery.h"
#include "zcl_handler.h"
#include "pi_commands.h"
#include "serial_reader.h"

static const char *TAG = "ESP_ZB_GATEWAY";


/* ─────────────────────────────────────────────────────────────────────────────
 * bdb_start_top_level_commissioning_cb()
 *
 * Thin wrapper used with esp_zb_scheduler_alarm() for retrying network formation.
 * The scheduler alarm API requires a callback with signature (uint8_t) → void,
 * so we wrap the real call here. The mode_mask is passed as the uint8_t param.
 * ───────────────────────────────────────────────────────────────────────────── */
static void bdb_start_top_level_commissioning_cb(uint8_t mode_mask)
{
    ESP_RETURN_ON_FALSE(
        esp_zb_bdb_start_top_level_commissioning(mode_mask) == ESP_OK,
        , TAG, "Failed to start Zigbee commissioning"
    );
}


/* ─────────────────────────────────────────────────────────────────────────────
 * esp_zb_app_signal_handler()  [REQUIRED — overrides weak symbol in Zigbee lib]
 *
 * The Zigbee stack calls this for every network-level event.
 * Think of it as the main event loop for network state management.
 *
 * signal_struct contains:
 *   p_app_signal:   pointer to the signal type enum value
 *   esp_err_status: whether the event succeeded or failed
 *
 * Signal-specific parameters (device addresses, etc.) are retrieved via
 * esp_zb_app_signal_get_params(p_sg_p) — each signal has a different struct type.
 * ───────────────────────────────────────────────────────────────────────────── */
void esp_zb_app_signal_handler(esp_zb_app_signal_t *signal_struct)
{
    uint32_t                *p_sg_p     = signal_struct->p_app_signal;
    esp_err_t                err_status = signal_struct->esp_err_status;
    esp_zb_app_signal_type_t sig_type   = *p_sg_p;

    switch (sig_type) {

    case ESP_ZB_ZDO_SIGNAL_SKIP_STARTUP:
        /*
         * First signal on every boot.
         * "Skip startup" is the BDB layer telling us to kick off initialization.
         * We start the BDB initialization sequence, which then fires
         * DEVICE_FIRST_START or DEVICE_REBOOT depending on NVS contents.
         */
        ESP_LOGI(TAG, "Zigbee stack ready — starting BDB initialization");
        esp_zb_bdb_start_top_level_commissioning(ESP_ZB_BDB_MODE_INITIALIZATION);
        break;

    case ESP_ZB_BDB_SIGNAL_DEVICE_FIRST_START:
        /*
         * NVS was empty — this device has never formed a network.
         * We need to create one from scratch (NETWORK_FORMATION).
         */
    case ESP_ZB_BDB_SIGNAL_DEVICE_REBOOT:
        /*
         * NVS had a saved network config — it's been restored automatically.
         * We just need to open the network briefly so existing paired devices
         * can reconnect after our reboot.
         */
        if (err_status == ESP_OK) {
            if (esp_zb_bdb_is_factory_new()) {
                ESP_LOGI(TAG, "Factory new device — creating Zigbee network");
                esp_zb_bdb_start_top_level_commissioning(ESP_ZB_BDB_MODE_NETWORK_FORMATION);
            } else {
                ESP_LOGI(TAG, "Existing network restored (PAN: 0x%04X, Ch: %d)",
                         esp_zb_get_pan_id(), esp_zb_get_current_channel());
                esp_zb_bdb_open_network(180); /* Open 3 min for devices to rejoin */
            }
        } else {
            ESP_LOGE(TAG, "Stack init failed: %s", esp_err_to_name(err_status));
            serial_send_error("zigbee_init_failed");
        }
        break;

    case ESP_ZB_BDB_SIGNAL_FORMATION:
        /*
         * Network creation complete (or failed).
         * On success: we have a PAN. Move on to STEERING (open the network).
         * On failure: retry after 1 second via scheduler alarm.
         */
        if (err_status == ESP_OK) {
            ESP_LOGI(TAG, "Network formed: PAN=0x%04X Ch=%d Addr=0x%04X",
                     esp_zb_get_pan_id(),
                     esp_zb_get_current_channel(),
                     esp_zb_get_short_address());
            esp_zb_bdb_start_top_level_commissioning(ESP_ZB_BDB_MODE_NETWORK_STEERING);
        } else {
            ESP_LOGW(TAG, "Network formation failed (%s) — retrying in 1s",
                     esp_err_to_name(err_status));
            esp_zb_scheduler_alarm(
                (esp_zb_callback_t)bdb_start_top_level_commissioning_cb,
                ESP_ZB_BDB_MODE_NETWORK_FORMATION, 1000
            );
        }
        break;

    case ESP_ZB_BDB_SIGNAL_STEERING:
        /*
         * Steering (opening the network for joins) has started.
         * The network is now operational — tell the Pi it's ready.
         */
        if (err_status == ESP_OK) {
            ESP_LOGI(TAG, "Network steering started — gateway is ready");
            serial_send_gateway_ready();
        }
        break;

    case ESP_ZB_ZDO_SIGNAL_DEVICE_ANNCE: {
        /*
         * A device has announced itself. This fires when:
         *   a) A new device joins for the first time
         *   b) An existing device reconnects after power cycle
         *
         * esp_zb_app_signal_get_params() returns the announce parameters struct.
         * We cast to esp_zb_zdo_signal_device_annce_params_t to get the addresses.
         */
        esp_zb_zdo_signal_device_annce_params_t *annce =
            (esp_zb_zdo_signal_device_annce_params_t *)esp_zb_app_signal_get_params(p_sg_p);

        ESP_LOGI(TAG, "Device announced: short=0x%04X", annce->device_short_addr);

        /* Notify the Pi about the new device */
        serial_send_device_joined(annce->device_short_addr, annce->ieee_addr);

        /* Kick off ZDO discovery to find out what the device can do */
        query_device_descriptor(annce->device_short_addr);
        break;
    }

    case ESP_ZB_NWK_SIGNAL_PERMIT_JOIN_STATUS:
        /*
         * Fires whenever the permit-join window changes.
         * Parameter is a uint8_t: seconds remaining (0 = just closed).
         * We only notify the Pi when it fully closes (seconds == 0),
         * not on every countdown tick.
         */
        if (err_status == ESP_OK) {
            uint8_t seconds = *(uint8_t *)esp_zb_app_signal_get_params(p_sg_p);
            if (seconds == 0) {
                ESP_LOGI(TAG, "Permit join window closed");
                serial_send_network_closed();
            } else {
                ESP_LOGI(TAG, "Permit join open: %d seconds remaining", seconds);
            }
        }
        break;

    case ESP_ZB_ZDO_SIGNAL_PRODUCTION_CONFIG_READY:
        /*
         * Production config (manufacturer codes etc.) loaded from NVS.
         * Set our custom manufacturer code here.
         */
        ESP_LOGI(TAG, "Production config %s", err_status == ESP_OK ? "ready" : "not present");
        esp_zb_set_node_descriptor_manufacturer_code(ESP_MANUFACTURER_CODE);
        break;

    default:
        /* Log any unhandled signals at debug level — useful when adding new features */
        ESP_LOGD(TAG, "Unhandled signal: %s (0x%x) status: %s",
                 esp_zb_zdo_signal_to_string(sig_type), sig_type,
                 esp_err_to_name(err_status));
        break;
    }
}


/* ─────────────────────────────────────────────────────────────────────────────
 * esp_zb_task()  [FreeRTOS task — never returns]
 *
 * Initializes the Zigbee stack and hands control to the stack's main loop.
 * After esp_zb_stack_main_loop() is called, all further Zigbee activity
 * happens through callbacks (esp_zb_app_signal_handler and zb_attribute_handler).
 * ───────────────────────────────────────────────────────────────────────────── */
static void esp_zb_task(void *pvParameters)
{
    /*
     * esp_zb_cfg_t: top-level Zigbee configuration.
     * ESP_ZB_ZC_CONFIG() macro (defined in esp_zigbee_gateway.h) sets:
     *   - Device role: coordinator (ZC = Zigbee Coordinator)
     *   - Max children: 10 (adjustable in the header)
     *   - Install code policy: disabled
     */
    esp_zb_cfg_t zb_nwk_cfg = ESP_ZB_ZC_CONFIG();
    esp_zb_init(&zb_nwk_cfg);

    /*
     * Set the channel for this room unit.
     * GATEWAY_CHANNEL is defined in esp_zigbee_gateway.h and converted to a
     * bitmask by ESP_ZB_PRIMARY_CHANNEL_MASK. Each room should use a different
     * channel to avoid RF interference between neighbouring coordinators.
     *
     * Preferred channels (sit between common Wi-Fi channels 1, 6, 11):
     *   15, 20, 25
     */
    esp_zb_set_primary_network_channel_set(ESP_ZB_PRIMARY_CHANNEL_MASK);

    /*
     * Set a fixed PAN ID for this room unit.
     * GATEWAY_PAN_ID is defined in esp_zigbee_gateway.h.
     *
     * This must be called BEFORE esp_zb_start(). Setting it here ensures
     * this coordinator always uses the same PAN ID regardless of what other
     * networks are nearby, making multi-room deployments predictable.
     *
     * Note: if the device reboots and NVS already has a saved network config,
     * the stack will use the saved PAN ID. Call esp_zb_start(true) once to
     * factory-reset if you change GATEWAY_PAN_ID after initial deployment.
     */
    esp_zb_set_pan_id(GATEWAY_PAN_ID);

    ESP_LOGI(TAG, "Room: %s  |  PAN ID: 0x%04X  |  Channel: %d",
             GATEWAY_ROOM_NAME, GATEWAY_PAN_ID, GATEWAY_CHANNEL);

    /*
     * Register the coordinator's own endpoint.
     *
     * Even a gateway needs at least one endpoint to be a valid Zigbee node.
     * We use the "Remote Control" device ID since we act as a controller.
     * The Basic and Identify clusters are mandatory by the Zigbee spec.
     *
     * Profile ID 0x0104 = Home Automation.
     * Device ID  0x0006 = Remote Control.
     */
    esp_zb_ep_list_t      *ep_list      = esp_zb_ep_list_create();
    esp_zb_cluster_list_t *cluster_list = esp_zb_zcl_cluster_list_create();

    esp_zb_endpoint_config_t endpoint_config = {
        .endpoint           = ESP_ZB_GATEWAY_ENDPOINT,
        .app_profile_id     = ESP_ZB_AF_HA_PROFILE_ID,
        .app_device_id      = ESP_ZB_HA_REMOTE_CONTROL_DEVICE_ID,
        .app_device_version = 0,
    };

    /* Basic cluster — holds our manufacturer name and model identifier */
    esp_zb_attribute_list_t *basic_cluster = esp_zb_basic_cluster_create(NULL);
    esp_zb_basic_cluster_add_attr(basic_cluster,
        ESP_ZB_ZCL_ATTR_BASIC_MANUFACTURER_NAME_ID, ESP_MANUFACTURER_NAME);
    esp_zb_basic_cluster_add_attr(basic_cluster,
        ESP_ZB_ZCL_ATTR_BASIC_MODEL_IDENTIFIER_ID, ESP_MODEL_IDENTIFIER);
    esp_zb_cluster_list_add_basic_cluster(cluster_list, basic_cluster,
        ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);

    /* Identify cluster — required by spec, used for visual identification (blink) */
    esp_zb_cluster_list_add_identify_cluster(cluster_list,
        esp_zb_identify_cluster_create(NULL), ESP_ZB_ZCL_CLUSTER_SERVER_ROLE);

    esp_zb_ep_list_add_gateway_ep(ep_list, cluster_list, endpoint_config);
    esp_zb_device_register(ep_list);

    /*
     * Register the ZCL attribute handler from zcl_handler.c.
     * Without this, incoming attribute reports and read responses would be discarded.
     * The stack calls zb_attribute_handler() for every ZCL attribute message.
     */
    esp_zb_core_action_handler_register(zb_attribute_handler);

    /*
     * Start the Zigbee stack. false = preserve NVS (keep existing network config).
     * Pass true only if you want a full factory reset.
     */
    ESP_ERROR_CHECK(esp_zb_start(false));

    /* This call NEVER RETURNS. The Zigbee main loop runs here forever. */
    esp_zb_stack_main_loop();

    vTaskDelete(NULL); /* Unreachable, but good practice */
}


/* ─────────────────────────────────────────────────────────────────────────────
 * esp_zb_gateway_console_init()
 *
 * Configures the USB Serial JTAG peripheral so stdin/stdout are connected
 * to the USB cable going to the Raspberry Pi.
 *
 * Key settings:
 *   - Unbuffered stdin so characters arrive immediately (not line-buffered)
 *   - Non-blocking mode so fgetc() returns EOF instead of blocking
 *   - Line ending translation for cross-platform compatibility
 *
 * Only compiled when CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG is enabled in menuconfig.
 * ───────────────────────────────────────────────────────────────────────────── */
#if CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG
esp_err_t esp_zb_gateway_console_init(void)
{
    esp_err_t ret = ESP_OK;

    setvbuf(stdin, NULL, _IONBF, 0); /* Disable stdin buffering */

    usb_serial_jtag_vfs_set_rx_line_endings(ESP_LINE_ENDINGS_CR);
    usb_serial_jtag_vfs_set_tx_line_endings(ESP_LINE_ENDINGS_CRLF);

    /*
     * Non-blocking mode: fgetc() returns EOF immediately when no data is
     * available, rather than blocking the serial_reader_task forever.
     */
    fcntl(fileno(stdout), F_SETFL, O_NONBLOCK);
    fcntl(fileno(stdin),  F_SETFL, O_NONBLOCK);

    usb_serial_jtag_driver_config_t usb_serial_jtag_config =
        USB_SERIAL_JTAG_DRIVER_CONFIG_DEFAULT();
    ret = usb_serial_jtag_driver_install(&usb_serial_jtag_config);
    usb_serial_jtag_vfs_use_driver();
    uart_vfs_dev_register();

    return ret;
}
#endif /* CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG */


/* ─────────────────────────────────────────────────────────────────────────────
 * app_main()
 *
 * Entry point — called by ESP-IDF after hardware boot.
 * Initializes peripherals, creates the command queue, then starts both tasks.
 * ───────────────────────────────────────────────────────────────────────────── */
void app_main(void)
{
    /*
     * Zigbee platform config: tells the stack how the 802.15.4 radio is connected.
     * ESP32-C6 has a native radio (same silicon), so we use ZB_RADIO_MODE_NATIVE.
     */
    esp_zb_platform_config_t config = {
        .radio_config = ESP_ZB_DEFAULT_RADIO_CONFIG(),
        .host_config  = ESP_ZB_DEFAULT_HOST_CONFIG(),
    };
    ESP_ERROR_CHECK(esp_zb_platform_config(&config));

    /* NVS stores the Zigbee network config across reboots */
    ESP_ERROR_CHECK(nvs_flash_init());

    /* Required by ESP-IDF framework even when not using Wi-Fi */
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

#if CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG
    ESP_ERROR_CHECK(esp_zb_gateway_console_init());
#endif

    /*
     * Initialize the command queue before starting tasks.
     * Both tasks reference it — it must exist before either runs.
     */
    if (!cmd_queue_init()) {
        ESP_LOGE(TAG, "FATAL: command queue init failed");
        return;
    }

    /*
     * Serial reader task: reads from stdin, feeds the command queue.
     * Stack 4096: fits the CMD_LINE_MAX buffer + overhead.
     * Priority 4: lower than Zigbee task so the stack gets scheduling priority.
     */
    xTaskCreate(serial_reader_task, "serial_reader", 4096, NULL, 4, NULL);

    /*
     * Zigbee main task: runs the stack, processes signals and ZCL callbacks.
     * Stack 8192: the Zigbee stack itself uses significant stack space.
     * Priority 5: highest in our application.
     */
    xTaskCreate(esp_zb_task, "Zigbee_main", 8192, NULL, 5, NULL);

    ESP_LOGI(TAG, "Gateway firmware started — Zigbee stack initializing...");
}

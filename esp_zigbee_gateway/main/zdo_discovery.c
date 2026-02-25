/*
 * zdo_discovery.c
 *
 * ZDO (Zigbee Device Object) discovery chain.
 *
 * When a device joins the network, we don't yet know what it can do.
 * This file implements the two-step ZDO query that finds out:
 *
 *   Step 1 — Active Endpoint Request:
 *     We ask "which endpoint numbers do you have?"
 *     A simple bulb might reply [1]. A smart strip might reply [1, 2, 3, 4].
 *
 *   Step 2 — Simple Descriptor Request (one per endpoint):
 *     For each endpoint, we ask "what clusters live on this endpoint?"
 *     The device replies with a list of cluster IDs.
 *     A dimmable bulb on endpoint 1 might reply [0x0000, 0x0003, 0x0004, 0x0005, 0x0006, 0x0008]
 *     (Basic, Identify, Groups, Scenes, On/Off, Level Control)
 *
 * After step 2, we call serial_send_descriptor() to forward the cluster list to the Pi.
 * The Pi's CLUSTER_DEFINITIONS dict maps those IDs to human-readable variables.
 */

#include <string.h>
#include "esp_log.h"
#include "esp_zigbee_core.h"
#include "zdo_discovery.h"
#include "serial_protocol.h"

static const char *TAG = "ZDO_DISCOVERY";

/* ─────────────────────────────────────────────────────────────────────────────
 * simple_desc_cb()  [PRIVATE CALLBACK]
 *
 * Called by the Zigbee stack when a device responds to a Simple Descriptor Request.
 *
 * A Simple Descriptor contains:
 *   - endpoint number
 *   - Profile ID  (e.g., 0x0104 = Home Automation)
 *   - Device ID   (e.g., 0x0100 = On/Off Light, 0x0101 = Dimmable Light)
 *   - Server cluster list: clusters the device IMPLEMENTS (we read/control these)
 *   - Client cluster list: clusters the device USES (it sends commands to other devices)
 *
 * We only send server clusters to the Pi because those represent the device's
 * actual capabilities. Client clusters are for devices acting as controllers
 * (e.g., a Zigbee switch has On/Off as a client cluster).
 *
 * user_ctx: We packed the short_addr into this void* pointer using a cast trick.
 *           See the comment in active_ep_cb for explanation.
 * ───────────────────────────────────────────────────────────────────────────── */
static void simple_desc_cb(esp_zb_zdp_status_t status,
                            esp_zb_af_simple_desc_1_1_t *simple_desc,
                            void *user_ctx)
{
    if (status != ESP_ZB_ZDP_STATUS_SUCCESS) {
        ESP_LOGE(TAG, "Simple descriptor request failed (status: 0x%x)", status);
        serial_send_error("simple_desc_query_failed");
        return;
    }

    /* Recover the short address we smuggled through user_ctx */
    uint16_t short_addr = (uint16_t)(uintptr_t)user_ctx;

    ESP_LOGI(TAG, "Simple descriptor received for 0x%04X endpoint %d",
             short_addr, simple_desc->endpoint);
    ESP_LOGI(TAG, "  Profile ID: 0x%04X  Device ID: 0x%04X",
             simple_desc->app_profile_id, simple_desc->app_device_id);
    ESP_LOGI(TAG, "  Server clusters: %d  Client clusters: %d",
             simple_desc->app_num_in_clusters, simple_desc->app_num_out_clusters);

    /*
     * app_cluster_list is a flat array laid out as:
     *   [server_cluster_0, server_cluster_1, ..., client_cluster_0, client_cluster_1, ...]
     *
     * app_num_in_clusters  = number of server clusters (starts at index 0)
     * app_num_out_clusters = number of client clusters (starts at index app_num_in_clusters)
     *
     * We pass just the server clusters (in_clusters) to the Pi.
     */
    if (simple_desc->app_num_in_clusters > 0) {
        serial_send_descriptor(short_addr,
                               simple_desc->endpoint,
                               simple_desc->app_cluster_list,
                               simple_desc->app_num_in_clusters);
    } else {
        ESP_LOGW(TAG, "Device 0x%04X endpoint %d has no server clusters",
                 short_addr, simple_desc->endpoint);
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
 * active_ep_cb()  [PRIVATE CALLBACK]
 *
 * Called when a device responds to our Active Endpoint Request.
 * Receives the list of endpoint numbers on the device.
 * Fires a Simple Descriptor Request for each endpoint.
 *
 * Why pass short_addr through user_ctx instead of using the callback's short_addr param?
 * Because the simple_desc callback doesn't receive a short_addr parameter directly —
 * only a user_ctx void*. We need to carry the address from this callback into that one.
 *
 * The cast trick:  (void *)(uintptr_t)short_addr
 *   uint16_t → uintptr_t (widens to pointer size, no truncation on any platform)
 *   uintptr_t → void*    (standard integer-to-pointer conversion)
 * Recover with: (uint16_t)(uintptr_t)user_ctx
 *
 * This avoids heap allocation for a single integer — perfectly safe as long as
 * sizeof(uintptr_t) >= sizeof(uint16_t), which is always true.
 * ───────────────────────────────────────────────────────────────────────────── */
static void active_ep_cb(esp_zb_zdp_status_t status,
                          uint16_t short_addr,
                          uint8_t ep_count,
                          uint8_t *ep_id_list,
                          void *user_ctx)
{
    (void)user_ctx; /* Not used here — short_addr comes as a direct parameter */

    if (status != ESP_ZB_ZDP_STATUS_SUCCESS) {
        ESP_LOGE(TAG, "Active endpoint request failed for 0x%04X (status: 0x%x)",
                 short_addr, status);
        serial_send_error("active_ep_query_failed");
        return;
    }

    ESP_LOGI(TAG, "Device 0x%04X has %d endpoint(s)", short_addr, ep_count);

    /* Request a Simple Descriptor for each endpoint the device reported */
    for (int i = 0; i < ep_count; i++) {
        ESP_LOGI(TAG, "  Requesting simple descriptor for endpoint %d", ep_id_list[i]);

        /*
         * esp_zb_zdo_simple_desc_req_param_t: parameters for a Simple Descriptor Request.
         *   addr_of_interest: short address of the device to query
         *   endpoint:         which endpoint to describe
         */
        esp_zb_zdo_simple_desc_req_param_t req = {
            .addr_of_interest = short_addr,
            .endpoint         = ep_id_list[i],
        };

        /*
         * Pack the short_addr into user_ctx so simple_desc_cb can identify
         * which device responded (see comment above for the cast explanation).
         */
        esp_zb_zdo_simple_desc_req(&req, simple_desc_cb, (void *)(uintptr_t)short_addr);
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
 * query_device_descriptor()  [PUBLIC]
 *
 * Entry point for the discovery chain. Call this from the signal handler
 * when a new device announces itself (ESP_ZB_ZDO_SIGNAL_DEVICE_ANNCE).
 *
 * Sends an Active Endpoint Request to the device and returns immediately.
 * The rest of the chain runs asynchronously via callbacks.
 * ───────────────────────────────────────────────────────────────────────────── */
void query_device_descriptor(uint16_t short_addr)
{
    ESP_LOGI(TAG, "Starting descriptor query for device 0x%04X", short_addr);

    /*
     * esp_zb_zdo_active_ep_req_param_t: parameters for an Active Endpoint Request.
     *   addr_of_interest: who to ask
     */
    esp_zb_zdo_active_ep_req_param_t req = {
        .addr_of_interest = short_addr,
    };

    /*
     * Send the request. active_ep_cb will be called automatically by the
     * Zigbee stack when the device replies. NULL for user_ctx because
     * active_ep_cb receives short_addr as a direct parameter anyway.
     */
    esp_zb_zdo_active_ep_req(&req, active_ep_cb, NULL);
}

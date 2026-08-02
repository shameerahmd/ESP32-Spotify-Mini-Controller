#pragma once

#include <stdint.h>


namespace DeskSyncConfig
{
    // Wi-Fi network used by both the PC and ESP32.
    static constexpr char WIFI_SSID[] =
        "YOUR_WIFI_NAME";

    static constexpr char WIFI_PASSWORD[] =
        "YOUR_WIFI_PASSWORD";


    // Use the LAN IPv4 address of the PC running Flask.
    // Do not use 127.0.0.1 here.
    static constexpr char BRIDGE_HOST[] =
        "192.168.1.100";

    static constexpr uint16_t BRIDGE_PORT =
        5000;


    // Copy the DESKSYNC_API_KEY value from bridge/.env.
    static constexpr char API_KEY[] =
        "YOUR_DESKSYNC_API_KEY";


    static constexpr char DEVICE_NAME[] =
        "DeskSync-ESP32";


    // Connection and request timeouts.
    static constexpr unsigned long
        WIFI_TIMEOUT_MS = 20000;

    static constexpr unsigned long
        HTTP_TIMEOUT_MS = 5000;
}
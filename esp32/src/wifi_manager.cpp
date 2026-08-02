#include <Arduino.h>
#include <WiFi.h>

#include "config.h"
#include "wifi_manager.h"


namespace
{
    constexpr unsigned long
        RECONNECT_INTERVAL_MS = 10000;

    unsigned long connectionStartedAt = 0;
    unsigned long lastReconnectAttemptAt = 0;

    bool connectionAttemptActive = false;
    wl_status_t previousStatus = WL_IDLE_STATUS;


    void printStatusChange(
        wl_status_t currentStatus
    )
    {
        if (currentStatus == previousStatus)
        {
            return;
        }

        previousStatus = currentStatus;

        Serial.print(
            "Wi-Fi status changed: "
        );

        Serial.println(
            DeskSyncWiFi::statusText()
        );

        if (currentStatus == WL_CONNECTED)
        {
            Serial.print(
                "ESP32 IP address: "
            );

            Serial.println(
                WiFi.localIP()
            );

            Serial.print(
                "Signal strength: "
            );

            Serial.print(
                WiFi.RSSI()
            );

            Serial.println(" dBm");
        }
    }


    void startConnection()
    {
        Serial.println();
        Serial.print(
            "Connecting to Wi-Fi: "
        );

        Serial.println(
            DeskSyncConfig::WIFI_SSID
        );

        WiFi.mode(WIFI_STA);

        WiFi.setHostname(
            DeskSyncConfig::DEVICE_NAME
        );

        WiFi.begin(
            DeskSyncConfig::WIFI_SSID,
            DeskSyncConfig::WIFI_PASSWORD
        );

        connectionStartedAt = millis();
        lastReconnectAttemptAt = millis();

        connectionAttemptActive = true;
    }
}


namespace DeskSyncWiFi
{
    void begin()
    {
        previousStatus = WiFi.status();

        startConnection();
    }


    void update()
    {
        const wl_status_t currentStatus =
            WiFi.status();

        printStatusChange(
            currentStatus
        );

        if (currentStatus == WL_CONNECTED)
        {
            connectionAttemptActive = false;
            return;
        }

        const unsigned long now =
            millis();

        if (
            connectionAttemptActive
            && now - connectionStartedAt
                >= DeskSyncConfig::WIFI_TIMEOUT_MS
        )
        {
            Serial.println(
                "Wi-Fi connection timed out."
            );

            WiFi.disconnect();

            connectionAttemptActive = false;

            lastReconnectAttemptAt = now;
        }

        if (
            !connectionAttemptActive
            && now - lastReconnectAttemptAt
                >= RECONNECT_INTERVAL_MS
        )
        {
            Serial.println(
                "Retrying Wi-Fi connection..."
            );

            startConnection();
        }
    }


    bool isConnected()
    {
        return (
            WiFi.status()
            == WL_CONNECTED
        );
    }


    String ipAddress()
    {
        if (!isConnected())
        {
            return "0.0.0.0";
        }

        return WiFi.localIP().toString();
    }


    String statusText()
    {
        switch (WiFi.status())
        {
            case WL_IDLE_STATUS:
                return "Idle";

            case WL_NO_SSID_AVAIL:
                return "Wi-Fi network not found";

            case WL_SCAN_COMPLETED:
                return "Scan completed";

            case WL_CONNECTED:
                return "Connected";

            case WL_CONNECT_FAILED:
                return "Connection failed";

            case WL_CONNECTION_LOST:
                return "Connection lost";

            case WL_DISCONNECTED:
                return "Disconnected";

            default:
                return "Unknown";
        }
    }
}
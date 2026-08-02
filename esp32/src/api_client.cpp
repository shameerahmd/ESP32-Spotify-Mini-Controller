#include <Arduino.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <WiFiClient.h>

#include "api_client.h"
#include "config.h"
#include "wifi_manager.h"


namespace
{
    constexpr unsigned long
        API_REFRESH_INTERVAL_MS = 5000;

    unsigned long lastRequestAt = 0;

    bool firstRequest = true;
    bool bridgeOnline = false;

    String errorMessage = "";

    DeskSyncApi::DeviceState currentState;


    String createUrl(
        const char* path
    )
    {
        String url = "http://";

        url += DeskSyncConfig::BRIDGE_HOST;
        url += ":";
        url += String(
            DeskSyncConfig::BRIDGE_PORT
        );
        url += path;

        return url;
    }


    bool performGetRequest(
        const char* path,
        JsonDocument& document
    )
    {
        if (!DeskSyncWiFi::isConnected())
        {
            errorMessage =
                "Wi-Fi is not connected.";

            bridgeOnline = false;

            return false;
        }

        WiFiClient client;
        HTTPClient http;

        const String url =
            createUrl(path);

        Serial.print(
            "DeskSync request: "
        );

        Serial.println(url);

        if (!http.begin(client, url))
        {
            errorMessage =
                "Unable to start HTTP request.";

            bridgeOnline = false;

            return false;
        }

        http.setTimeout(
            DeskSyncConfig::HTTP_TIMEOUT_MS
        );

        http.addHeader(
            "X-DeskSync-Key",
            DeskSyncConfig::API_KEY
        );

        const int httpCode =
            http.GET();

        if (httpCode <= 0)
        {
            errorMessage =
                "HTTP request failed: ";

            errorMessage +=
                HTTPClient::errorToString(
                    httpCode
                );

            http.end();

            bridgeOnline = false;

            return false;
        }

        const String payload =
            http.getString();

        http.end();

        Serial.print(
            "HTTP response code: "
        );

        Serial.println(httpCode);

        if (
            httpCode < 200
            || httpCode >= 300
        )
        {
            errorMessage =
                "Bridge returned HTTP ";

            errorMessage +=
                String(httpCode);

            if (!payload.isEmpty())
            {
                errorMessage += ": ";
                errorMessage += payload;
            }

            bridgeOnline = false;

            return false;
        }

        const DeserializationError
            jsonError =
                deserializeJson(
                    document,
                    payload
                );

        if (jsonError)
        {
            errorMessage =
                "JSON error: ";

            errorMessage +=
                jsonError.c_str();

            bridgeOnline = false;

            return false;
        }

        errorMessage = "";
        bridgeOnline = true;

        return true;
    }


    bool checkHealth()
    {
        JsonDocument document;

        if (
            !performGetRequest(
                "/health",
                document
            )
        )
        {
            return false;
        }

        const char* status =
            document["status"]
            | "unknown";

        Serial.print(
            "Bridge health: "
        );

        Serial.println(status);

        return (
            String(status) == "online"
            || String(status) == "degraded"
        );
    }


    bool fetchDeviceState()
    {
        JsonDocument document;

        if (
            !performGetRequest(
                "/device-state",
                document
            )
        )
        {
            currentState.valid = false;

            return false;
        }

        const char* bridgeStatus =
            document["status"]
            | "unknown";

        const char* timestamp =
            document["timestamp"]
            | "";

        const char* spotifyStatus =
            document["spotify"]["status"]
            | "offline";

        const char* songTitle =
            document["spotify"]["title"]
            | "";

        const char* artistName =
            document["spotify"]["artist"]
            | "";

        const char* notificationTitle =
            document[
                "notifications"
            ][
                "latest"
            ][
                "title"
            ]
            | "";

        currentState.valid = true;

        currentState.bridgeStatus =
            bridgeStatus;

        currentState.timestamp =
            timestamp;

        currentState.spotifyOnline =
            String(spotifyStatus)
            == "online";

        currentState.spotifyPlaying =
            document[
                "spotify"
            ][
                "playing"
            ]
            | false;

        currentState.songTitle =
            songTitle;

        currentState.artistName =
            artistName;

        currentState.progressMs =
            document[
                "spotify"
            ][
                "progress_ms"
            ]
            | 0L;

        currentState.durationMs =
            document[
                "spotify"
            ][
                "duration_ms"
            ]
            | 0L;

        currentState.cpuPercent =
            document[
                "system"
            ][
                "cpu_percent"
            ]
            | -1.0F;

        currentState.memoryPercent =
            document[
                "system"
            ][
                "memory_percent"
            ]
            | -1.0F;

        currentState.diskPercent =
            document[
                "system"
            ][
                "disk_percent"
            ]
            | -1.0F;

        currentState.unreadNotifications =
            document[
                "notifications"
            ][
                "unread_count"
            ]
            | 0;

        currentState.latestNotificationTitle =
            notificationTitle;

        return true;
    }


    void printDeviceState()
    {
        Serial.println();
        Serial.println(
            "DeskSync Device State"
        );

        Serial.println(
            "---------------------"
        );

        Serial.print(
            "Bridge: "
        );

        Serial.println(
            currentState.bridgeStatus
        );

        Serial.print(
            "Spotify: "
        );

        Serial.println(
            currentState.spotifyOnline
                ? "Online"
                : "Offline"
        );

        if (currentState.spotifyOnline)
        {
            Serial.print(
                "Playing: "
            );

            Serial.println(
                currentState.spotifyPlaying
                    ? "Yes"
                    : "No"
            );

            Serial.print(
                "Song: "
            );

            Serial.println(
                currentState.songTitle
            );

            Serial.print(
                "Artist: "
            );

            Serial.println(
                currentState.artistName
            );
        }

        Serial.print(
            "CPU: "
        );

        Serial.print(
            currentState.cpuPercent
        );

        Serial.println("%");

        Serial.print(
            "Memory: "
        );

        Serial.print(
            currentState.memoryPercent
        );

        Serial.println("%");

        Serial.print(
            "Disk: "
        );

        Serial.print(
            currentState.diskPercent
        );

        Serial.println("%");

        Serial.print(
            "Unread notifications: "
        );

        Serial.println(
            currentState
                .unreadNotifications
        );

        if (
            !currentState
                .latestNotificationTitle
                .isEmpty()
        )
        {
            Serial.print(
                "Latest notification: "
            );

            Serial.println(
                currentState
                    .latestNotificationTitle
            );
        }

        Serial.println();
    }
}


namespace DeskSyncApi
{
    void begin()
    {
        firstRequest = true;
        bridgeOnline = false;
        errorMessage = "";

        currentState =
            DeviceState();
    }


    void update()
    {
        if (!DeskSyncWiFi::isConnected())
        {
            bridgeOnline = false;
            currentState.valid = false;

            return;
        }

        const unsigned long now =
            millis();

        if (
            !firstRequest
            && now - lastRequestAt
                < API_REFRESH_INTERVAL_MS
        )
        {
            return;
        }

        firstRequest = false;
        lastRequestAt = now;

        if (!checkHealth())
        {
            Serial.print(
                "DeskSync health failed: "
            );

            Serial.println(
                errorMessage
            );

            return;
        }

        if (!fetchDeviceState())
        {
            Serial.print(
                "Device-state request failed: "
            );

            Serial.println(
                errorMessage
            );

            return;
        }

        printDeviceState();
    }


    bool isBridgeOnline()
    {
        return bridgeOnline;
    }


    String lastError()
    {
        return errorMessage;
    }


    const DeviceState& deviceState()
    {
        return currentState;
    }
}
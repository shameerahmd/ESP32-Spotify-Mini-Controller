#pragma once

#include <Arduino.h>


namespace DeskSyncApi
{
    struct DeviceState
    {
        bool valid = false;

        String bridgeStatus = "offline";
        String timestamp = "";

        bool spotifyOnline = false;
        bool spotifyPlaying = false;

        String songTitle = "";
        String artistName = "";

        long progressMs = 0;
        long durationMs = 0;

        float cpuPercent = -1.0;
        float memoryPercent = -1.0;
        float diskPercent = -1.0;

        int unreadNotifications = 0;

        String latestNotificationTitle = "";
    };


    void begin();

    void update();

    bool isBridgeOnline();

    String lastError();

    const DeviceState& deviceState();
}
#pragma once

#include <Arduino.h>


namespace DeskSyncWiFi
{
    void begin();

    void update();

    bool isConnected();

    String ipAddress();

    String statusText();
}
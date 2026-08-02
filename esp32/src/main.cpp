#include <Arduino.h>

#include "config.h"
#include "wifi_manager.h"


bool valueIsConfigured(
    const char* value
)
{
    if (
        value == nullptr
        || value[0] == '\0'
    )
    {
        return false;
    }

    const String text(value);

    return !text.startsWith(
        "YOUR_"
    );
}


bool configurationIsValid()
{
    return (
        valueIsConfigured(
            DeskSyncConfig::WIFI_SSID
        )
        && valueIsConfigured(
            DeskSyncConfig::WIFI_PASSWORD
        )
        && valueIsConfigured(
            DeskSyncConfig::BRIDGE_HOST
        )
        && valueIsConfigured(
            DeskSyncConfig::API_KEY
        )
    );
}


void printConfigurationStatus()
{
    Serial.println();
    Serial.println(
        "DeskSync Configuration Check"
    );

    Serial.println(
        "----------------------------"
    );

    Serial.print(
        "Device name: "
    );

    Serial.println(
        DeskSyncConfig::DEVICE_NAME
    );

    Serial.print(
        "Bridge address: "
    );

    Serial.print(
        DeskSyncConfig::BRIDGE_HOST
    );

    Serial.print(":");

    Serial.println(
        DeskSyncConfig::BRIDGE_PORT
    );

    Serial.print(
        "Wi-Fi configured: "
    );

    Serial.println(
        valueIsConfigured(
            DeskSyncConfig::WIFI_SSID
        )
            ? "Yes"
            : "No"
    );

    Serial.print(
        "API key configured: "
    );

    Serial.println(
        valueIsConfigured(
            DeskSyncConfig::API_KEY
        )
            ? "Yes"
            : "No"
    );

    Serial.println(
        "Passwords and API keys "
        "are never printed."
    );
}


void setup()
{
    Serial.begin(115200);

    delay(1000);

    printConfigurationStatus();

    if (!configurationIsValid())
    {
        Serial.println();
        Serial.println(
            "Configuration is incomplete."
        );

        Serial.println(
            "Update include/config.h "
            "before using the device."
        );

        return;
    }

    DeskSyncWiFi::begin();
}


void loop()
{
    if (configurationIsValid())
    {
        DeskSyncWiFi::update();
    }

    delay(100);
}
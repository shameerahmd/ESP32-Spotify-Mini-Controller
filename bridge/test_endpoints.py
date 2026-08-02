import os
import sys

from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

ENV_PATH = (
    Path(__file__).resolve().parent
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_PATH,
    override=True,
)


BASE_URL = "http://127.0.0.1:5000"

TIMEOUT_SECONDS = 10


API_KEY = os.getenv(
    "DESKSYNC_API_KEY",
    "",
).strip()


PROTECTED_HEADERS = {
    "X-DeskSync-Key": API_KEY,
}


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def print_response(
    data: Any,
    indentation: int = 0,
) -> None:
    """Print nested response data clearly."""

    prefix = " " * indentation

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(
                value,
                (dict, list),
            ):
                print(f"{prefix}{key}:")

                print_response(
                    value,
                    indentation + 2,
                )

            else:
                print(
                    f"{prefix}{key}: {value}"
                )

        return

    if isinstance(data, list):
        for index, value in enumerate(data):
            print(f"{prefix}[{index}]")

            print_response(
                value,
                indentation + 2,
            )

        return

    print(f"{prefix}{data}")


def test_endpoint(
    name: str,
    path: str,
    expected_statuses: tuple[int, ...] = (200,),
    protected: bool = True,
) -> bool:
    """Test one DeskSync GET endpoint."""

    url = f"{BASE_URL}{path}"

    headers = (
        PROTECTED_HEADERS
        if protected
        else {}
    )

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT_SECONDS,
        )

    except requests.ConnectionError:
        print(
            f"FAIL {name}: "
            "DeskSync bridge is not running."
        )
        return False

    except requests.Timeout:
        print(
            f"FAIL {name}: "
            "Request timed out."
        )
        return False

    except requests.RequestException as error:
        print(
            f"FAIL {name}: {error}"
        )
        return False

    if response.status_code not in expected_statuses:
        print(
            f"FAIL {name}: "
            f"HTTP {response.status_code}"
        )

        try:
            print_response(
                response.json()
            )

        except ValueError:
            print(response.text)

        return False

    try:
        data = response.json()

    except ValueError:
        print(
            f"FAIL {name}: "
            "Response was not JSON."
        )

        print(response.text)

        return False

    status = data.get(
        "status",
        "unknown",
    )

    print(
        f"PASS {name}: "
        f"HTTP {response.status_code}, "
        f"status={status}"
    )

    return True


def test_unauthorized_access() -> bool:
    """Confirm protected endpoints reject missing keys."""

    try:
        response = requests.get(
            f"{BASE_URL}/device-state",
            timeout=TIMEOUT_SECONDS,
        )

    except requests.RequestException as error:
        print(
            "FAIL Security Check: "
            f"{error}"
        )
        return False

    if response.status_code != 401:
        print(
            "FAIL Security Check: "
            "Expected HTTP 401 but received "
            f"HTTP {response.status_code}"
        )
        return False

    print(
        "PASS Security Check: "
        "Missing API key was rejected"
    )

    return True


# ---------------------------------------------------------
# Main test runner
# ---------------------------------------------------------

def main() -> int:
    print()
    print("DeskSync Endpoint Test")
    print("=" * 40)
    print()

    if not ENV_PATH.exists():
        print(
            "FAIL: bridge/.env was not found."
        )
        print(
            f"Checked file: {ENV_PATH}"
        )
        return 1

    if not API_KEY:
        print(
            "FAIL: DESKSYNC_API_KEY "
            "was not loaded from bridge/.env"
        )
        print(
            f"Checked file: {ENV_PATH}"
        )
        return 1

    print(
        "API key loaded successfully."
    )
    print(
        f"API key length: {len(API_KEY)}"
    )
    print()

    tests = [
        {
            "name": "Health",
            "path": "/health",
            "expected_statuses": (200,),
            "protected": False,
        },
        {
            "name": "Device State",
            "path": "/device-state",
            "expected_statuses": (200,),
            "protected": True,
        },
        {
            "name": "Spotify Song",
            "path": "/song",
            "expected_statuses": (200,),
            "protected": True,
        },
        {
            "name": "PC System",
            "path": "/system",
            "expected_statuses": (200,),
            "protected": True,
        },
        {
            "name": "Notifications",
            "path": "/notifications?index=0",
            "expected_statuses": (200,),
            "protected": True,
        },
        {
            "name": "Lyrics",
            "path": "/lyrics",
            "expected_statuses": (
                200,
                400,
                404,
            ),
            "protected": True,
        },
    ]

    passed = 0

    for test in tests:
        if test_endpoint(
            name=test["name"],
            path=test["path"],
            expected_statuses=(
                test["expected_statuses"]
            ),
            protected=test["protected"],
        ):
            passed += 1

    security_passed = (
        test_unauthorized_access()
    )

    if security_passed:
        passed += 1

    total = len(tests) + 1

    print()
    print("=" * 40)
    print(
        f"Result: {passed}/{total} "
        "tests passed"
    )

    if passed == total:
        print(
            "DeskSync bridge is ready."
        )
        return 0

    print(
        "One or more endpoints "
        "need attention."
    )

    return 1


if __name__ == "__main__":
    sys.exit(main())
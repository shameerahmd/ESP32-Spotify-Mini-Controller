import sys
from typing import Any

import requests


BASE_URL = "http://127.0.0.1:5000"
TIMEOUT_SECONDS = 10


def test_endpoint(
    name: str,
    path: str,
    expected_statuses: tuple[int, ...] = (200,),
) -> bool:
    """Test one DeskSync GET endpoint."""

    url = f"{BASE_URL}{path}"

    try:
        response = requests.get(
            url,
            timeout=TIMEOUT_SECONDS,
        )

    except requests.ConnectionError:
        print(
            f"FAIL {name}: DeskSync bridge is not running."
        )
        return False

    except requests.Timeout:
        print(
            f"FAIL {name}: Request timed out."
        )
        return False

    except requests.RequestException as error:
        print(
            f"FAIL {name}: {error}"
        )
        return False

    if response.status_code not in expected_statuses:
        print(
            f"FAIL {name}: HTTP "
            f"{response.status_code}"
        )

        try:
            print_response(response.json())

        except ValueError:
            print(response.text)

        return False

    try:
        data = response.json()

    except ValueError:
        print(
            f"FAIL {name}: Response was not JSON."
        )
        print(response.text)
        return False

    status = data.get("status", "unknown")

    print(
        f"PASS {name}: "
        f"HTTP {response.status_code}, "
        f"status={status}"
    )

    return True


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


def main() -> int:
    print()
    print("DeskSync Endpoint Test")
    print("=" * 40)
    print()

    tests = [
        (
            "Health",
            "/health",
            (200,),
        ),
        (
            "Device State",
            "/device-state",
            (200,),
        ),
        (
            "Spotify Song",
            "/song",
            (200,),
        ),
        (
            "PC System",
            "/system",
            (200,),
        ),
        (
            "Notifications",
            "/notifications?index=0",
            (200,),
        ),
        (
            "Lyrics",
            "/lyrics",
            (200, 400, 404),
        ),
    ]

    passed = 0

    for name, path, expected_statuses in tests:
        if test_endpoint(
            name=name,
            path=path,
            expected_statuses=expected_statuses,
        ):
            passed += 1

    total = len(tests)

    print()
    print("=" * 40)
    print(
        f"Result: {passed}/{total} tests passed"
    )

    if passed == total:
        print("DeskSync bridge is ready.")
        return 0

    print(
        "One or more endpoints need attention."
    )

    return 1


if __name__ == "__main__":
    sys.exit(main())
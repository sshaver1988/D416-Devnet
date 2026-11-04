"""Create a Webex room if needed and post a guideline notice."""

import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://webexapis.com/v1"
ROOM_TITLE = "DEVASC2025 Space"
TARGET_TEXT = (
    "Hello everyone! This is a test message from the Webex API script."
)
REPLACEMENT_TEXT = "Previous post did not meet guidelines."


def api_request(path_or_url, token, method="GET", payload=None):
    if urlparse(path_or_url).scheme:
        url = path_or_url
    else:
        url = BASE_URL.rstrip("/") + "/" + path_or_url.lstrip("/")
    parsed_url = urlparse(url)
    if parsed_url.scheme != "https" or parsed_url.hostname != "webexapis.com":
        raise RuntimeError("Webex API returned an unexpected pagination URL.")

    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read()
            result = json.loads(body.decode("utf-8")) if body else None
            return result, response.headers.get("Link", "")
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            "Webex API request failed (HTTP {}): {}".format(
                error.code, details or error.reason
            )
        ) from error
    except URLError as error:
        raise RuntimeError("Could not reach the Webex API: {}".format(error.reason)) from error


def next_page_url(link_header):
    match = re.search(
        r'<([^>]+)>\s*;\s*rel="?next"?',
        link_header,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else None


def get_all(path, token, collection_key, params=None):
    query = "?" + urlencode(params) if params else ""
    next_url = path + query
    results = []

    while next_url:
        response, link_header = api_request(next_url, token)
        if not isinstance(response, dict) or not isinstance(
            response.get(collection_key), list
        ):
            raise RuntimeError(
                "Unexpected Webex API response while reading {}.".format(
                    collection_key
                )
            )
        results.extend(response[collection_key])
        next_url = next_page_url(link_header)

    return results


def confirm_changes(action):
    print(action)
    if "--yes" in sys.argv[1:]:
        return True
    confirmation = input("Continue? [y/N] ").strip().lower()
    return confirmation in ("y", "yes")


def post_replacement(room_id, token):
    api_request(
        "/messages",
        token,
        method="POST",
        payload={"roomId": room_id, "text": REPLACEMENT_TEXT},
    )
    print("Replacement message posted.")


def main():
    token = os.environ.get("WEBEX_ACCESS_TOKEN")
    if not token:
        raise RuntimeError(
            "Set the WEBEX_ACCESS_TOKEN environment variable before running."
        )

    rooms = get_all("/rooms", token, "items", {"max": 1000})
    matching_rooms = [
        room for room in rooms if room.get("title") == ROOM_TITLE
    ]
    if len(matching_rooms) > 1:
        raise RuntimeError(
            "Expected at most one room titled {!r}; found {}.".format(
                ROOM_TITLE, len(matching_rooms)
            )
        )

    if not matching_rooms:
        if not confirm_changes(
            "Room {!r} does not exist. It will be created and the notice posted.".format(
                ROOM_TITLE
            )
        ):
            print("No changes made.")
            return
        room, _ = api_request(
            "/rooms",
            token,
            method="POST",
            payload={"title": ROOM_TITLE},
        )
        if not isinstance(room, dict) or not room.get("id"):
            raise RuntimeError("The created room response did not include an ID.")
        print("Room created: {}.".format(ROOM_TITLE))
        post_replacement(room["id"], token)
        return

    room_id = matching_rooms[0].get("id")
    if not room_id:
        raise RuntimeError("The matching room did not include an ID.")

    messages = get_all(
        "/messages",
        token,
        "items",
        {"roomId": room_id, "max": 1000},
    )
    matching_messages = [
        message for message in messages if message.get("text") == TARGET_TEXT
    ]
    if len(matching_messages) != 1:
        raise RuntimeError(
            "Expected exactly one matching message; found {}.".format(
                len(matching_messages)
            )
        )

    message_id = matching_messages[0].get("id")
    if not message_id:
        raise RuntimeError("The matching message did not include an ID.")

    if not confirm_changes(
        "Room and exact message found. The message will be deleted and replaced."
    ):
        print("No changes made.")
        return

    api_request("/messages/{}".format(message_id), token, method="DELETE")
    print("Original message deleted.")
    post_replacement(room_id, token)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, EOFError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        sys.exit(1)
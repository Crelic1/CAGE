"""Graceful pre-cap wrap-up reminder (Layer-1).

Three pure pieces make up the hook:
  * ``resolve_wrapup`` — turns a ``wrapup_before`` OFFSET + message (runtime
    override or benchmark-sample default) into an ABSOLUTE ``(wrapup_at, msg)``
    against the resolved round cap. Disabled when there is no finite cap, no
    positive offset, the offset is not below the cap, or the message is empty.
  * ``_inject_wrapup_reminder`` — appends the reminder into the last ``user``
    turn of an Anthropic-shaped request body (so it rides a still-forwarded
    request, unlike the hard ``max_requests`` rejection).
  * ``_wrapup_reminder_active`` — emits only at the successful-round boundary;
    a failed upstream attempt leaves the count there so its retry is reminded.
"""

from __future__ import annotations

import pytest

from cage.contracts.execution import resolve_wrapup
from cage.experiment.engine.trial_runner import _effective_trial_startup_reminder
from cage.proxy.sidecar import (
    _inject_wrapup_reminder,
    _startup_reminder_active,
    _wrapup_reminder_active,
)

# --------------------------------------------------------------------------- #
# resolve_wrapup(cap, exec_before, exec_msg, sample_before, sample_msg)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "cap, exec_before, exec_msg, sample_before, sample_msg, expected",
    [
        # sample default: offset 5 below a cap of 60 ⇒ fire at 55
        (60, None, None, 5, "flush", (55, "flush")),
        # runtime override wins over the sample default (both offset and message)
        (60, 10, "yaml", 5, "sample", (50, "yaml")),
        # runtime offset only ⇒ runtime offset + sample message
        (60, 10, None, 5, "sample", (50, "sample")),
        # empty / blank message ⇒ disabled
        (60, None, None, 5, "", (-1, "")),
        (60, None, None, 5, "   ", (-1, "")),
        # no finite cap ⇒ nothing to offset from ⇒ disabled
        (-1, None, None, 5, "flush", (-1, "")),
        (0, None, None, 5, "flush", (-1, "")),
        # no positive offset ⇒ disabled
        (60, None, None, None, "flush", (-1, "")),
        (60, None, None, 0, "flush", (-1, "")),
        (60, None, None, -3, "flush", (-1, "")),
        # offset not strictly below the cap ⇒ disabled (would fire at/before 0)
        (60, None, None, 60, "flush", (-1, "")),
        (60, None, None, 99, "flush", (-1, "")),
    ],
)
def test_resolve_wrapup(cap, exec_before, exec_msg, sample_before, sample_msg, expected):
    assert resolve_wrapup(cap, exec_before, exec_msg, sample_before, sample_msg) == expected


# --------------------------------------------------------------------------- #
# _inject_wrapup_reminder(body, message)  -> appends to the last user turn
# --------------------------------------------------------------------------- #

def test_inject_into_string_content():
    body = {"messages": [{"role": "user", "content": "hello"}]}
    assert _inject_wrapup_reminder(body, "WRAP") is True
    content = body["messages"][0]["content"]
    assert content.startswith("hello")
    assert "<system-reminder>" in content and "WRAP" in content


def test_inject_into_list_content_targets_last_user():
    body = {
        "messages": [
            {"role": "user", "content": "task"},
            {"role": "assistant", "content": "working"},
            {"role": "user", "content": [{"type": "tool_result", "content": "obs"}]},
        ]
    }
    assert _inject_wrapup_reminder(body, "WRAP") is True
    # the assistant turn is untouched; the block lands on the LAST user turn
    assert body["messages"][1]["content"] == "working"
    last = body["messages"][-1]["content"]
    assert last[0]["type"] == "tool_result"
    assert last[-1]["type"] == "text" and "WRAP" in last[-1]["text"]


def test_inject_noops_without_user_turn():
    body = {"messages": [{"role": "assistant", "content": "x"}]}
    assert _inject_wrapup_reminder(body, "WRAP") is False
    assert body["messages"][0]["content"] == "x"


def test_inject_noops_on_empty_message_or_no_messages():
    body = {"messages": [{"role": "user", "content": "hi"}]}
    assert _inject_wrapup_reminder(body, "") is False
    assert body["messages"][0]["content"] == "hi"
    assert _inject_wrapup_reminder({"messages": []}, "WRAP") is False
    assert _inject_wrapup_reminder({}, "WRAP") is False


@pytest.mark.parametrize(
    "round_count,expected",
    [
        (179, False),  # at - 1
        (180, True),   # at
        (181, False),  # at + 1
    ],
)
def test_wrapup_reminder_fires_only_at_boundary(round_count, expected):
    assert _wrapup_reminder_active(round_count, 180, "WRAP") is expected


def test_wrapup_reminder_is_retried_after_upstream_failure():
    # The first boundary request fails upstream, so the successful-round count
    # remains 180. Its retry is reminded again; only a success advances to 181
    # and disables subsequent injection.
    successful_round_counts = [179, 180, 180, 181]
    assert [
        _wrapup_reminder_active(count, 180, "WRAP")
        for count in successful_round_counts
    ] == [False, True, True, False]


@pytest.mark.parametrize(
    "sample,expected",
    [
        (
            {
                "startup_reminder_at": 4,
                "startup_reminder_until": 16,
                "startup_reminder_message": "deliver",
            },
            (4, 16, "deliver"),
        ),
        ({}, (-1, -1, "")),
        (
            {
                "startup_reminder_at": 0,
                "startup_reminder_until": 16,
                "startup_reminder_message": "deliver",
            },
            (-1, -1, ""),
        ),
        (
            {
                "startup_reminder_at": 8,
                "startup_reminder_until": 4,
                "startup_reminder_message": "deliver",
            },
            (-1, -1, ""),
        ),
    ],
)
def test_resolve_startup_reminder(sample, expected):
    assert _effective_trial_startup_reminder(sample) == expected


def test_startup_reminder_window_is_inclusive():
    assert not _startup_reminder_active(3, 4, 16, "deliver")
    assert _startup_reminder_active(4, 4, 16, "deliver")
    assert _startup_reminder_active(16, 4, 16, "deliver")
    assert not _startup_reminder_active(17, 4, 16, "deliver")
    assert not _startup_reminder_active(8, 4, 16, "")

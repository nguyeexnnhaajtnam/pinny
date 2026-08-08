import json
import logging

from pinny.core.logging import JsonFormatter, redact


def test_redact_masks_nested_sensitive_values() -> None:
    value = {"user": "pinny", "nested": {"password": "do-not-log"}, "token": "secret"}

    assert redact(value) == {
        "user": "pinny",
        "nested": {"password": "[REDACTED]"},
        "token": "[REDACTED]",
    }


def test_formatter_outputs_json_and_redacts_message_and_context() -> None:
    record = logging.LogRecord(
        "pinny.test", logging.INFO, __file__, 1, "password=hunter2", (), None
    )
    record.context = {"authorization": "Bearer private", "request_id": "abc"}

    output = json.loads(JsonFormatter().format(record))

    assert output["message"] == "password=[REDACTED]"
    assert output["context"]["authorization"] == "[REDACTED]"
    assert output["context"]["request_id"] == "abc"

import copy
import json

import pytest

from agentshield.audit import AuditLog, minimize


@pytest.mark.parametrize("key", [
    "password", "PASSWORD", "passwd", "token", "Authorization", "Proxy-Authorization",
    "access_token", "accessToken", "refresh-token", "id_token", "api_key", "X-API-Key",
    "client_secret", "SECRET", "aws_secret_access_key", "aws_session_token", "private_key",
])
def test_credentials_are_fully_redacted(key):
    secret = "SYNTHETIC-CREDENTIAL-Z9Q7"
    redacted = minimize({key: secret})
    assert redacted == {key: "[REDACTED]"}
    assert "Z9Q7" not in json.dumps(redacted)


def test_nested_dicts_and_lists_are_redacted_without_mutating_arguments():
    args = {
        "order_ids": ["ORD-1001"],
        "requests": [
            {"headers": {"Authorization": "Bearer SYNTHETIC-HEADER"}},
            {"items": [{"accessToken": "SYNTHETIC-TOKEN", "status": "PENDING"}]},
        ],
    }
    before = copy.deepcopy(args)
    assert minimize(args) == {
        "order_ids": ["ORD-1001"],
        "requests": [
            {"headers": {"Authorization": "[REDACTED]"}},
            {"items": [{"accessToken": "[REDACTED]", "status": "PENDING"}]},
        ],
    }
    assert args == before


@pytest.mark.parametrize("key,value,expected", [
    ("account", "GT82-0000-0091", "***0091"),
    ("CARD", "4111111111111234", "***1234"),
    ("account", "1234", "***"),
    ("card", "123", "***"),
    ("account", None, None),
    ("card", "", ""),
])
def test_account_and_card_masking_at_any_depth(key, value, expected):
    assert minimize({"customer": [{key: value}]}) == {"customer": [{key: expected}]}


def test_structured_credential_and_account_values_do_not_expose_contents():
    assert minimize({"token": {"value": "SYNTHETIC-TOKEN"},
                     "account": ["SYNTHETIC-ACCOUNT"]}) == {
        "token": "[REDACTED]", "account": "[REDACTED]"}


def test_non_sensitive_fields_and_types_are_preserved():
    args = {"order_id": "ORD-1001", "status": "PENDING", "version": 2, "enabled": True,
            "token_count": 10, "max_tokens": 100, "secretary": "Customer-A", "empty": None,
            "items": [1, False, None, "read-only"], "checks": {"grounded": 0.95}}
    assert minimize(args) == args


def test_file_and_listeners_receive_only_redacted_record(tmp_path):
    path = tmp_path / "audit.jsonl"
    audit = AuditLog(path)
    events = []
    audit.subscribe(events.append)
    record = {
        "decision_id": "test-decision", "verdict": "deny", "reason": "regla dura",
        "token": "SYNTHETIC-TOP-LEVEL", "args": {"account": "GT82-0000-0091"},
        "upstream": {"headers": {"Authorization": "Bearer SYNTHETIC-HEADER"}},
    }
    original = copy.deepcopy(record)

    audit.write(record)

    serialized = path.read_text(encoding="utf-8")
    saved = json.loads(serialized)
    assert "SYNTHETIC" not in serialized and "GT82-0000" not in serialized
    assert saved["token"] == "[REDACTED]"
    assert saved["upstream"]["headers"]["Authorization"] == "[REDACTED]"
    assert saved["args"]["account"] == "***0091"
    assert saved["decision_id"] == "test-decision" and saved["verdict"] == "deny" and saved["ts"]
    assert events == [saved]
    assert record == original

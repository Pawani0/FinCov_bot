import json
import base64

from utils.tts import _extract_audio_from_unmute_message


def test_binary_message_returns_audio_and_not_done():
    data = b"\x00\x01\x02test"
    audio, done = _extract_audio_from_unmute_message(data)
    assert audio == data
    assert done is False


def test_json_with_base64_audio_returns_audio():
    payload = {"audio": base64.b64encode(b"hello").decode("ascii")}
    audio, done = _extract_audio_from_unmute_message(json.dumps(payload))
    assert audio == b"hello"
    assert done is False


def test_json_done_event_sets_done_true():
    payload = {"event": "done"}
    audio, done = _extract_audio_from_unmute_message(json.dumps(payload))
    assert audio is None
    assert done is True


def test_invalid_base64_does_not_crash_and_returns_none():
    payload = {"audio": "!!!not_base64!!!"}
    audio, done = _extract_audio_from_unmute_message(json.dumps(payload))
    assert audio is None
    assert done is False


def test_plain_text_message_returns_none():
    audio, done = _extract_audio_from_unmute_message("not json, not binary")
    assert audio is None
    assert done is False

"""Tests for content extraction helpers."""
from unittest.mock import MagicMock
from app.bot.content import extract_content, build_header
from app.models import ContentType


def _make_message(**kwargs):
    """Create a mock Telegram message with specified content."""
    msg = MagicMock()
    msg.text = kwargs.get("text")
    msg.caption = kwargs.get("caption")
    msg.photo = kwargs.get("photo")
    msg.video = kwargs.get("video")
    msg.voice = kwargs.get("voice")
    msg.video_note = kwargs.get("video_note")
    msg.sticker = kwargs.get("sticker")
    msg.document = kwargs.get("document")
    msg.animation = kwargs.get("animation")
    msg.audio = kwargs.get("audio")
    return msg


def test_extract_text_message():
    msg = _make_message(text="Hello world")
    result = extract_content(msg)
    assert result["content_type"] == ContentType.TEXT
    assert result["text"] == "Hello world"
    assert result["file_id"] is None


def test_extract_photo_message():
    small = MagicMock()
    small.file_id = "small_id"
    large = MagicMock()
    large.file_id = "large_id"
    msg = _make_message(photo=[small, large], caption="Nice photo")
    result = extract_content(msg)
    assert result["content_type"] == ContentType.PHOTO
    assert result["file_id"] == "large_id"
    assert result["text"] == "Nice photo"


def test_extract_photo_no_caption():
    photo = MagicMock()
    photo.file_id = "photo_id"
    msg = _make_message(photo=[photo])
    result = extract_content(msg)
    assert result["content_type"] == ContentType.PHOTO
    assert result["text"] == ""


def test_extract_video_message():
    video = MagicMock()
    video.file_id = "video_id"
    msg = _make_message(video=video, caption="My video")
    result = extract_content(msg)
    assert result["content_type"] == ContentType.VIDEO
    assert result["file_id"] == "video_id"
    assert result["text"] == "My video"


def test_extract_voice_message():
    voice = MagicMock()
    voice.file_id = "voice_id"
    msg = _make_message(voice=voice)
    result = extract_content(msg)
    assert result["content_type"] == ContentType.VOICE
    assert result["file_id"] == "voice_id"
    assert result["text"] == ""


def test_extract_video_note_message():
    video_note = MagicMock()
    video_note.file_id = "videonote_id"
    msg = _make_message(video_note=video_note)
    result = extract_content(msg)
    assert result["content_type"] == ContentType.VIDEO_NOTE
    assert result["file_id"] == "videonote_id"
    assert result["text"] == ""


def test_extract_sticker_message():
    sticker = MagicMock()
    sticker.file_id = "sticker_id"
    msg = _make_message(sticker=sticker)
    result = extract_content(msg)
    assert result["content_type"] == ContentType.STICKER
    assert result["file_id"] == "sticker_id"
    assert result["text"] == ""


def test_extract_document_message():
    document = MagicMock()
    document.file_id = "doc_id"
    msg = _make_message(document=document, caption="Report.pdf")
    result = extract_content(msg)
    assert result["content_type"] == ContentType.DOCUMENT
    assert result["file_id"] == "doc_id"
    assert result["text"] == "Report.pdf"


def test_extract_animation_message():
    animation = MagicMock()
    animation.file_id = "gif_id"
    msg = _make_message(animation=animation)
    result = extract_content(msg)
    assert result["content_type"] == ContentType.ANIMATION
    assert result["file_id"] == "gif_id"
    assert result["text"] == ""


def test_extract_audio_message():
    audio = MagicMock()
    audio.file_id = "audio_id"
    msg = _make_message(audio=audio, caption="Song")
    result = extract_content(msg)
    assert result["content_type"] == ContentType.AUDIO
    assert result["file_id"] == "audio_id"
    assert result["text"] == "Song"


def test_extract_empty_text_message():
    msg = _make_message()
    result = extract_content(msg)
    assert result["content_type"] == ContentType.TEXT
    assert result["text"] == ""
    assert result["file_id"] is None


def test_build_header_with_username():
    header = build_header(42, "Ivan", "ivan_dev")
    assert "#42" in header
    assert "Ivan" in header
    assert "@ivan_dev" in header


def test_build_header_without_username():
    header = build_header(1, "Anna", None)
    assert "Anna" in header
    assert "@" not in header


def test_build_header_custom_status():
    header = build_header(5, "User", None, status_text="Закрыто")
    assert "Закрыто" in header

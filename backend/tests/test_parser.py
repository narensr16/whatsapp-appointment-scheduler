"""Tests for natural-language WhatsApp message parsing."""
from datetime import datetime, date, time, timedelta
from app.services.message_parser import MessageParser


def test_parse_challenge_exact_example_without_date_before_time():
    """
    Test exact challenge example: 'Book appointment with Dr. A at 10am'.
    Default Date Policy: When current time is 8 AM, 10 AM today is in the future,
    so it infers TODAY.
    """
    ref_dt = datetime(2026, 10, 15, 8, 0, 0)
    msg = "Book appointment with Dr. A at 10am"
    parsed = MessageParser.parse_message(msg, reference_datetime=ref_dt)

    assert parsed.is_complete is True
    assert "Dr. A" in parsed.doctor_query
    assert parsed.target_time == time(10, 0)
    assert parsed.target_date == date(2026, 10, 15)
    assert parsed.slot == datetime(2026, 10, 15, 10, 0)


def test_parse_challenge_exact_example_without_date_after_time():
    """
    Test exact challenge example: 'Book appointment with Dr. A at 10am'.
    Default Date Policy: When current time is 11 AM, 10 AM today has already passed,
    so it infers TOMORROW.
    """
    ref_dt = datetime(2026, 10, 15, 11, 0, 0)
    msg = "Book appointment with Dr. A at 10am"
    parsed = MessageParser.parse_message(msg, reference_datetime=ref_dt)

    assert parsed.is_complete is True
    assert "Dr. A" in parsed.doctor_query
    assert parsed.target_time == time(10, 0)
    assert parsed.target_date == date(2026, 10, 16)
    assert parsed.slot == datetime(2026, 10, 16, 10, 0)


def test_parse_tomorrow_10am():
    """Test 'Book appointment with Dr. A at 10 AM tomorrow.'"""
    ref_dt = datetime(2026, 10, 15, 8, 0, 0)
    msg = "Book appointment with Dr. A at 10 AM tomorrow."
    parsed = MessageParser.parse_message(msg, reference_datetime=ref_dt)

    assert parsed.is_complete is True
    assert "Dr. A" in parsed.doctor_query
    assert parsed.target_date == date(2026, 10, 16)
    assert parsed.target_time == time(10, 0)
    assert parsed.slot == datetime(2026, 10, 16, 10, 0)


def test_parse_explicit_date_and_time():
    """Test 'I need an appointment with Dr. B on 20 October at 3 PM.'"""
    ref_dt = datetime(2026, 10, 1, 9, 0, 0)
    msg = "I need an appointment with Dr. B on 20 October at 3 PM."
    parsed = MessageParser.parse_message(msg, reference_datetime=ref_dt)

    assert parsed.is_complete is True
    assert "Dr. B" in parsed.doctor_query
    assert parsed.target_date == date(2026, 10, 20)
    assert parsed.target_time == time(15, 0)
    assert parsed.slot == datetime(2026, 10, 20, 15, 0)


def test_parse_today_1030am():
    """Test 'Book Dr. A today at 10:30 AM.'"""
    ref_dt = datetime(2026, 10, 15, 8, 0, 0)
    msg = "Book Dr. A today at 10:30 AM."
    parsed = MessageParser.parse_message(msg, reference_datetime=ref_dt)

    assert parsed.is_complete is True
    assert "Dr. A" in parsed.doctor_query
    assert parsed.target_date == date(2026, 10, 15)
    assert parsed.target_time == time(10, 30)
    assert parsed.slot == datetime(2026, 10, 15, 10, 30)


def test_parse_missing_time():
    """Test message missing time prompt clarification."""
    msg = "I want to see Dr. Bob Jones tomorrow."
    parsed = MessageParser.parse_message(msg)

    assert parsed.is_complete is False
    assert parsed.target_time is None
    assert parsed.clarification_prompt is not None
    assert "time" in parsed.clarification_prompt.lower()


def test_parse_missing_doctor():
    """Test message missing doctor prompt clarification."""
    msg = "Book appointment tomorrow at 10 AM."
    parsed = MessageParser.parse_message(msg)

    assert parsed.is_complete is False
    assert parsed.doctor_query is None
    assert "doctor" in parsed.clarification_prompt.lower()


def test_parse_missing_date_and_time():
    """Test message specifying only doctor prompts for date and time clarification."""
    msg = "I want to see Dr. Alice Smith."
    parsed = MessageParser.parse_message(msg)

    assert parsed.is_complete is False
    assert parsed.target_time is None
    assert parsed.clarification_prompt is not None
    assert "date" in parsed.clarification_prompt.lower() or "time" in parsed.clarification_prompt.lower()


def test_parse_empty_or_greeting():
    """Test greeting message provides helpful usage info."""
    msg = "Hi there"
    parsed = MessageParser.parse_message(msg)

    assert parsed.is_complete is False
    assert parsed.clarification_prompt is not None

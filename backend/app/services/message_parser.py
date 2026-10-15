"""
Natural-language message parser for WhatsApp appointment booking requests.
Extracts doctor, date, and time, normalizes values, handles relative and explicit formats,
and flags ambiguity or missing fields for clarification.
"""
import re
from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any, Tuple
from dateutil import parser as dt_parser


class ParsedBookingRequest:
    def __init__(
        self,
        doctor_query: Optional[str] = None,
        target_date: Optional[date] = None,
        target_time: Optional[time] = None,
        slot: Optional[datetime] = None,
        is_complete: bool = False,
        clarification_prompt: Optional[str] = None,
        raw_text: str = ""
    ):
        self.doctor_query = doctor_query
        self.target_date = target_date
        self.target_time = target_time
        self.slot = slot
        self.is_complete = is_complete
        self.clarification_prompt = clarification_prompt
        self.raw_text = raw_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doctor_query": self.doctor_query,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "target_time": self.target_time.strftime("%I:%M %p") if self.target_time else None,
            "slot": self.slot.isoformat() if self.slot else None,
            "is_complete": self.is_complete,
            "clarification_prompt": self.clarification_prompt,
            "raw_text": self.raw_text
        }


class MessageParser:
    """Parses natural-language booking messages into structured appointment intents."""

    # Month names for regex matching
    MONTHS = (
        r"january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
    )

    @classmethod
    def parse_message(cls, text: str, reference_datetime: Optional[datetime] = None) -> ParsedBookingRequest:
        """
        Parse raw WhatsApp message into structured appointment intent.
        
        Args:
            text: Raw WhatsApp message string.
            reference_datetime: Optional base datetime (defaults to datetime.utcnow()).
        """
        if not text or not text.strip():
            return ParsedBookingRequest(
                is_complete=False,
                clarification_prompt="Hello! You can book an appointment by saying: 'Book appointment with Dr. A tomorrow at 10 AM'.",
                raw_text=""
            )

        ref_dt = reference_datetime or datetime.utcnow()
        text_clean = text.strip()

        doctor_query = cls._extract_doctor(text_clean)
        target_date = cls._extract_date(text_clean, ref_dt)
        target_time = cls._extract_time(text_clean)

        # If time is specified but date is omitted, apply Default Date Policy:
        # If the requested time today is still in the future, book today.
        # Otherwise, book tomorrow.
        if not target_date and target_time:
            today = ref_dt.date()
            candidate_today = datetime.combine(today, target_time)
            if candidate_today > ref_dt:
                target_date = today
            else:
                target_date = today + timedelta(days=1)

        # Check for completeness and missing parts
        missing = []
        if not doctor_query:
            missing.append("the doctor's name (e.g. Dr. A or Dr. B)")
        if not target_date:
            missing.append("the date (e.g. today, tomorrow, or 20 October)")
        if not target_time:
            missing.append("the appointment time (e.g. 10:00 AM or 3:00 PM)")

        if missing:
            clarification = (
                f"I couldn't quite complete your booking. Please specify {', and '.join(missing)}. "
                "Example: 'Book Dr. A tomorrow at 10 AM'."
            )
            return ParsedBookingRequest(
                doctor_query=doctor_query,
                target_date=target_date,
                target_time=target_time,
                is_complete=False,
                clarification_prompt=clarification,
                raw_text=text
            )

        # Combine date and time
        slot = datetime.combine(target_date, target_time)

        return ParsedBookingRequest(
            doctor_query=doctor_query,
            target_date=target_date,
            target_time=target_time,
            slot=slot,
            is_complete=True,
            clarification_prompt=None,
            raw_text=text
        )

    @classmethod
    def _extract_doctor(cls, text: str) -> Optional[str]:
        """Extract doctor identifier or name from message."""
        # 1. Matches "Dr. A", "Dr A", "Dr. Alice Smith", "Doctor Bob"
        patterns = [
            r"\b(?:dr\.|dr|doctor)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
            r"\bwith\s+(?:dr\.|dr|doctor)?\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)",
            r"\bsee\s+(?:dr\.|dr|doctor)?\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)"
        ]

        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # Stop if candidate grabbed preposition
                candidate = re.split(r"\b(?:at|on|today|tomorrow|in|for)\b", candidate, flags=re.IGNORECASE)[0].strip()
                if candidate:
                    return f"Dr. {candidate}" if not candidate.lower().startswith("dr") else candidate

        # Check direct doctor ID if mentioned e.g. "doctor 1" or "doctor id 2"
        id_match = re.search(r"\bdoctor\s+(?:id\s*)?([0-9]+)\b", text, re.IGNORECASE)
        if id_match:
            return id_match.group(1)

        return None

    @classmethod
    def _extract_date(cls, text: str, ref_dt: datetime) -> Optional[date]:
        """Extract target date from text relative to reference date."""
        today = ref_dt.date()
        lower = text.lower()

        # Relative keywords
        if re.search(r"\bday after tomorrow\b", lower):
            return today + timedelta(days=2)
        if re.search(r"\btomorrow\b", lower):
            return today + timedelta(days=1)
        if re.search(r"\btoday\b", lower):
            return today

        # Explicit date: "20 October", "20th October", "October 20", "Oct 20th"
        day_month = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({cls.MONTHS})(?:\s+(\d{{4}}))?\b", lower)
        if day_month:
            day_str, month_str, year_str = day_month.group(1), day_month.group(2), day_month.group(3)
            year = int(year_str) if year_str else ref_dt.year
            try:
                parsed_dt = dt_parser.parse(f"{day_str} {month_str} {year}")
                parsed_date = parsed_dt.date()
                if not year_str and parsed_date < today:
                    parsed_date = parsed_date.replace(year=year + 1)
                return parsed_date
            except Exception:
                pass

        month_day = re.search(rf"\b({cls.MONTHS})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s+(\d{{4}}))?\b", lower)
        if month_day:
            month_str, day_str, year_str = month_day.group(1), month_day.group(2), month_day.group(3)
            year = int(year_str) if year_str else ref_dt.year
            try:
                parsed_dt = dt_parser.parse(f"{month_str} {day_str} {year}")
                parsed_date = parsed_dt.date()
                if not year_str and parsed_date < today:
                    parsed_date = parsed_date.replace(year=year + 1)
                return parsed_date
            except Exception:
                pass

        # ISO format: 2026-10-20 or 20/10/2026
        iso_match = re.search(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b", lower)
        if iso_match:
            try:
                return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            except Exception:
                pass

        return None

    @classmethod
    def _extract_time(cls, text: str) -> Optional[time]:
        """Extract appointment time (e.g., 10 AM, 10:30 AM, 3 PM, 14:00)."""
        lower = text.lower()

        # 12-hour format with AM/PM: "10:30 AM", "10 AM", "3:15 pm", "2pm"
        ampm_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lower)
        if ampm_match:
            hour = int(ampm_match.group(1))
            minute = int(ampm_match.group(2)) if ampm_match.group(2) else 0
            meridiem = ampm_match.group(3)

            if hour == 12:
                hour = 12 if meridiem == "pm" else 0
            elif meridiem == "pm":
                hour += 12

            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return time(hour, minute)

        # 24-hour format: "14:00", "09:30"
        military_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", lower)
        if military_match:
            hour = int(military_match.group(1))
            minute = int(military_match.group(2))
            return time(hour, minute)

        return None

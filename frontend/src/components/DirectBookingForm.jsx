import React, { useState, useEffect } from 'react';
import { Send, CheckCircle2, AlertCircle, Clock, Calendar, Phone, User, Loader2 } from 'lucide-react';
import { api } from '../api';
import { validatePhoneNumber } from '../utils/phoneValidation';
import { formatApiErrorMessage, getApiErrorField } from '../utils/errorHandler';

export const DirectBookingForm = ({ onAppointmentCreated }) => {
  const [doctors, setDoctors] = useState([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState('');
  const [phone, setPhone] = useState('+14155552671');
  const [dateStr, setDateStr] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedTime, setSelectedTime] = useState('');
  const [loading, setLoading] = useState(false);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [message, setMessage] = useState(null);

  // Automatically clears phone validation errors and stale success messages
  // while preserving unrelated schedule/slot errors.
  const clearPhoneError = () => {
    setMessage((prev) => {
      if (!prev) return null;
      if (prev.type === 'success' || prev.field === 'phone') {
        return null;
      }
      return prev;
    });
  };

  // Clears stale success messages and schedule/doctor/slot errors
  // while preserving unrelated phone validation errors.
  const clearScheduleError = () => {
    setMessage((prev) => {
      if (!prev) return null;
      if (prev.type === 'success' || prev.field !== 'phone') {
        return null;
      }
      return prev;
    });
  };

  useEffect(() => {
    const loadDoctors = async () => {
      try {
        const data = await api.getDoctors();
        setDoctors(data);
        if (data.length > 0) {
          setSelectedDoctorId(String(data[0].id));
        }
      } catch (err) {
        console.error('Failed to load doctors', err);
      }
    };
    loadDoctors();
  }, []);

  useEffect(() => {
    const loadSlots = async () => {
      if (!selectedDoctorId || !dateStr) return;
      setSlotsLoading(true);
      try {
        const slotData = await api.getDoctorSlots(selectedDoctorId, dateStr);
        setAvailableSlots(slotData.available_slots || []);
        if (slotData.available_slots?.length > 0) {
          setSelectedTime(slotData.available_slots[0]);
        } else {
          setSelectedTime('');
        }
      } catch (err) {
        console.error('Failed to load slots', err);
      } finally {
        setSlotsLoading(false);
      }
    };

    loadSlots();
  }, [selectedDoctorId, dateStr]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Prevent duplicate submission while already processing
    if (loading) return;

    // Clear any previous message before processing new request
    setMessage(null);

    // 1. Validate slot selection
    if (!selectedTime) {
      setMessage({
        type: 'error',
        text: 'Please select an available appointment time slot.',
        field: 'slot'
      });
      return;
    }

    // 2. Validate patient phone number (rejects abc123, empty strings, invalid characters)
    const phoneValidation = validatePhoneNumber(phone);
    if (!phoneValidation.isValid) {
      setMessage({
        type: 'error',
        text: phoneValidation.error,
        field: 'phone'
      });
      return;
    }

    setLoading(true);

    try {
      // Parse 12-hour time e.g. "10:00 AM" or "02:30 PM" into datetime ISO
      const [timePart, meridiem] = selectedTime.split(' ');
      const [hoursStr, minutesStr] = timePart.split(':');
      let hours = parseInt(hoursStr, 10);
      const minutes = parseInt(minutesStr, 10);

      if (meridiem === 'PM' && hours < 12) hours += 12;
      if (meridiem === 'AM' && hours === 12) hours = 0;

      const formattedHour = String(hours).padStart(2, '0');
      const formattedMin = String(minutes).padStart(2, '0');
      const slotIso = `${dateStr}T${formattedHour}:${formattedMin}:00`;

      const response = await api.createAppointment({
        user_phone: phoneValidation.normalized,
        doctor_id: parseInt(selectedDoctorId, 10),
        slot: slotIso
      });

      setMessage({
        type: 'success',
        text: `Appointment #${response.id} successfully created with ${response.doctor_name || 'doctor'} for ${selectedTime} on ${dateStr}!`,
        field: 'general'
      });

      if (onAppointmentCreated) {
        onAppointmentCreated();
      }
    } catch (err) {
      const field = getApiErrorField(err);
      const formattedError = formatApiErrorMessage(err, 'Booking failed. Please check the details and try again.');
      setMessage({
        type: 'error',
        text: formattedError,
        field: field
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div style={{ padding: '20px 20px 0' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Calendar size={18} color="var(--primary)" /> Direct REST Booking Form (POST /appointments/)
        </h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Submit appointment requests directly using validated REST endpoints.
        </p>
      </div>

      {message && (
        <div className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-error'}`} role="alert">
          {message.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          <span>{typeof message.text === 'string' ? message.text : String(message.text || '')}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="form-grid">
        <div className="form-group">
          <label className="form-label" htmlFor="rest-phone">Patient Phone Number</label>
          <input
            id="rest-phone"
            type="text"
            className="form-input"
            value={phone}
            onChange={(e) => {
              setPhone(e.target.value);
              clearPhoneError();
            }}
            required
            placeholder="+14155552671"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="rest-doctor">Select Doctor</label>
          <select
            id="rest-doctor"
            className="form-select"
            value={selectedDoctorId}
            onChange={(e) => {
              setSelectedDoctorId(e.target.value);
              clearScheduleError();
            }}
            required
          >
            {doctors.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.name} - {doc.specialty}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="rest-date">Appointment Date</label>
          <input
            id="rest-date"
            type="date"
            className="form-input"
            value={dateStr}
            min={new Date().toISOString().split('T')[0]}
            onChange={(e) => {
              setDateStr(e.target.value);
              clearScheduleError();
            }}
            required
          />
        </div>

        <div className="form-group full-width">
          <label className="form-label">
            Available 30-Minute Slots {slotsLoading && '(Refreshing...)'}:
          </label>
          {availableSlots.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '8px 0' }}>
              {slotsLoading ? 'Checking calendar availability...' : 'No available slots remaining on this date.'}
            </p>
          ) : (
            <div className="slots-container">
              {availableSlots.map((slot) => (
                <button
                  type="button"
                  key={slot}
                  className={`slot-pill ${selectedTime === slot ? 'selected' : ''}`}
                  onClick={() => {
                    setSelectedTime(slot);
                    clearScheduleError();
                  }}
                >
                  <Clock size={12} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                  {slot}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="form-group full-width" style={{ marginTop: '10px' }}>
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !selectedTime || !phone.trim()}
            id="rest-book-appointment-btn"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            {loading ? 'Confirming Booking...' : `Book Appointment for ${selectedTime || ''}`}
          </button>
        </div>
      </form>
    </div>
  );
};

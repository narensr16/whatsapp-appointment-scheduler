import React, { useState, useEffect } from 'react';
import { Calendar, RefreshCw, Trash2, Search, Filter, Clock, Phone, UserCheck } from 'lucide-react';
import { api } from '../api';
import { formatApiErrorMessage } from '../utils/errorHandler';

export const AppointmentsList = ({ refreshTrigger, onRefreshNeeded }) => {
  const [appointments, setAppointments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [doctorFilter, setDoctorFilter] = useState('');
  const [phoneSearch, setPhoneSearch] = useState('');

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const params = {};
      if (doctorFilter) params.doctor_id = doctorFilter;
      if (phoneSearch.trim()) params.user_phone = phoneSearch.trim();

      const data = await api.getAppointments(params);
      setAppointments(data);
    } catch (err) {
      console.error('Failed to load appointments:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDoctors = async () => {
    try {
      const docData = await api.getDoctors();
      setDoctors(docData);
    } catch (err) {
      console.error('Failed to load doctors:', err);
    }
  };

  useEffect(() => {
    fetchDoctors();
  }, []);

  useEffect(() => {
    fetchAppointments();
  }, [refreshTrigger, doctorFilter, phoneSearch]);

  const handleCancel = async (id) => {
    if (!window.confirm(`Are you sure you want to cancel appointment #${id}?`)) return;
    try {
      await api.cancelAppointment(id);
      fetchAppointments();
      if (onRefreshNeeded) onRefreshNeeded();
    } catch (err) {
      alert('Failed to cancel appointment: ' + formatApiErrorMessage(err));
    }
  };

  return (
    <div className="card" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calendar size={18} color="var(--primary)" /> Booked Appointments ({appointments.length})
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Live appointments stored in SQLite database
          </p>
        </div>

        <button
          onClick={fetchAppointments}
          disabled={loading}
          className="tab-btn"
          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          id="refresh-appointments-btn"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '200px', display: 'flex', alignItems: 'center', gap: '8px', background: '#F8FAFC', padding: '6px 12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <Search size={14} color="#94A3B8" />
          <input
            placeholder="Search by patient phone..."
            value={phoneSearch}
            onChange={(e) => setPhoneSearch(e.target.value)}
            style={{ border: 'none', background: 'transparent', width: '100%', outline: 'none', fontSize: '0.85rem' }}
          />
        </div>

        <select
          value={doctorFilter}
          onChange={(e) => setDoctorFilter(e.target.value)}
          className="form-select"
          style={{ padding: '6px 12px', fontSize: '0.85rem' }}
        >
          <option value="">All Doctors</option>
          {doctors.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} ({d.specialty})
            </option>
          ))}
        </select>
      </div>

      {/* Appointments Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Patient Phone</th>
              <th>Doctor</th>
              <th>Appointment Slot</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {appointments.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  {loading ? 'Loading appointments...' : 'No appointments booked yet. Use the WhatsApp chat or REST form to book!'}
                </td>
              </tr>
            ) : (
              appointments.map((appt) => {
                const slotDate = new Date(appt.slot);
                const formattedDate = slotDate.toLocaleDateString([], {
                  weekday: 'short',
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                });
                const formattedTime = slotDate.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                });

                return (
                  <tr key={appt.id}>
                    <td style={{ fontWeight: 600, color: 'var(--primary)' }}>#{appt.id}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{appt.user_phone}</td>
                    <td style={{ fontWeight: 500 }}>{appt.doctor_name || `Doctor #${appt.doctor_id}`}</td>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 600 }}>{formattedDate}</span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{formattedTime}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${appt.status === 'CONFIRMED' ? 'badge-confirmed' : 'badge-cancelled'}`}>
                        {appt.status}
                      </span>
                    </td>
                    <td>
                      {appt.status === 'CONFIRMED' && (
                        <button
                          onClick={() => handleCancel(appt.id)}
                          className="btn-danger-outline"
                          title="Cancel Appointment"
                        >
                          <Trash2 size={13} style={{ verticalAlign: 'middle', marginRight: '4px' }} />
                          Cancel
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

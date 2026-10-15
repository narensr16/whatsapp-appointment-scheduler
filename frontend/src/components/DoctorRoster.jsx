import React, { useState, useEffect } from 'react';
import { UserCheck, Clock, Calendar } from 'lucide-react';
import { api } from '../api';

export const DoctorRoster = () => {
  const [doctors, setDoctors] = useState([]);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [slots, setSlots] = useState([]);
  const [dateStr, setDateStr] = useState(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const data = await api.getDoctors();
        setDoctors(data);
        if (data.length > 0) {
          setSelectedDoctor(data[0]);
        }
      } catch (err) {
        console.error('Failed to load doctors:', err);
      }
    };
    fetchDoctors();
  }, []);

  useEffect(() => {
    const fetchSlots = async () => {
      if (!selectedDoctor) return;
      setLoading(true);
      try {
        const data = await api.getDoctorSlots(selectedDoctor.id, dateStr);
        setSlots(data.available_slots || []);
      } catch (err) {
        console.error('Failed to load slots:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSlots();
  }, [selectedDoctor, dateStr]);

  return (
    <div className="card" style={{ padding: '20px' }}>
      <h2 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
        <UserCheck size={18} color="var(--primary)" /> Medical Staff & Available Schedule
      </h2>
      <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
        Active clinic doctors and real-time open slots
      </p>

      {/* Doctor Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
        {doctors.map((doc) => {
          const isSelected = selectedDoctor?.id === doc.id;
          return (
            <div
              key={doc.id}
              onClick={() => setSelectedDoctor(doc)}
              style={{
                padding: '12px',
                borderRadius: '12px',
                border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border-color)'}`,
                background: isSelected ? '#F0FDF4' : '#FFFFFF',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-main)' }}>{doc.name}</div>
              <div style={{ fontSize: '0.78rem', color: 'var(--primary-light)', fontWeight: 500 }}>{doc.specialty}</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                ID: #{doc.id} &bull; {doc.phone || 'No direct phone'}
              </div>
            </div>
          );
        })}
      </div>

      {/* Date selector and available slots for selected doctor */}
      {selectedDoctor && (
        <div style={{ background: '#F8FAFC', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', marginBottom: '12px' }}>
            <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
              Schedule for {selectedDoctor.name}:
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calendar size={14} color="#64748B" />
              <input
                type="date"
                className="form-input"
                style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                value={dateStr}
                min={new Date().toISOString().split('T')[0]}
                onChange={(e) => setDateStr(e.target.value)}
              />
            </div>
          </div>

          {loading ? (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Loading slots...</p>
          ) : slots.length === 0 ? (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              No remaining available slots for {dateStr}.
            </p>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {slots.map((s) => (
                <span
                  key={s}
                  style={{
                    background: '#FFFFFF',
                    border: '1px solid #CBD5E1',
                    borderRadius: '6px',
                    padding: '4px 10px',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                  }}
                >
                  <Clock size={11} style={{ verticalAlign: 'middle', marginRight: '4px', color: '#10B981' }} />
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { WhatsAppChat } from './components/WhatsAppChat';
import { AppointmentsList } from './components/AppointmentsList';
import { DirectBookingForm } from './components/DirectBookingForm';
import { DoctorRoster } from './components/DoctorRoster';
import { ErrorBoundary } from './components/ErrorBoundary';
import { MessageSquare, Calendar, PlusCircle, Users } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState('appointments');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleAppointmentBooked = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="app-container">
      <Navbar />

      <main className="main-content">
        {/* Left Column: Interactive WhatsApp Phone Simulator */}
        <div>
          <div style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <MessageSquare size={18} color="var(--primary)" />
            <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)' }}>
              WhatsApp Webhook Simulator
            </span>
          </div>
          <ErrorBoundary fallbackTitle="WhatsApp Simulator Error">
            <WhatsAppChat onAppointmentBooked={handleAppointmentBooked} />
          </ErrorBoundary>
        </div>

        {/* Right Column: Appointments Dashboard & REST API Controls */}
        <div>
          {/* Tab Selection */}
          <div className="dashboard-tabs">
            <button
              className={`tab-btn ${activeTab === 'appointments' ? 'active' : ''}`}
              onClick={() => setActiveTab('appointments')}
              id="tab-appointments-btn"
            >
              <Calendar size={16} /> Booked Appointments
            </button>
            <button
              className={`tab-btn ${activeTab === 'direct_book' ? 'active' : ''}`}
              onClick={() => setActiveTab('direct_book')}
              id="tab-direct-book-btn"
            >
              <PlusCircle size={16} /> REST Booking Form
            </button>
            <button
              className={`tab-btn ${activeTab === 'doctors' ? 'active' : ''}`}
              onClick={() => setActiveTab('doctors')}
              id="tab-doctors-btn"
            >
              <Users size={16} /> Doctor Roster & Slots
            </button>
          </div>

          {/* Active Tab Content protected by ErrorBoundary */}
          <ErrorBoundary fallbackTitle="Dashboard Section Error">
            {activeTab === 'appointments' && (
              <AppointmentsList
                refreshTrigger={refreshTrigger}
                onRefreshNeeded={handleAppointmentBooked}
              />
            )}

            {activeTab === 'direct_book' && (
              <DirectBookingForm onAppointmentCreated={handleAppointmentBooked} />
            )}

            {activeTab === 'doctors' && <DoctorRoster />}
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
}

export default App;

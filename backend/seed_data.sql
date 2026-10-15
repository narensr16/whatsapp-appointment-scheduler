-- Seed Data for WhatsApp Appointment Scheduler (SQLite)

-- Insert sample doctors if they do not already exist
INSERT OR IGNORE INTO doctors (id, name, specialty, phone, is_active, created_at)
VALUES 
    (1, 'Dr. Alice Smith', 'Cardiology', '+14155550101', 1, CURRENT_TIMESTAMP),
    (2, 'Dr. Bob Jones', 'Pediatrics', '+14155550102', 1, CURRENT_TIMESTAMP),
    (3, 'Dr. Charlie Brown', 'Dermatology', '+14155550103', 1, CURRENT_TIMESTAMP);

-- Insert sample booked appointment for conflict testing
-- Note: Replace with tomorrow's date at 10:00:00 when testing conflicts
INSERT OR IGNORE INTO whatsapp_appointments (id, user_phone, doctor_id, slot, status, created_at)
VALUES 
    (1, '+14155559999', 1, '2026-10-25 10:00:00', 'CONFIRMED', CURRENT_TIMESTAMP);

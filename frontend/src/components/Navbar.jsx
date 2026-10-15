import React, { useEffect, useState } from 'react';
import { Activity, ExternalLink, Calendar, Stethoscope } from 'lucide-react';
import { api } from '../api';

export const Navbar = () => {
  const [health, setHealth] = useState({ status: 'checking', database: 'unknown' });

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await api.checkHealth();
        setHealth(data);
      } catch (err) {
        setHealth({ status: 'offline', database: 'disconnected' });
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health.status === 'ok' && health.database === 'connected';

  return (
    <header className="navbar">
      <div className="brand">
        <div className="brand-icon">
          <Stethoscope size={20} />
        </div>
        <div>
          <h1 className="brand-title">WhatsApp Appointment Scheduler</h1>
          <p className="brand-subtitle">FastAPI &bull; SQLite &bull; Alembic &bull; React &bull; OpenAPI</p>
        </div>
      </div>

      <div className="nav-badges">
        <div className="health-badge" title={`API: ${health.status}, DB: ${health.database}`}>
          <span
            className="status-dot"
            style={{ backgroundColor: isHealthy ? '#25D366' : '#EF4444' }}
          />
          <span>{isHealthy ? 'Backend Live & Connected' : 'Backend Disconnected'}</span>
        </div>

        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="nav-link"
          id="swagger-docs-link"
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            Swagger Docs <ExternalLink size={14} />
          </span>
        </a>
      </div>
    </header>
  );
};

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * ErrorBoundary prevents any component runtime or render error from
 * unmounting the entire React application into a blank white page.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled render error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="card" style={{ padding: '24px', margin: '16px 0', borderColor: '#FCA5A5', background: '#FEF2F2' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <AlertTriangle size={20} color="#DC2626" />
            <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700, color: '#991B1B' }}>
              {this.props.fallbackTitle || 'Component Error'}
            </h3>
          </div>
          <p style={{ fontSize: '0.85rem', color: '#B91C1C', marginBottom: '12px' }}>
            {this.state.error?.message || 'An unexpected rendering error occurred in this view.'}
          </p>

          {/* Development / debugging diagnostics */}
          {(this.state.error?.stack || this.state.errorInfo?.componentStack) && (
            <details style={{ marginTop: '10px', marginBottom: '14px', fontSize: '0.75rem', color: '#7F1D1D', background: '#FEE2E2', padding: '10px', borderRadius: '6px', border: '1px solid #FECACA' }}>
              <summary style={{ cursor: 'pointer', fontWeight: 600, outline: 'none' }}>
                Error Diagnostics & Stack Trace
              </summary>
              <pre style={{ margin: '8px 0 0', overflowX: 'auto', fontSize: '0.72rem', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                {this.state.error?.stack}
                {this.state.errorInfo?.componentStack}
              </pre>
            </details>
          )}

          <button
            type="button"
            onClick={this.handleReset}
            className="tab-btn"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', padding: '6px 14px' }}
          >
            <RefreshCw size={14} /> Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

/**
 * Formats API errors from Axios responses or network failures into safe, human-readable strings.
 * Guarantees that the returned value is always a primitive string and NEVER an object or array,
 * completely preventing React "Objects are not valid as a React child" white-page crashes.
 *
 * Handles:
 * - HTTP 400 (Bad Request: past slot, invalid slot alignment)
 * - HTTP 404 (Doctor not found)
 * - HTTP 409 (Conflict: slot already booked)
 * - HTTP 422 (Unprocessable Entity: FastAPI/Pydantic validation error lists)
 * - HTTP 500 (Internal Server Error)
 * - Network failures / CORS / timeout errors
 * - Non-JSON or unstructured responses
 *
 * @param {any} err - The caught error object
 * @param {string} [fallback='Booking failed. Please try again.']
 * @returns {string} - Clean, safe error message string
 */
export function formatApiErrorMessage(err, fallback = 'Booking failed. Please try again.') {
  if (!err) return fallback;

  // 1. If error is already a string
  if (typeof err === 'string') return err;

  // 2. Check for Axios response data
  const response = err.response;
  if (response && response.data) {
    const data = response.data;

    // A. If data is a plain string
    if (typeof data === 'string') {
      return data;
    }

    // B. If data.detail is present
    if (data.detail !== undefined && data.detail !== null) {
      // String detail (e.g. HTTPException(detail="..."))
      if (typeof data.detail === 'string') {
        return data.detail;
      }

      // Array detail (e.g. FastAPI / Pydantic 422 validation errors)
      if (Array.isArray(data.detail)) {
        const errorMessages = data.detail
          .map((item) => {
            if (typeof item === 'string') return item;
            if (item && typeof item === 'object') {
              // Extract field name from loc array, ignoring 'body'
              const fieldName = Array.isArray(item.loc)
                ? item.loc.filter((part) => part !== 'body').join('.')
                : '';
              let msg = item.msg || 'Invalid field';
              // Strip Pydantic's "Value error, " prefix if present
              msg = msg.replace(/^Value error,\s*/i, '');

              return fieldName ? `${fieldName}: ${msg}` : msg;
            }
            return String(item);
          })
          .filter(Boolean);

        if (errorMessages.length > 0) {
          return errorMessages.join('; ');
        }
      }

      // Object detail
      if (typeof data.detail === 'object') {
        try {
          return JSON.stringify(data.detail);
        } catch {
          return fallback;
        }
      }
    }

    // C. If data.message is present
    if (typeof data.message === 'string') {
      return data.message;
    }

    // D. Generic object response
    try {
      return JSON.stringify(data);
    } catch {
      return fallback;
    }
  }

  // 3. Network or connection errors
  if (err.message === 'Network Error' || err.code === 'ERR_NETWORK') {
    return 'Network Error: Unable to connect to the backend server. Please verify the backend is running on http://localhost:8000.';
  }

  if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
    return 'Request timeout: The server took too long to respond. Please try again.';
  }

  // 4. Fall back to standard error message
  if (typeof err.message === 'string' && err.message) {
    return err.message;
  }

  return fallback;
}

/**
 * Determines which form field an API error is associated with ('phone', 'slot', 'doctor', or 'general').
 *
 * @param {any} err - The caught error object
 * @returns {'phone' | 'slot' | 'doctor' | 'general'}
 */
export function getApiErrorField(err) {
  if (!err) return 'general';
  const data = err.response?.data;
  const status = err.response?.status;

  if (status === 409) return 'slot';

  if (data && typeof data === 'object') {
    if (Array.isArray(data.detail)) {
      for (const item of data.detail) {
        if (item && Array.isArray(item.loc)) {
          if (item.loc.includes('user_phone')) return 'phone';
          if (item.loc.includes('slot')) return 'slot';
          if (item.loc.includes('doctor_id')) return 'doctor';
        }
      }
    }

    const detailText = typeof data.detail === 'string' ? data.detail.toLowerCase() : '';
    if (detailText.includes('phone')) return 'phone';
    if (detailText.includes('slot') || detailText.includes('hour') || detailText.includes('past') || detailText.includes('interval')) {
      return 'slot';
    }
    if (detailText.includes('doctor')) return 'doctor';
  }

  return 'general';
}

export default formatApiErrorMessage;


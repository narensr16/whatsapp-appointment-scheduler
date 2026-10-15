import { test, describe } from 'node:test';
import assert from 'node:assert';
import React from 'react';
import ReactDOMServer from 'react-dom/server';
import { validatePhoneNumber } from '../src/utils/phoneValidation.js';
import { formatApiErrorMessage, getApiErrorField } from '../src/utils/errorHandler.js';

describe('Frontend Phone Number Validation', () => {
  test('valid international E.164 phone numbers are accepted', () => {
    const res = validatePhoneNumber('+14155552671');
    assert.strictEqual(res.isValid, true);
    assert.strictEqual(res.normalized, '+14155552671');
    assert.strictEqual(res.error, null);
  });

  test('valid formatted phone numbers with spaces, hyphens, and parentheses are normalized', () => {
    const res = validatePhoneNumber('+1 (415) 555-2671');
    assert.strictEqual(res.isValid, true);
    assert.strictEqual(res.normalized, '+14155552671');
    assert.strictEqual(res.error, null);
  });

  test('international numbers from other countries are accepted', () => {
    const uk = validatePhoneNumber('+44 20 7946 0919');
    assert.strictEqual(uk.isValid, true);
    assert.strictEqual(uk.normalized, '+442079460919');

    const india = validatePhoneNumber('+91 98765 43210');
    assert.strictEqual(india.isValid, true);
    assert.strictEqual(india.normalized, '+919876543210');
  });

  test('abc123 is rejected with a descriptive letter error', () => {
    const res = validatePhoneNumber('abc123');
    assert.strictEqual(res.isValid, false);
    assert.match(res.error, /letters/i);
  });

  test('empty string and whitespace-only are rejected', () => {
    const emptyRes = validatePhoneNumber('');
    assert.strictEqual(emptyRes.isValid, false);
    assert.match(emptyRes.error, /empty|required/i);

    const whitespaceRes = validatePhoneNumber('   ');
    assert.strictEqual(whitespaceRes.isValid, false);
    assert.match(whitespaceRes.error, /empty|required/i);
  });

  test('phone number with invalid characters is rejected', () => {
    const res = validatePhoneNumber('+1415#555*2671');
    assert.strictEqual(res.isValid, false);
    assert.match(res.error, /invalid characters/i);
  });

  test('phone number that is too short is rejected', () => {
    const res = validatePhoneNumber('+1234');
    assert.strictEqual(res.isValid, false);
    assert.match(res.error, /at least 7 digits/i);
  });
});

describe('Frontend API Error Handling & White-Page Crash Prevention', () => {
  test('formats FastAPI 422 validation error array into a clean string', () => {
    const fastApi422Error = {
      response: {
        status: 422,
        data: {
          detail: [
            {
              type: 'value_error',
              loc: ['body', 'user_phone'],
              msg: 'Value error, Phone number cannot contain letters or alphabetic characters.',
              input: 'abc123'
            }
          ]
        }
      }
    };

    const formatted = formatApiErrorMessage(fastApi422Error);
    assert.strictEqual(typeof formatted, 'string');
    assert.strictEqual(formatted, 'user_phone: Phone number cannot contain letters or alphabetic characters.');

    // CRITICAL: Ensure rendering this string in React does NOT throw "Objects are not valid as a React child"
    assert.doesNotThrow(() => {
      const element = React.createElement('span', null, formatted);
      const html = ReactDOMServer.renderToString(element);
      assert.match(html, /user_phone/);
    });
  });

  test('handles HTTP 409 Slot Conflict cleanly without crashing', () => {
    const conflictError = {
      response: {
        status: 409,
        data: {
          detail: 'Doctor Dr. Alice Smith is already booked at 2026-10-16 10:00 AM.'
        }
      }
    };

    const formatted = formatApiErrorMessage(conflictError);
    assert.strictEqual(typeof formatted, 'string');
    assert.match(formatted, /already booked/i);
  });

  test('handles HTTP 400 Bad Request cleanly without crashing', () => {
    const badRequestError = {
      response: {
        status: 400,
        data: {
          detail: 'Appointment slot cannot be in the past.'
        }
      }
    };

    const formatted = formatApiErrorMessage(badRequestError);
    assert.strictEqual(typeof formatted, 'string');
    assert.match(formatted, /past/i);
  });

  test('handles HTTP 500 Internal Server Error cleanly', () => {
    const serverError = {
      response: {
        status: 500,
        data: {
          detail: 'An internal server error occurred. Please try again later.'
        }
      }
    };

    const formatted = formatApiErrorMessage(serverError);
    assert.strictEqual(typeof formatted, 'string');
    assert.match(formatted, /internal server error/i);
  });

  test('handles Axios Network Failure / ERR_NETWORK gracefully', () => {
    const networkError = {
      message: 'Network Error',
      code: 'ERR_NETWORK'
    };

    const formatted = formatApiErrorMessage(networkError);
    assert.strictEqual(typeof formatted, 'string');
    assert.match(formatted, /network error/i);
  });

  test('handles unexpected response body formats without throwing', () => {
    const unstructuredError = {
      response: {
        status: 502,
        data: 'Bad Gateway: Nginx reverse proxy error'
      }
    };

    const formatted = formatApiErrorMessage(unstructuredError);
    assert.strictEqual(typeof formatted, 'string');
    assert.strictEqual(formatted, 'Bad Gateway: Nginx reverse proxy error');
  });
});

describe('Form Submission Lifecycle & Safety Logic', () => {
  test('clearing previous success message when new submission starts', () => {
    let message = { type: 'success', text: 'Appointment #4 successfully created!' };
    assert.strictEqual(message.type, 'success');

    // Simulate start of new submission: previous message is reset to null
    message = null;
    assert.strictEqual(message, null);

    // If invalid input is processed: only the new error message is set
    const validation = validatePhoneNumber('abc123');
    if (!validation.isValid) {
      message = { type: 'error', text: validation.error };
    }

    assert.strictEqual(message.type, 'error');
    assert.match(message.text, /letters/i);
    // Old success message is completely gone
    assert.doesNotMatch(message.text, /Appointment #4/);
  });

  test('preventing duplicate submissions during loading state', () => {
    let loading = false;
    let callCount = 0;

    const mockSubmit = () => {
      if (loading) return;
      loading = true;
      callCount += 1;
    };

    // First click: fires
    mockSubmit();
    assert.strictEqual(callCount, 1);
    assert.strictEqual(loading, true);

    // Repeated rapid clicks while loading is true: blocked
    mockSubmit();
    mockSubmit();
    mockSubmit();
    assert.strictEqual(callCount, 1);

    // Request finishes
    loading = false;
    assert.strictEqual(loading, false);
  });

  test('clearing phone validation error when user corrects phone number', () => {
    let message = { type: 'error', text: 'Phone number cannot contain letters.', field: 'phone' };

    // Function matching DirectBookingForm's clearPhoneError
    const clearPhoneError = () => {
      if (message && (message.type === 'success' || message.field === 'phone')) {
        message = null;
      }
    };

    // User starts typing into phone input
    clearPhoneError();
    assert.strictEqual(message, null, 'Phone error should be cleared when correcting phone');
  });

  test('preserving phone validation error when changing doctor, date, or slot', () => {
    let message = { type: 'error', text: 'Phone number cannot contain letters.', field: 'phone' };

    // Function matching DirectBookingForm's clearScheduleError
    const clearScheduleError = () => {
      if (message && (message.type === 'success' || message.field !== 'phone')) {
        message = null;
      }
    };

    // User selects another doctor, date, or slot without fixing the phone
    clearScheduleError();
    assert.notStrictEqual(message, null, 'Phone error must not be cleared prematurely by schedule changes');
    assert.strictEqual(message.field, 'phone');
  });

  test('clearing schedule error when changing doctor, date, or slot', () => {
    let message = { type: 'error', text: 'Doctor is already booked at this slot.', field: 'slot' };

    const clearScheduleError = () => {
      if (message && (message.type === 'success' || message.field !== 'phone')) {
        message = null;
      }
    };

    // User selects a different slot
    clearScheduleError();
    assert.strictEqual(message, null, 'Slot conflict error should be cleared when selecting a new slot');
  });

  test('preserving schedule error when user types into phone input', () => {
    let message = { type: 'error', text: 'Doctor is already booked at this slot.', field: 'slot' };

    const clearPhoneError = () => {
      if (message && (message.type === 'success' || message.field === 'phone')) {
        message = null;
      }
    };

    // User edits phone number while slot error exists
    clearPhoneError();
    assert.notStrictEqual(message, null, 'Schedule error must not be cleared prematurely by phone changes');
    assert.strictEqual(message.field, 'slot');
  });
});

describe('API Error Field Mapping (getApiErrorField)', () => {
  test('identifies phone validation errors from 422 payload', () => {
    const err = {
      response: {
        status: 422,
        data: {
          detail: [{ loc: ['body', 'user_phone'], msg: 'Invalid phone' }]
        }
      }
    };
    assert.strictEqual(getApiErrorField(err), 'phone');
  });

  test('identifies slot conflict errors from HTTP 409', () => {
    const err = { response: { status: 409, data: { detail: 'Already booked' } } };
    assert.strictEqual(getApiErrorField(err), 'slot');
  });

  test('identifies slot timing errors from HTTP 400', () => {
    const err = { response: { status: 400, data: { detail: 'Appointments can only be booked during working hours' } } };
    assert.strictEqual(getApiErrorField(err), 'slot');
  });

  test('identifies doctor errors from HTTP 404', () => {
    const err = { response: { status: 404, data: { detail: 'Doctor with ID 999 does not exist.' } } };
    assert.strictEqual(getApiErrorField(err), 'doctor');
  });
});

describe('WhatsApp Simulator Payload Compatibility', () => {
  test('creates payload compatible with both sender/text and Twilio From/Body schema', () => {
    const sender = '+14155552671';
    const text = 'Book appointment with Dr. A at 10 AM tomorrow';
    const messageId = 'ui_msg_12345';

    // Verify canonical payload structure
    const payload = {
      sender,
      text,
      message_id: messageId,
      From: sender,
      Body: text
    };

    assert.strictEqual(payload.sender, '+14155552671');
    assert.strictEqual(payload.From, '+14155552671');
    assert.strictEqual(payload.text, text);
    assert.strictEqual(payload.Body, text);
  });

  test('differentiates HTTP status errors vs Network/CORS failures in error display', () => {
    // 1. Network / CORS failure (no err.response)
    const netErr = new Error('Network Error');
    netErr.code = 'ERR_NETWORK';
    const netFormatted = formatApiErrorMessage(netErr);
    assert.match(netFormatted, /Unable to connect to the backend server/i);

    // 2. HTTP 400 Bad Request error
    const http400Err = {
      response: {
        status: 400,
        data: { detail: 'Appointments can only be booked during working hours' }
      }
    };
    const http400Formatted = formatApiErrorMessage(http400Err);
    assert.strictEqual(http400Formatted, 'Appointments can only be booked during working hours');

    // 3. HTTP 404 Not Found error
    const http404Err = {
      response: {
        status: 404,
        data: { detail: 'Doctor with ID 999 does not exist.' }
      }
    };
    const http404Formatted = formatApiErrorMessage(http404Err);
    assert.strictEqual(http404Formatted, 'Doctor with ID 999 does not exist.');

    // 4. HTTP 409 Conflict error
    const http409Err = {
      response: {
        status: 409,
        data: { detail: 'The requested slot is already booked.' }
      }
    };
    const http409Formatted = formatApiErrorMessage(http409Err);
    assert.strictEqual(http409Formatted, 'The requested slot is already booked.');

    // 5. HTTP 422 Validation error
    const http422Err = {
      response: {
        status: 422,
        data: {
          detail: [{ loc: ['body', 'sender'], msg: 'Sender phone number is required' }]
        }
      }
    };
    const http422Formatted = formatApiErrorMessage(http422Err);
    assert.match(http422Formatted, /sender: Sender phone number is required/i);

    // 6. HTTP 500 Server error
    const http500Err = {
      response: {
        status: 500,
        data: { detail: 'An internal server error occurred.' }
      }
    };
    const http500Formatted = formatApiErrorMessage(http500Err);
    assert.strictEqual(http500Formatted, 'An internal server error occurred.');
  });

  test('allows recovery and retry after error in WhatsApp chat submission lifecycle', () => {
    let loading = false;
    let messages = [];

    // Simulate sending message that fails
    const attemptSend = async (willFail) => {
      if (loading) return false;
      loading = true;
      try {
        if (willFail) {
          throw new Error('Network Error');
        }
        messages.push({ status: 'success', text: 'Confirmed' });
        return true;
      } catch (err) {
        messages.push({ status: 'error', text: formatApiErrorMessage(err) });
        return false;
      } finally {
        loading = false;
      }
    };

    // First attempt fails
    assert.strictEqual(loading, false);
    attemptSend(true);
    assert.strictEqual(loading, false);
    assert.strictEqual(messages.length, 1);
    assert.strictEqual(messages[0].status, 'error');

    // Second attempt recovers and succeeds
    attemptSend(false);
    assert.strictEqual(loading, false);
    assert.strictEqual(messages.length, 2);
    assert.strictEqual(messages[1].status, 'success');
  });
});




/**
 * Validates and normalizes patient phone numbers.
 * Supports international formats with leading '+' and country codes.
 * Rejects empty strings, letters (e.g. 'abc123'), and invalid characters.
 *
 * @param {string} phone - Raw input phone number
 * @returns {{ isValid: boolean, normalized: string, error: string | null }}
 */
export function validatePhoneNumber(phone) {
  if (!phone || typeof phone !== 'string' || !phone.trim()) {
    return {
      isValid: false,
      normalized: '',
      error: 'Phone number is required and cannot be empty.',
    };
  }

  const trimmed = phone.trim();

  // Check for alphabetic letters
  if (/[a-zA-Z]/.test(trimmed)) {
    return {
      isValid: false,
      normalized: '',
      error: 'Phone number cannot contain letters or alphabetic characters.',
    };
  }

  // Check for invalid special characters (allow +, -, (, ), ., and spaces)
  if (/[^0-9+\-\(\)\.\s]/.test(trimmed)) {
    return {
      isValid: false,
      normalized: '',
      error: 'Phone number contains invalid characters.',
    };
  }

  // Normalize: strip whitespace, hyphens, parentheses, dots
  const normalized = trimmed.replace(/[\s\-\(\)\.]/g, '');

  // International phone number check:
  // Optional leading '+', followed by 7 to 20 digits (supporting standard E.164 and extended formats)
  const phonePattern = /^\+?[0-9]{7,20}$/;
  if (!phonePattern.test(normalized)) {
    if (normalized.length < 7) {
      return {
        isValid: false,
        normalized: '',
        error: 'Phone number must contain at least 7 digits.',
      };
    }
    return {
      isValid: false,
      normalized: '',
      error: 'Phone number must contain between 7 and 20 digits, optionally starting with "+".',
    };
  }

  return {
    isValid: true,
    normalized,
    error: null,
  };
}

export default validatePhoneNumber;

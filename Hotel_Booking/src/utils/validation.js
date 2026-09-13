/**
 * Validation utility functions for the Hotel Booking application.
 * All validation is deterministic and predictable for Playwright testing.
 */

/**
 * Validates the home search form fields.
 * @param {object} values - { city, checkIn, checkOut, guests }
 * @returns {object} errors - keyed by field name
 */
export function validateSearchForm(values) {
  const errors = {};
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // City
  if (!values.city || values.city.trim() === '') {
    errors.city = 'City is required.';
  }

  // Check-in
  if (!values.checkIn) {
    errors.checkIn = 'Check-in date is required.';
  } else {
    const checkInDate = new Date(values.checkIn);
    checkInDate.setHours(0, 0, 0, 0);
    if (checkInDate < today) {
      errors.checkIn = 'Check-in date must be today or a future date.';
    }
  }

  // Check-out
  if (!values.checkOut) {
    errors.checkOut = 'Check-out date is required.';
  } else if (values.checkIn) {
    const checkInDate = new Date(values.checkIn);
    const checkOutDate = new Date(values.checkOut);
    checkInDate.setHours(0, 0, 0, 0);
    checkOutDate.setHours(0, 0, 0, 0);
    if (checkOutDate <= checkInDate) {
      errors.checkOut = 'Check-out date must be after check-in date.';
    }
  }

  // Guests
  if (!values.guests && values.guests !== 0) {
    errors.guests = 'Number of guests is required.';
  } else {
    const guestsNum = Number(values.guests);
    if (isNaN(guestsNum) || guestsNum < 1 || guestsNum > 10) {
      errors.guests = 'Number of guests must be between 1 and 10.';
    }
  }

  return errors;
}

/**
 * Validates the booking form fields.
 * @param {object} values - all booking form fields
 * @returns {object} errors - keyed by field name
 */
export function validateBookingForm(values) {
  const errors = {};
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // First Name
  if (!values.firstName || values.firstName.trim() === '') {
    errors.firstName = 'First name is required.';
  } else if (values.firstName.trim().length < 2) {
    errors.firstName = 'First name must be at least 2 characters.';
  }

  // Last Name
  if (!values.lastName || values.lastName.trim() === '') {
    errors.lastName = 'Last name is required.';
  } else if (values.lastName.trim().length < 2) {
    errors.lastName = 'Last name must be at least 2 characters.';
  }

  // Email
  if (!values.email || values.email.trim() === '') {
    errors.email = 'Email is required.';
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(values.email.trim())) {
      errors.email = 'Please enter a valid email address.';
    }
  }

  // Phone
  if (!values.phone || values.phone.trim() === '') {
    errors.phone = 'Phone number is required.';
  } else {
    const phoneDigits = values.phone.trim();
    if (/[^0-9]/.test(phoneDigits)) {
      errors.phone = 'Phone number must contain only digits.';
    } else if (phoneDigits.length !== 10) {
      errors.phone = 'Phone number must contain exactly 10 digits.';
    }
  }

  // Check-in
  if (!values.checkIn) {
    errors.checkIn = 'Check-in date is required.';
  } else {
    const checkInDate = new Date(values.checkIn);
    checkInDate.setHours(0, 0, 0, 0);
    if (checkInDate < today) {
      errors.checkIn = 'Check-in date must be today or a future date.';
    }
  }

  // Check-out
  if (!values.checkOut) {
    errors.checkOut = 'Check-out date is required.';
  } else if (values.checkIn) {
    const checkInDate = new Date(values.checkIn);
    const checkOutDate = new Date(values.checkOut);
    checkInDate.setHours(0, 0, 0, 0);
    checkOutDate.setHours(0, 0, 0, 0);
    if (checkOutDate <= checkInDate) {
      errors.checkOut = 'Check-out date must be after check-in date.';
    }
  }

  // Guests
  if (!values.guests && values.guests !== 0) {
    errors.guests = 'Number of guests is required.';
  } else {
    const guestsNum = Number(values.guests);
    if (isNaN(guestsNum) || !Number.isInteger(guestsNum) || guestsNum < 1 || guestsNum > 10) {
      errors.guests = 'Number of guests must be between 1 and 10.';
    }
  }

  // Special Requests
  if (values.specialRequests && values.specialRequests.length > 500) {
    errors.specialRequests = 'Special requests must be 500 characters or fewer.';
  }

  // Card Number
  if (!values.cardNumber || values.cardNumber.trim() === '') {
    errors.cardNumber = 'Card number is required.';
  } else {
    const cardDigits = values.cardNumber.trim().replace(/\s/g, '');
    if (/[^0-9]/.test(cardDigits)) {
      errors.cardNumber = 'Card number must contain only digits.';
    } else if (cardDigits.length !== 16) {
      errors.cardNumber = 'Card number must contain exactly 16 digits.';
    }
  }

  // Expiry
  if (!values.expiry || values.expiry.trim() === '') {
    errors.expiry = 'Expiry date is required.';
  } else {
    const expiryRegex = /^(0[1-9]|1[0-2])\/([0-9]{2})$/;
    const match = values.expiry.trim().match(expiryRegex);
    if (!match) {
      errors.expiry = 'Expiry date must be in MM/YY format.';
    } else {
      const month = parseInt(match[1], 10);
      const year = parseInt(match[2], 10) + 2000;
      const now = new Date();
      const currentMonth = now.getMonth() + 1;
      const currentYear = now.getFullYear();
      if (year < currentYear || (year === currentYear && month < currentMonth)) {
        errors.expiry = 'Card has expired.';
      }
    }
  }

  // CVV
  if (!values.cvv || values.cvv.trim() === '') {
    errors.cvv = 'CVV is required.';
  } else {
    const cvvDigits = values.cvv.trim();
    if (/[^0-9]/.test(cvvDigits)) {
      errors.cvv = 'CVV must contain only digits.';
    } else if (cvvDigits.length !== 3) {
      errors.cvv = 'CVV must contain exactly 3 digits.';
    }
  }

  return errors;
}

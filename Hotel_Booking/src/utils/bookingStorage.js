/**
 * Booking storage utility for localStorage operations.
 * Uses the key "hotelBookings" for all booking data.
 */

const STORAGE_KEY = 'hotelBookings';

/**
 * Generates a unique booking reference in the format BK-XXXXXX.
 * @returns {string} A booking reference like "BK-928341"
 */
export function generateBookingReference() {
  const digits = Math.floor(100000 + Math.random() * 900000);
  return `BK-${digits}`;
}

/**
 * Retrieves all bookings from localStorage.
 * @returns {Array} Array of booking objects
 */
export function getBookings() {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) return [];
    return JSON.parse(data);
  } catch (error) {
    console.error('Error reading bookings from localStorage:', error);
    return [];
  }
}

/**
 * Saves a new booking to localStorage.
 * @param {object} booking - The booking object to save
 * @returns {object} The saved booking with id and reference number
 */
export function saveBooking(booking) {
  try {
    const bookings = getBookings();
    const newBooking = {
      ...booking,
      id: Date.now(),
      referenceNumber: generateBookingReference(),
      bookingStatus: 'Confirmed',
      createdAt: new Date().toISOString()
    };
    bookings.push(newBooking);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(bookings));
    return newBooking;
  } catch (error) {
    console.error('Error saving booking to localStorage:', error);
    return null;
  }
}

/**
 * Gets a single booking by its reference number.
 * @param {string} referenceNumber - The booking reference to find
 * @returns {object|null} The booking object or null
 */
export function getBookingByReference(referenceNumber) {
  const bookings = getBookings();
  return bookings.find(b => b.referenceNumber === referenceNumber) || null;
}

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validateBookingForm } from '../utils/validation';
import { saveBooking } from '../utils/bookingStorage';
import ErrorMessage from './ErrorMessage';

export default function BookingForm({ room }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    checkIn: '',
    checkOut: '',
    guests: '',
    specialRequests: '',
    cardNumber: '',
    expiry: '',
    cvv: ''
  });
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const validationErrors = validateBookingForm(formData);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    // Create and save booking
    const booking = {
      roomId: room.id,
      hotelName: room.name,
      roomType: room.roomType,
      firstName: formData.firstName.trim(),
      lastName: formData.lastName.trim(),
      email: formData.email.trim(),
      phone: formData.phone.trim(),
      checkIn: formData.checkIn,
      checkOut: formData.checkOut,
      guests: Number(formData.guests),
      specialRequests: formData.specialRequests.trim()
    };

    const savedBooking = saveBooking(booking);

    if (savedBooking) {
      // Store the last booking reference for the confirmation page
      sessionStorage.setItem('lastBooking', JSON.stringify(savedBooking));
      navigate('/confirmation');
    }
  };

  return (
    <form className="booking-form-card" onSubmit={handleSubmit} noValidate>
      {/* Guest Information */}
      <div className="form-section">
        <h3 className="form-section-title">
          <span className="form-section-icon">👤</span>
          Guest Information
        </h3>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label" htmlFor="firstName">First Name</label>
            <input
              id="firstName"
              name="firstName"
              type="text"
              className={`form-input ${errors.firstName ? 'error' : ''}`}
              placeholder="John"
              value={formData.firstName}
              onChange={handleChange}
              data-testid="first-name-input"
              autoComplete="given-name"
            />
            <ErrorMessage message={errors.firstName} testId="first-name-error" />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="lastName">Last Name</label>
            <input
              id="lastName"
              name="lastName"
              type="text"
              className={`form-input ${errors.lastName ? 'error' : ''}`}
              placeholder="Doe"
              value={formData.lastName}
              onChange={handleChange}
              data-testid="last-name-input"
              autoComplete="family-name"
            />
            <ErrorMessage message={errors.lastName} testId="last-name-error" />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              className={`form-input ${errors.email ? 'error' : ''}`}
              placeholder="john@example.com"
              value={formData.email}
              onChange={handleChange}
              data-testid="email-input"
              autoComplete="email"
            />
            <ErrorMessage message={errors.email} testId="email-error" />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="phone">Phone</label>
            <input
              id="phone"
              name="phone"
              type="tel"
              className={`form-input ${errors.phone ? 'error' : ''}`}
              placeholder="1234567890"
              value={formData.phone}
              onChange={handleChange}
              data-testid="phone-input"
              autoComplete="tel"
            />
            <ErrorMessage message={errors.phone} testId="phone-error" />
          </div>
        </div>
      </div>

      {/* Stay Details */}
      <div className="form-section">
        <h3 className="form-section-title">
          <span className="form-section-icon">📅</span>
          Stay Details
        </h3>
        <div className="form-grid">
          <div className="form-group">
            <label className="form-label" htmlFor="bookingCheckIn">Check-in Date</label>
            <input
              id="bookingCheckIn"
              name="checkIn"
              type="date"
              className={`form-input ${errors.checkIn ? 'error' : ''}`}
              value={formData.checkIn}
              onChange={handleChange}
              data-testid="booking-checkin-input"
            />
            <ErrorMessage message={errors.checkIn} testId="booking-checkin-error" />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="bookingCheckOut">Check-out Date</label>
            <input
              id="bookingCheckOut"
              name="checkOut"
              type="date"
              className={`form-input ${errors.checkOut ? 'error' : ''}`}
              value={formData.checkOut}
              onChange={handleChange}
              data-testid="booking-checkout-input"
            />
            <ErrorMessage message={errors.checkOut} testId="booking-checkout-error" />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="bookingGuests">Number of Guests</label>
            <input
              id="bookingGuests"
              name="guests"
              type="number"
              min="1"
              max="10"
              className={`form-input ${errors.guests ? 'error' : ''}`}
              placeholder="Number of guests"
              value={formData.guests}
              onChange={handleChange}
              data-testid="booking-guests-input"
            />
            <ErrorMessage message={errors.guests} testId="booking-guests-error" />
          </div>

          <div className="form-group full-width">
            <label className="form-label" htmlFor="specialRequests">Special Requests (Optional)</label>
            <textarea
              id="specialRequests"
              name="specialRequests"
              className={`form-input form-textarea ${errors.specialRequests ? 'error' : ''}`}
              placeholder="Any special requirements or preferences..."
              value={formData.specialRequests}
              onChange={handleChange}
              data-testid="special-requests-input"
              maxLength={500}
            />
            <ErrorMessage message={errors.specialRequests} testId="special-requests-error" />
            <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
              {formData.specialRequests.length}/500 characters
            </p>
          </div>
        </div>
      </div>

      {/* Payment Information */}
      <div className="form-section">
        <h3 className="form-section-title">
          <span className="form-section-icon">💳</span>
          Payment Information
        </h3>
        <div className="form-grid">
          <div className="form-group full-width">
            <label className="form-label" htmlFor="cardNumber">Card Number</label>
            <input
              id="cardNumber"
              name="cardNumber"
              type="text"
              className={`form-input ${errors.cardNumber ? 'error' : ''}`}
              placeholder="1234567890123456"
              value={formData.cardNumber}
              onChange={handleChange}
              data-testid="card-number-input"
              autoComplete="cc-number"
              maxLength={16}
            />
            <ErrorMessage message={errors.cardNumber} testId="card-error" />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="expiry">Expiry Date</label>
            <input
              id="expiry"
              name="expiry"
              type="text"
              className={`form-input ${errors.expiry ? 'error' : ''}`}
              placeholder="MM/YY"
              value={formData.expiry}
              onChange={handleChange}
              data-testid="expiry-input"
              autoComplete="cc-exp"
              maxLength={5}
            />
            <ErrorMessage message={errors.expiry} testId="expiry-error" />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="cvv">CVV</label>
            <input
              id="cvv"
              name="cvv"
              type="text"
              className={`form-input ${errors.cvv ? 'error' : ''}`}
              placeholder="123"
              value={formData.cvv}
              onChange={handleChange}
              data-testid="cvv-input"
              autoComplete="cc-csc"
              maxLength={3}
            />
            <ErrorMessage message={errors.cvv} testId="cvv-error" />
          </div>
        </div>
      </div>

      <button
        type="submit"
        className="btn btn-success btn-large btn-full"
        data-testid="confirm-booking-button"
      >
        ✓ Confirm Booking
      </button>
    </form>
  );
}

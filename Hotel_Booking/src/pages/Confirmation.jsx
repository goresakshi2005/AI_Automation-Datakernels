import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { formatDate } from '../utils/formatDate';

export default function Confirmation() {
  const [booking, setBooking] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    try {
      const lastBooking = sessionStorage.getItem('lastBooking');
      if (lastBooking) {
        setBooking(JSON.parse(lastBooking));
      }
    } catch (error) {
      console.error('Error reading last booking:', error);
    }
  }, []);

  if (!booking) {
    return (
      <div className="confirmation-page" data-testid="confirmation-page">
        <div className="not-found">
          <div className="not-found-icon">❓</div>
          <h1 className="not-found-title">No booking found</h1>
          <p className="not-found-text">
            There is no recent booking to confirm. Please make a booking first.
          </p>
          <Link to="/" className="btn btn-primary" data-testid="back-to-home">
            ← Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="confirmation-page" data-testid="confirmation-page">
      <div className="confirmation-card" data-testid="booking-confirmation">
        <div className="confirmation-icon">🎉</div>
        <h1 className="confirmation-title">Booking Confirmed!</h1>
        <p className="confirmation-subtitle">
          Thank you, {booking.firstName}! Your reservation has been confirmed.
        </p>

        <div className="confirmation-status">
          ✓ {booking.bookingStatus}
        </div>

        <div className="confirmation-details">
          <div className="confirmation-detail-row">
            <span className="confirmation-detail-label">Hotel</span>
            <span className="confirmation-detail-value">{booking.hotelName}</span>
          </div>
          <div className="confirmation-detail-row">
            <span className="confirmation-detail-label">Room Type</span>
            <span className="confirmation-detail-value">{booking.roomType}</span>
          </div>
          <div className="confirmation-detail-row">
            <span className="confirmation-detail-label">Check-in</span>
            <span className="confirmation-detail-value">{formatDate(booking.checkIn)}</span>
          </div>
          <div className="confirmation-detail-row">
            <span className="confirmation-detail-label">Check-out</span>
            <span className="confirmation-detail-value">{formatDate(booking.checkOut)}</span>
          </div>
          <div className="confirmation-detail-row">
            <span className="confirmation-detail-label">Guests</span>
            <span className="confirmation-detail-value">
              {booking.guests} {booking.guests === 1 ? 'Guest' : 'Guests'}
            </span>
          </div>
          <div className="confirmation-detail-row">
            <span className="confirmation-detail-label">Guest</span>
            <span className="confirmation-detail-value">
              {booking.firstName} {booking.lastName}
            </span>
          </div>
        </div>

        <div className="confirmation-reference">
          <p className="confirmation-reference-label">Booking Reference</p>
          <p className="confirmation-reference-number" data-testid="booking-reference">
            {booking.referenceNumber}
          </p>
        </div>

        <Link
          to="/bookings"
          className="btn btn-primary btn-large"
          data-testid="view-bookings-button"
        >
          View My Bookings
        </Link>
      </div>
    </div>
  );
}

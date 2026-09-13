import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getBookings } from '../utils/bookingStorage';
import BookingCard from '../components/BookingCard';

export default function Bookings() {
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    const storedBookings = getBookings();
    // Show newest first
    setBookings(storedBookings.reverse());
  }, []);

  return (
    <div data-testid="bookings-page">
      <h1 className="bookings-title">My Bookings</h1>

      {bookings.length === 0 ? (
        <div className="empty-state" data-testid="no-bookings">
          <div className="empty-state-icon">📋</div>
          <h2 className="empty-state-title">No bookings found.</h2>
          <p className="empty-state-text">
            You haven&apos;t made any bookings yet. Start exploring hotels!
          </p>
          <Link to="/" className="btn btn-primary" data-testid="start-booking">
            Find Hotels
          </Link>
        </div>
      ) : (
        <div className="bookings-grid">
          {bookings.map((booking) => (
            <BookingCard
              key={booking.id}
              booking={booking}
            />
          ))}
        </div>
      )}
    </div>
  );
}

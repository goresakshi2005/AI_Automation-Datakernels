import { formatDateShort } from '../utils/formatDate';

export default function BookingCard({ booking }) {
  const testIdSuffix = booking.referenceNumber || booking.id;

  return (
    <article
      className="booking-card"
      data-testid={`booking-card-${testIdSuffix}`}
    >
      <div className="booking-card-info">
        <span className="booking-card-ref">
          Booking: {booking.referenceNumber}
        </span>
        <h3 className="booking-card-hotel">{booking.hotelName}</h3>
        <p className="booking-card-room">{booking.roomType}</p>
        <p className="booking-card-dates">
          📅 {formatDateShort(booking.checkIn)} → {formatDateShort(booking.checkOut)}
        </p>
        <p className="booking-card-guests">
          👥 {booking.guests} {booking.guests === 1 ? 'Guest' : 'Guests'}
        </p>
      </div>
      <span className="booking-card-status">
        ✓ {booking.bookingStatus}
      </span>
    </article>
  );
}

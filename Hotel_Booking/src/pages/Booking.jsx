import { useParams, Link } from 'react-router-dom';
import rooms from '../data/rooms';
import BookingForm from '../components/BookingForm';

export default function Booking() {
  const { id } = useParams();
  const room = rooms.find(r => r.id === Number(id));

  if (!room) {
    return (
      <div className="booking-page" data-testid="booking-page">
        <div className="not-found">
          <div className="not-found-icon">🚫</div>
          <h1 className="not-found-title">Room not found</h1>
          <p className="not-found-text">
            The room you&apos;re trying to book doesn&apos;t exist.
          </p>
          <Link to="/search" className="btn btn-primary" data-testid="back-to-search">
            ← Back to Search
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="booking-page" data-testid="booking-page">
      <Link to={`/room/${room.id}`} className="btn-back" data-testid="back-to-room">
        ← Back to Room Details
      </Link>

      <h1 style={{ fontSize: '1.875rem', fontWeight: 800, marginBottom: '1.5rem' }}>
        Complete Your Booking
      </h1>

      <div className="booking-room-summary" data-testid="booking-room-summary">
        <img
          className="booking-room-image"
          src={room.image}
          alt={`${room.name} - ${room.roomType}`}
        />
        <div className="booking-room-info">
          <h2>{room.name}</h2>
          <p>{room.roomType}</p>
          <p className="price-tag">${room.price} / night</p>
        </div>
      </div>

      <BookingForm room={room} />
    </div>
  );
}

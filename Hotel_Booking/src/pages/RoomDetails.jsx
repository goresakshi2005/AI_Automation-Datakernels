import { useParams, Link } from 'react-router-dom';
import rooms from '../data/rooms';

export default function RoomDetails() {
  const { id } = useParams();
  const room = rooms.find(r => r.id === Number(id));

  if (!room) {
    return (
      <div data-testid="room-details-page">
        <div className="not-found">
          <div className="not-found-icon">🚫</div>
          <h1 className="not-found-title">Room not found</h1>
          <p className="not-found-text">
            The room you&apos;re looking for doesn&apos;t exist or has been removed.
          </p>
          <Link to="/search" className="btn btn-primary" data-testid="back-to-search">
            ← Back to Search
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="room-details" data-testid="room-details-page">
      <Link to="/search" className="btn-back" data-testid="back-to-search">
        ← Back to Search Results
      </Link>

      <img
        className="room-details-image"
        src={room.image}
        alt={`${room.name} - ${room.roomType}`}
      />

      <div className="room-details-header">
        <div className="room-details-info">
          <h1 data-testid="room-name">{room.name}</h1>
          <p className="room-details-type" data-testid="room-type">{room.roomType}</p>
        </div>
        <div className="room-details-price-card">
          <div className="room-details-price" data-testid="room-price">${room.price}</div>
          <div className="room-details-price-label">per night</div>
        </div>
      </div>

      <p className="room-details-description">{room.description}</p>

      <h2 className="room-details-amenities-title">Amenities</h2>
      <ul className="room-details-amenities" data-testid="amenities-list">
        {room.amenities.map((amenity, index) => (
          <li key={index} className="room-details-amenity">
            <span className="amenity-check">✓</span>
            {amenity}
          </li>
        ))}
      </ul>

      <Link
        to={`/book/${room.id}`}
        className="btn btn-success btn-large btn-full"
        data-testid="book-now-button"
      >
        Book Now
      </Link>
    </div>
  );
}

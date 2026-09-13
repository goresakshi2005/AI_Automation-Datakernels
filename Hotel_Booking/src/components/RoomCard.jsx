import { Link } from 'react-router-dom';

export default function RoomCard({ room }) {
  return (
    <article className="room-card" data-testid={`room-card-${room.id}`}>
      <img
        className="room-card-image"
        src={room.image}
        alt={`${room.name} - ${room.roomType}`}
        loading="lazy"
      />
      <div className="room-card-body">
        <div className="room-card-header">
          <h3 className="room-card-name">{room.name}</h3>
          <span className="room-card-rating">
            ⭐ {room.rating}
          </span>
        </div>
        <p className="room-card-type">{room.roomType}</p>
        <p className="room-card-price">
          ${room.price} <span>/ night</span>
        </p>
        <ul className="room-card-amenities" aria-label="Amenities">
          {room.amenities.map((amenity, index) => (
            <li key={index} className="amenity-tag">{amenity}</li>
          ))}
        </ul>
        <Link
          to={`/room/${room.id}`}
          className="btn btn-primary btn-full"
          data-testid={`view-details-${room.id}`}
        >
          View Details
        </Link>
      </div>
    </article>
  );
}

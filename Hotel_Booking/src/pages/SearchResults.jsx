import { useSearchParams, Link } from 'react-router-dom';
import rooms from '../data/rooms';
import RoomCard from '../components/RoomCard';
import { formatDate } from '../utils/formatDate';

export default function SearchResults() {
  const [searchParams] = useSearchParams();

  const city = searchParams.get('city') || '';
  const checkIn = searchParams.get('checkIn') || '';
  const checkOut = searchParams.get('checkOut') || '';
  const guests = searchParams.get('guests') || '';

  const hasValidParams = city && checkIn && checkOut && guests;

  if (!hasValidParams) {
    return (
      <div data-testid="search-results-page">
        <div className="not-found">
          <div className="not-found-icon">🔍</div>
          <h1 className="not-found-title">Please enter valid search details.</h1>
          <p className="not-found-text">
            Use the search form to find available hotels.
          </p>
          <Link to="/" className="btn btn-primary" data-testid="back-to-home">
            ← Back to Home
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="search-results-page">
      <Link to="/" className="btn-back" data-testid="back-to-home">
        ← Back to Home
      </Link>

      <div className="search-header">
        <h1 className="search-title">Search Results</h1>
        <div className="search-meta">
          <span className="search-meta-item">📍 {city}</span>
          <span className="search-meta-item">📅 {formatDate(checkIn)} → {formatDate(checkOut)}</span>
          <span className="search-meta-item">👥 {guests} {Number(guests) === 1 ? 'Guest' : 'Guests'}</span>
        </div>
      </div>

      <div className="rooms-grid" data-testid="rooms-list">
        {rooms.map(room => (
          <RoomCard key={room.id} room={room} />
        ))}
      </div>
    </div>
  );
}

import { Link, NavLink } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="navbar" data-testid="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo" data-testid="navbar-logo">
          <span className="navbar-logo-icon">🏨</span>
          StayBooker
        </Link>
        <div className="navbar-links">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            data-testid="nav-home"
          >
            Home
          </NavLink>
          <NavLink
            to="/bookings"
            className={({ isActive }) => `navbar-link ${isActive ? 'active' : ''}`}
            data-testid="nav-bookings"
          >
            My Bookings
          </NavLink>
        </div>
      </div>
    </nav>
  );
}

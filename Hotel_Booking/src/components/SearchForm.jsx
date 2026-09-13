import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validateSearchForm } from '../utils/validation';
import ErrorMessage from './ErrorMessage';

export default function SearchForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    city: '',
    checkIn: '',
    checkOut: '',
    guests: ''
  });
  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const validationErrors = validateSearchForm({
      city: formData.city,
      checkIn: formData.checkIn,
      checkOut: formData.checkOut,
      guests: formData.guests
    });

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    // Navigate with query parameters
    const params = new URLSearchParams({
      city: formData.city.trim(),
      checkIn: formData.checkIn,
      checkOut: formData.checkOut,
      guests: formData.guests
    });

    navigate(`/search?${params.toString()}`);
  };

  return (
    <form className="search-form-card" onSubmit={handleSubmit} noValidate>
      <h2 className="search-form-title">Find Your Perfect Stay</h2>
      <div className="form-grid">
        <div className="form-group full-width">
          <label className="form-label" htmlFor="city">City</label>
          <input
            id="city"
            name="city"
            type="text"
            className={`form-input ${errors.city ? 'error' : ''}`}
            placeholder="Where are you going?"
            value={formData.city}
            onChange={handleChange}
            data-testid="city-input"
            autoComplete="off"
          />
          <ErrorMessage message={errors.city} testId="city-error" />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="checkIn">Check-in</label>
          <input
            id="checkIn"
            name="checkIn"
            type="date"
            className={`form-input ${errors.checkIn ? 'error' : ''}`}
            value={formData.checkIn}
            onChange={handleChange}
            data-testid="checkin-input"
          />
          <ErrorMessage message={errors.checkIn} testId="checkin-error" />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="checkOut">Check-out</label>
          <input
            id="checkOut"
            name="checkOut"
            type="date"
            className={`form-input ${errors.checkOut ? 'error' : ''}`}
            value={formData.checkOut}
            onChange={handleChange}
            data-testid="checkout-input"
          />
          <ErrorMessage message={errors.checkOut} testId="checkout-error" />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="guests">Guests</label>
          <input
            id="guests"
            name="guests"
            type="number"
            min="1"
            max="10"
            className={`form-input ${errors.guests ? 'error' : ''}`}
            placeholder="Number of guests"
            value={formData.guests}
            onChange={handleChange}
            data-testid="guests-input"
          />
          <ErrorMessage message={errors.guests} testId="guests-error" />
        </div>

        <div className="form-group full-width">
          <button
            type="submit"
            className="btn btn-primary btn-large btn-full"
            data-testid="search-button"
          >
            🔍 Search Hotels
          </button>
        </div>
      </div>
    </form>
  );
}

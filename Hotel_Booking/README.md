# AI-Powered Automated Testing System - Part 1

This is the completed Part 1 of the hiring assignment: **Hotel Booking Website**.

## 1. Project Overview

This is a responsive, client-side only React application for booking hotel rooms. It serves as the foundation for future automated testing using Python and Playwright. The application is built to be highly testable with predictable data, stable selectors, and deterministic validation.

## 2. Technology Stack

- React (v18)
- Vite
- React Router (v6)
- JavaScript (.js / .jsx only)
- CSS (Custom properties, no external frameworks)
- localStorage for data persistence

*Note: As per requirements, no TypeScript, real APIs, databases, or backend servers were used.*

## 3. Features

- **Search Hotels**: Filter available rooms by city, dates, and guests.
- **View Rooms**: Browse a list of available rooms with their amenities and pricing.
- **Room Details**: View in-depth information about a specific room.
- **Booking Flow**: Complete a detailed booking form with rigorous validation.
- **Confirmation**: Receive a unique booking reference upon successful booking.
- **My Bookings**: View a history of all bookings stored locally.

## 4. Project Structure

```text
src/
├── components/
│   ├── BookingCard.jsx    # Card displaying a confirmed booking
│   ├── BookingForm.jsx    # The main booking form with validation
│   ├── ErrorMessage.jsx   # Reusable validation error display
│   ├── Navbar.jsx         # Main navigation
│   ├── RoomCard.jsx       # Card displaying room summary in search results
│   └── SearchForm.jsx     # The home page search form
├── data/
│   └── rooms.js           # Static mock data for hotels/rooms
├── pages/
│   ├── Booking.jsx        # /book/:id page
│   ├── Bookings.jsx       # /bookings page
│   ├── Confirmation.jsx   # /confirmation page
│   ├── Home.jsx           # / (Home) page
│   ├── RoomDetails.jsx    # /room/:id page
│   └── SearchResults.jsx  # /search page
├── utils/
│   ├── bookingStorage.js  # localStorage operations and reference generation
│   ├── formatDate.js      # Date formatting utilities
│   └── validation.js      # Centralized, deterministic validation rules
├── App.jsx                # Main application component and routing
├── index.css              # Global styles and design system
└── main.jsx               # Application entry point
```

## 5. Installation

To install the project dependencies, run:

```bash
npm install
```

## 6. How to Run

To start the development server, run:

```bash
npm run dev
```

The application will be available at `http://localhost:5173`.

## 7. Available Routes

1. **Home**: `/`
2. **Search Results**: `/search` (uses query parameters like `?city=New York&checkIn=...`)
3. **Room Details**: `/room/:id`
4. **Booking Form**: `/book/:id`
5. **Confirmation**: `/confirmation`
6. **My Bookings**: `/bookings`

## 8. Validation Rules

The application implements strict, deterministic validation exactly as requested:

- **First/Last Name**: Required, minimum 2 characters.
- **Email**: Required, valid format.
- **Phone**: Required, exactly 10 digits.
- **Check-in**: Required, today or future.
- **Check-out**: Required, after check-in.
- **Guests**: Required, between 1 and 10.
- **Special Requests**: Optional, max 500 characters.
- **Card Number**: Required, exactly 16 digits.
- **Expiry**: Required, MM/YY format, must not be expired.
- **CVV**: Required, exactly 3 digits.

## 9. Booking Flow

1. User searches on `/` -> Navigates to `/search?params...`
2. User selects a room -> Navigates to `/room/:id`
3. User clicks Book Now -> Navigates to `/book/:id`
4. User fills valid form -> Booking saved to localStorage, Reference generated -> Navigates to `/confirmation`
5. User clicks View My Bookings -> Navigates to `/bookings`

## 10. localStorage Structure

Data is stored under the key `"hotelBookings"` as an array of objects:

```json
[
  {
    "id": 1694602352355,
    "referenceNumber": "BK-582910",
    "roomId": 1,
    "hotelName": "Grand Hotel",
    "roomType": "Deluxe Room",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "phone": "1234567890",
    "checkIn": "2026-09-20",
    "checkOut": "2026-09-23",
    "guests": 2,
    "specialRequests": "Late check-in",
    "bookingStatus": "Confirmed",
    "createdAt": "2026-09-13T10:52:32.355Z"
  }
]
```

## 11. Playwright Testability Considerations

This application is designed specifically for future automated testing:
- **`data-testid` Attributes**: Every important interactive element, input, and error message has a stable, unique `data-testid`.
- **Deterministic Validation**: Validation logic does not rely on random factors or complex external state (other than the current date).
- **Predictable Storage**: `localStorage` is used predictably without complex state hydration issues.
- **URL Navigation**: Search parameters are passed via the URL (`/search?city=...`) to allow direct deep-linking during tests.
- **Semantic HTML**: Proper `<form>`, `<input>`, and `<button>` elements are used instead of custom div-based components.

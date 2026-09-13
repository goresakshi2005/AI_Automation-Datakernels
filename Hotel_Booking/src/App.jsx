import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import SearchResults from './pages/SearchResults';
import RoomDetails from './pages/RoomDetails';
import Booking from './pages/Booking';
import Confirmation from './pages/Confirmation';
import Bookings from './pages/Bookings';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main className="page-container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/search" element={<SearchResults />} />
          <Route path="/room/:id" element={<RoomDetails />} />
          <Route path="/book/:id" element={<Booking />} />
          <Route path="/confirmation" element={<Confirmation />} />
          <Route path="/bookings" element={<Bookings />} />
        </Routes>
      </main>
      <footer className="footer">
        <p>© 2026 StayBooker. All rights reserved.</p>
      </footer>
    </BrowserRouter>
  );
}

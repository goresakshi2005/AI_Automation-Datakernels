import SearchForm from '../components/SearchForm';

export default function Home() {
  return (
    <div data-testid="home-page">
      <section className="hero-section">
        <div className="hero-content">
          <h1 className="hero-title">Find Your Perfect Stay</h1>
          <p className="hero-subtitle">
            Discover amazing hotels at the best prices. Book your dream getaway today.
          </p>
        </div>
      </section>
      <SearchForm />
    </div>
  );
}

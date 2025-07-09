import { Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import SummaryDetail from './pages/SummaryDetail';
import Header from './components/Header';
import Footer from './components/Footer';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <Header />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/story/:id" element={<SummaryDetail />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

export default App;

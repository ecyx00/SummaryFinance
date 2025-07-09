import './Footer.css';

function Footer() {
  const year = new Date().getFullYear();
  
  return (
    <footer className="footer">
      <div className="container">
        <p>&copy; {year} SummaryFinance - Finansal Haberler için AI Özet Aracı</p>
      </div>
    </footer>
  );
}

export default Footer;

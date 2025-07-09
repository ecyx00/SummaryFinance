import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchSummaryById } from '../api/api';
import FeedbackButtons from '../components/FeedbackButtons';
import './SummaryDetail.css';

function SummaryDetail() {
  const { id } = useParams();
  const [story, setStory] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchStoryDetails() {
      try {
        setIsLoading(true);
        const response = await fetchSummaryById(id);
        setStory(response.data);
      } catch (err) {
        console.error('Özet detayları alınırken hata oluştu:', err);
        setError('Özet detayları yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.');
      } finally {
        setIsLoading(false);
      }
    }

    fetchStoryDetails();
  }, [id]);

  const formatDate = (dateString) => {
    const options = { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString('tr-TR', options);
  };

  if (isLoading) {
    return (
      <div className="detail-loading">
        <div className="loading-spinner"></div>
        <p>Özet detayları yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="detail-error">
        <h2>Bir hata oluştu</h2>
        <p>{error}</p>
        <Link to="/" className="back-link">Ana Sayfaya Dön</Link>
      </div>
    );
  }

  if (!story) {
    return (
      <div className="detail-not-found">
        <h2>Özet bulunamadı</h2>
        <p>Aradığınız özet raporu bulunamadı veya silinmiş olabilir.</p>
        <Link to="/" className="back-link">Ana Sayfaya Dön</Link>
      </div>
    );
  }

  return (
    <div className="summary-detail">
      <div className="detail-nav">
        <Link to="/" className="back-link">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="back-icon">
            <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
          </svg>
          Özet Listesine Dön
        </Link>
      </div>

      <article className="detail-content">
        <header className="detail-header">
          <div className="meta-info">
            <span className="detail-category">{story.category || 'Genel'}</span>
            <span className="detail-date">{formatDate(story.createdAt)}</span>
          </div>
          
          <h1 className="detail-title">{story.title}</h1>
          
          {story.sentiment && (
            <div className={`detail-sentiment sentiment-${story.sentiment.toLowerCase()}`}>
              <strong>Duygu Analizi:</strong> 
              {story.sentiment === 'POSITIVE' ? 'Olumlu' : 
               story.sentiment === 'NEGATIVE' ? 'Olumsuz' : 'Nötr'}
            </div>
          )}
        </header>
        
        <section className="detail-summary">
          <h2>Özet</h2>
          <p>{story.description}</p>
        </section>
        
        {story.content && (
          <section className="detail-analysis">
            <h2>Detaylı Analiz</h2>
            <div className="content-text">
              {story.content.split('\n').map((paragraph, idx) => (
                <p key={idx}>{paragraph}</p>
              ))}
            </div>
          </section>
        )}
        
        {story.entities && story.entities.length > 0 && (
          <section className="detail-entities">
            <h2>İlgili Kurumlar ve Kişiler</h2>
            <div className="entities-list">
              {story.entities.map((entity, index) => (
                <div key={index} className="entity-item">
                  <span className="entity-name">{entity.name}</span>
                  {entity.type && <span className="entity-type">{entity.type}</span>}
                </div>
              ))}
            </div>
          </section>
        )}
        
        {story.relatedNews && story.relatedNews.length > 0 && (
          <section className="detail-related">
            <h2>İlişkili Haberler</h2>
            <ul className="related-list">
              {story.relatedNews.map((news, index) => (
                <li key={index}>
                  <a href={news.url} target="_blank" rel="noopener noreferrer">
                    {news.title}
                  </a>
                </li>
              ))}
            </ul>
          </section>
        )}
        
        <FeedbackButtons storyId={parseInt(id)} />
      </article>
    </div>
  );
}

export default SummaryDetail;

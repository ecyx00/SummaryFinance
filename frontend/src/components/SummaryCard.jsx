import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';
import './SummaryCard.css';

function SummaryCard({ story }) {
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

  return (
    <div className="summary-card">
      <div className="card-header">
        <span className="summary-category">{story.category || 'Genel'}</span>
        <span className="summary-date">{formatDate(story.createdAt)}</span>
      </div>
      
      <h2 className="summary-title">{story.title}</h2>
      
      <p className="summary-description">{story.description}</p>
      
      <div className="summary-meta">
        {story.sentiment && (
          <span className={`sentiment-tag sentiment-${story.sentiment.toLowerCase()}`}>
            {story.sentiment === 'POSITIVE' ? 'Olumlu' : 
             story.sentiment === 'NEGATIVE' ? 'Olumsuz' : 'Nötr'}
          </span>
        )}
        
        {story.entities && story.entities.length > 0 && (
          <div className="entity-tags">
            {story.entities.slice(0, 3).map((entity, index) => (
              <span key={index} className="entity-tag">{entity.name}</span>
            ))}
            {story.entities.length > 3 && <span className="more-tag">+{story.entities.length - 3}</span>}
          </div>
        )}
      </div>
      
      <Link to={`/story/${story.id}`} className="read-more-btn">
        Detayları Görüntüle
      </Link>
    </div>
  );
}

SummaryCard.propTypes = {
  story: PropTypes.shape({
    id: PropTypes.number.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    createdAt: PropTypes.string.isRequired,
    category: PropTypes.string,
    sentiment: PropTypes.string,
    entities: PropTypes.arrayOf(
      PropTypes.shape({
        name: PropTypes.string.isRequired,
        type: PropTypes.string
      })
    )
  }).isRequired
};

export default SummaryCard;

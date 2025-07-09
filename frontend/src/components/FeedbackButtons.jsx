import { useState } from 'react';
import PropTypes from 'prop-types';
import { submitFeedback } from '../api/api';
import './FeedbackButtons.css';

function FeedbackButtons({ storyId }) {
  const [rating, setRating] = useState(null);
  const [isHelpful, setIsHelpful] = useState(null);
  const [comment, setComment] = useState('');
  const [showCommentBox, setShowCommentBox] = useState(false);
  const [isFeedbackSubmitted, setIsFeedbackSubmitted] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Yıldız değerlendirmesi için
  const handleRatingClick = (value) => {
    if (isFeedbackSubmitted) return;
    setRating(value);
    setIsHelpful(null); // Yıldız seçilirse helpful iptal edilsin
    setShowCommentBox(true);
  };

  // Yararlı/Yararsız için
  const handleHelpfulClick = (value) => {
    if (isFeedbackSubmitted) return;
    setIsHelpful(value);
    setRating(null); // Helpful seçilirse yıldızlar iptal edilsin
    setShowCommentBox(true);
  };

  // Yorum değişikliği
  const handleCommentChange = (e) => {
    setComment(e.target.value);
  };

  // Geri bildirim gönderme
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if ((rating === null && isHelpful === null) || loading) {
      return;
    }

    // Geri bildirim verisi hazırla
    const feedbackData = {
      storyId,
      rating, // Null olabilir
      isHelpful, // Null olabilir
      comment: comment.trim() || null
    };
    
    setLoading(true);
    setError(null);
    
    try {
      await submitFeedback(feedbackData);
      setIsFeedbackSubmitted(true);
      setShowCommentBox(false);
    } catch (err) {
      console.error('Geri bildirim gönderme hatası:', err);
      setError(
        err.response?.data?.message || 
        'Geri bildiriminiz gönderilemedi. Lütfen daha sonra tekrar deneyiniz.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (isFeedbackSubmitted) {
    return (
      <div className="feedback-submitted">
        <div className="feedback-success">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="success-icon">
            <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm13.36-1.814a.75.75 0 10-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 00-1.06 1.06l2.25 2.25a.75.75 0 001.14-.094l3.75-5.25z" clipRule="evenodd" />
          </svg>
          <p>Geri bildiriminiz için teşekkürler!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-container">
      <h3>Bu analiz raporunu nasıl buldunuz?</h3>
      
      <div className="feedback-options">
        <div className="rating-container">
          <p>Puanlayın:</p>
          <div className="star-rating">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                className={`star-button ${rating >= star ? 'active' : ''}`}
                onClick={() => handleRatingClick(star)}
                disabled={isFeedbackSubmitted}
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                  <path fillRule="evenodd" d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.006z" clipRule="evenodd" />
                </svg>
              </button>
            ))}
          </div>
        </div>
        
        <div className="helpful-container">
          <p>Veya değerlendirin:</p>
          <div className="helpful-buttons">
            <button
              type="button"
              className={`helpful-button ${isHelpful === true ? 'active' : ''}`}
              onClick={() => handleHelpfulClick(true)}
              disabled={isFeedbackSubmitted}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7.493 18.75c-.425 0-.82-.236-.975-.632A7.48 7.48 0 016 15.375c0-1.75.599-3.358 1.602-4.634.151-.192.373-.309.6-.397.473-.183.89-.514 1.212-.924a9.042 9.042 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75 2.25 2.25 0 012.25 2.25c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H14.23c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 00-1.423-.23h-.777zM2.331 10.977a11.969 11.969 0 00-.831 4.398 12 12 0 00.52 3.507c.26.85 1.084 1.368 1.973 1.368H4.9c.445 0 .72-.498.523-.898a8.963 8.963 0 01-.924-3.977c0-1.708.476-3.305 1.302-4.666.245-.403-.028-.959-.5-.959H4.25c-.832 0-1.612.453-1.918 1.227z" />
              </svg>
              Yararlı
            </button>
            <button
              type="button"
              className={`helpful-button ${isHelpful === false ? 'active' : ''}`}
              onClick={() => handleHelpfulClick(false)}
              disabled={isFeedbackSubmitted}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M15.73 5.25h1.035A7.465 7.465 0 0118 9.375a7.465 7.465 0 01-1.235 4.125h-.148c-.806 0-1.534.446-2.031 1.08a9.04 9.04 0 01-2.861 2.4c-.723.384-1.35.956-1.653 1.715a4.498 4.498 0 00-.322 1.672V21a.75.75 0 01-.75.75 2.25 2.25 0 01-2.25-2.25c0-1.152.26-2.243.723-3.218C7.74 15.724 7.366 15 6.748 15H3.622c-1.026 0-1.945-.694-2.054-1.715A12.134 12.134 0 011.5 12c0-2.848.992-5.464 2.649-7.521.388-.482.987-.729 1.605-.729H9.77a4.5 4.5 0 011.423.23l3.114 1.04a4.5 4.5 0 001.423.23zM21.669 13.773c.536-1.362.831-2.845.831-4.398 0-1.22-.182-2.398-.52-3.507-.26-.85-1.084-1.368-1.973-1.368H19.1c-.445 0-.72.498-.523.898.591 1.2.924 2.55.924 3.977a8.959 8.959 0 01-1.302 4.666c-.245.403.028.959.5.959h1.053c.832 0 1.612-.453 1.918-1.227z" />
              </svg>
              Yararsız
            </button>
          </div>
        </div>
      </div>
      
      {showCommentBox && (
        <form onSubmit={handleSubmit} className="feedback-form">
          <div className="form-group">
            <label htmlFor="comment">Düşüncelerinizi paylaşın (opsiyonel):</label>
            <textarea
              id="comment"
              value={comment}
              onChange={handleCommentChange}
              placeholder="Bu rapor hakkında düşüncelerinizi yazın..."
              rows="3"
              maxLength="500"
              disabled={isFeedbackSubmitted}
            ></textarea>
          </div>
          
          {error && <p className="error-message">{error}</p>}
          
          <button 
            type="submit" 
            className="submit-btn"
            disabled={loading || (rating === null && isHelpful === null)}
          >
            {loading ? 'Gönderiliyor...' : 'Gönder'}
          </button>
        </form>
      )}
    </div>
  );
}

FeedbackButtons.propTypes = {
  storyId: PropTypes.number.isRequired
};

export default FeedbackButtons;

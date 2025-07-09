import { useState, useEffect, useCallback } from 'react';
import { fetchSummaries } from '../api/api';
import useSse from '../hooks/useSse';
import SummaryCard from '../components/SummaryCard';
import './HomePage.css';

function HomePage() {
  const [summaries, setSummaries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Özetleri getiren fonksiyon
  const fetchAllSummaries = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetchSummaries();
      setSummaries(response.data);
      setError(null);
    } catch (err) {
      console.error('Özetler getirilirken hata oluştu:', err);
      setError('Özetler yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // SSE ile yeni güncellemeleri dinle
  const handleSseUpdate = useCallback((newData) => {
    console.log('Yeni SSE verisi alındı:', newData);
    
    // Yeni bir özet eklendi veya mevcut özet güncellendi
    if (newData.type === 'NEW_SUMMARY' || newData.type === 'UPDATE_SUMMARY') {
      // Tüm özet listesini yeniden getir (alternatif olarak sadece yeni/güncellenen özeti ekleyebilirsiniz)
      fetchAllSummaries();
    }
  }, [fetchAllSummaries]);
  
  // SSE hook'unu kullan
  const { error: sseError, isConnected } = useSse('/api/summary-updates', handleSseUpdate);

  // İlk yükleme
  useEffect(() => {
    fetchAllSummaries();
  }, [fetchAllSummaries]);

  return (
    <div className="home-page">
      <div className="page-header">
        <h1>Finansal Haber Özetleri</h1>
        <p>Yapay zeka ile özetlenmiş güncel finansal haberler ve stratejik değerlendirmeler</p>
        
        {isConnected && (
          <div className="live-indicator">
            <span className="live-dot"></span>
            Canlı Güncellemeler Aktif
          </div>
        )}
      </div>
      
      {sseError && (
        <div className="alert alert-warning">
          <p>Canlı güncellemeler şu anda aktif değil. Güncellemeler için sayfayı yenilemeniz gerekebilir.</p>
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          <p>{error}</p>
        </div>
      )}

      {isLoading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Özetler yükleniyor...</p>
        </div>
      ) : summaries.length > 0 ? (
        <div className="summaries-grid">
          {summaries.map(summary => (
            <SummaryCard key={summary.id} story={summary} />
          ))}
        </div>
      ) : (
        <div className="no-summaries">
          <p>Henüz özet bulunmuyor. Lütfen daha sonra tekrar kontrol edin.</p>
        </div>
      )}
    </div>
  );
}

export default HomePage;

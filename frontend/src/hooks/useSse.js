import { useEffect, useState } from 'react';

/**
 * SSE (Server-Sent Events) için özel bir hook.
 * 
 * @param {string} url - SSE endpoint URL'i
 * @param {function} onMessage - Yeni mesaj geldiğinde çalışacak callback fonksiyonu
 * @returns {object} - { data, error, isConnected } değerlerini içeren obje
 */
const useSse = (url, onMessage) => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // SSE'yi desteklemeyen tarayıcıları kontrol et
    if (!window.EventSource) {
      setError('Bu tarayıcı SSE (Server-Sent Events) özelliğini desteklemiyor.');
      return;
    }

    // EventSource örneği oluştur
    const eventSource = new EventSource(url);
    
    // Bağlantı açıldığında
    eventSource.onopen = () => {
      console.log('SSE bağlantısı kuruldu.');
      setIsConnected(true);
      setError(null);
    };
    
    // Mesaj alındığında
    eventSource.onmessage = (event) => {
      try {
        const newData = JSON.parse(event.data);
        setData(newData);
        
        // Callback fonksiyonu varsa çağır
        if (onMessage && typeof onMessage === 'function') {
          onMessage(newData);
        }
      } catch (err) {
        console.error('SSE veri işleme hatası:', err);
        setError('Alınan veri işlenirken bir hata oluştu.');
      }
    };
    
    // Hata durumunda
    eventSource.onerror = (err) => {
      console.error('SSE bağlantı hatası:', err);
      setIsConnected(false);
      setError('SSE bağlantısında bir hata oluştu. Yeniden bağlanmaya çalışılıyor...');
      
      // Bağlantı hatası durumunda yeniden bağlanma mantığı buraya eklenebilir
    };
    
    // Temizleme fonksiyonu
    return () => {
      console.log('SSE bağlantısı kapatılıyor...');
      eventSource.close();
      setIsConnected(false);
    };
  }, [url, onMessage]); // url veya callback değişirse hook yeniden çalışır

  return { data, error, isConnected };
};

export default useSse;

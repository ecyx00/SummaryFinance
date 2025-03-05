import requests
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ApiClient:
    """API istemcisi, dış API'lerle güvenli iletişim için kullanılır."""
    
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        """
        API istemcisini başlatır.
        
        Args:
            base_url: API'nin temel URL'si
            api_key: Kimlik doğrulama için API anahtarı
            timeout: İstek zaman aşımı (saniye)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Özelleştirilmiş HTTP oturum nesnesi oluşturur."""
        session = requests.Session()
        # Güvenlik başlıkları ekle
        session.headers.update({
            'User-Agent': 'SummaryFinance/1.0',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        return session
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        API yanıtını işler ve hataları yönetir.
        
        Args:
            response: HTTP yanıtı
            
        Returns:
            İşlenmiş yanıt verisi
            
        Raises:
            Exception: İstek başarısız olduğunda
        """
        try:
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"HTTP hata: {str(e)}")
            logger.error(f"Yanıt içeriği: {response.text}")
            raise Exception(f"API isteği başarısız oldu: {response.status_code} - {response.text}")
        except ValueError:
            logger.error(f"Geçersiz JSON yanıtı: {response.text}")
            raise Exception(f"Geçersiz API yanıtı: {response.text}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        GET isteği gönderir.
        
        Args:
            endpoint: API endpoint
            params: Sorgu parametreleri
            
        Returns:
            API yanıtı
        """
        url = f"{self.base_url}/{endpoint}"
        if params is None:
            params = {}
        
        # API anahtarını parametrelere ekle
        if self.api_key:
            params['api-key'] = self.api_key
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                timeout=self.timeout
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"İstek hatası: {str(e)}")
            raise Exception(f"API isteği gönderilirken hata oluştu: {str(e)}")
    
    def post(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        POST isteği gönderir.
        
        Args:
            endpoint: API endpoint
            data: İstek gövdesi
            params: Sorgu parametreleri
            
        Returns:
            API yanıtı
        """
        url = f"{self.base_url}/{endpoint}"
        if params is None:
            params = {}
        
        # API anahtarını parametrelere veya başlıklara ekle (API'ye bağlı olarak)
        if self.api_key:
            params['api-key'] = self.api_key
        
        try:
            response = self.session.post(
                url, 
                json=data, 
                params=params, 
                timeout=self.timeout
            )
            return self._handle_response(response)
        except requests.RequestException as e:
            logger.error(f"İstek hatası: {str(e)}")
            raise Exception(f"API isteği gönderilirken hata oluştu: {str(e)}")
    
    def close(self):
        """Oturumu kapatır ve kaynakları serbest bırakır."""
        self.session.close()
    
    def __enter__(self):
        """Context manager desteği için"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager'dan çıkıldığında session'ı kapat"""
        self.close() 
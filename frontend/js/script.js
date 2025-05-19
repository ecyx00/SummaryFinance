/**
 * SummaryFinance - Frontend Script
 * Bu script, Spring Boot backend'i ile SSE bağlantısı kurar ve 
 * yeni özet verileri geldiğinde ana sayfa içeriğini otomatik günceller.
 */

// Sayfa içeriği yüklendikten sonra çalışacak kodlar
document.addEventListener('DOMContentLoaded', function() {
    // Sayfa yüklendiginde özet listesini çek
    fetchSummaries();
    
    // SSE baglantısını başlat
    setupSseConnection();
    
    // Filtre butonları için event listener'lar ekle
    document.getElementById('applyFiltersButton').addEventListener('click', function() {
        applyFilters();
    });
    
    document.getElementById('clearFiltersButton').addEventListener('click', function() {
        document.getElementById('filterDate').value = '';
        document.getElementById('filterCategory').value = '';
        fetchSummaries(); // Filtreleri temizledikten sonra tüm özetleri göster
    });
});

/**
 * Server-Sent Events (SSE) bağlantısını kurar ve olay dinleyicilerini ekler
 */
let evtSource = null;
let reconnectAttempts = 0;
const maxReconnectDelay = 300000; // 5 dakika maksimum yeniden bağlanma süresi
const baseDelay = 15000; // 15 saniye başlangıç bekleme süresi

function setupSseConnection() {
    // Varolan bir bağlantı varsa kapat
    if (evtSource !== null) {
        evtSource.close();
    }
    
    console.log("SSE bağlantısı kuruluyor...");
    
    // SSE bağlantısını başlat
    evtSource = new EventSource('http://localhost:8888/api/summary-updates');
    
    // Bağlantı başarılı olduğunda
    evtSource.addEventListener('open', function() {
        console.log("SSE bağlantısı başarıyla kuruldu.");
        reconnectAttempts = 0; // Başarılı bağlantı kurulduğunda sıfırla
    });
    
    // Connect olayı (sunucudan ilk mesaj)
    evtSource.addEventListener('connect', function(e) {
        console.log("Sunucu bağlantısı sağlandı:", e.data);
    });
    
    // Yeni özet verileri geldiğinde - burada sayfa otomatik olarak yenilenecek
    evtSource.addEventListener('new_summaries_available', function(e) {
        console.log("Yeni özetler mevcut, sayfa güncelleniyor...");
        
        try {
            // Gelen veriyi parse et
            const data = JSON.parse(e.data);
            console.log("Güncelleme zamanı:", data.timestamp);
            
            // Özet listesini güncelle
            fetchSummaries();
            
            // Kullanıcıya bildirim göster
            showNotification("Yeni finans özetleri eklendi!", "Sayfa otomatik olarak güncellendi.");
        } catch (error) {
            console.error("SSE veri işleme hatası:", error);
        }
    });
    
    // Bağlantı hatası olduğunda
    evtSource.addEventListener('error', function(e) {
        console.error("SSE bağlantı hatası:", e);
        
        // Bağlantı kapandıysa
        if (evtSource.readyState === EventSource.CLOSED || evtSource.readyState === EventSource.CONNECTING) {
            handleReconnection();
        }
    });
    
    // Sayfa kapatıldığında bağlantıyı düzgün şekilde kapat
    window.addEventListener('beforeunload', function() {
        if (evtSource !== null) {
            evtSource.close();
            evtSource = null;
        }
    });
}

/**
 * SSE bağlantısı koptuğunda yeniden bağlanma stratejisini yönetir
 */
function handleReconnection() {
    reconnectAttempts++;
    
    // Üssel geri çekilme stratejisi - başlangıçta 15 saniye bekleyip, sonra katlanarak artar
    const delay = Math.min(baseDelay * Math.pow(1.5, reconnectAttempts), maxReconnectDelay);
    
    console.log(`SSE bağlantısı kesildi. ${Math.round(delay/1000)} saniye sonra yeniden bağlanma deneme ${reconnectAttempts}`);
    
    // Zaman aşımı süresi sonra yeniden bağlan
    setTimeout(function() {
        setupSseConnection();
    }, delay);
}

/**
 * Kullanıcıya ekranın üst kısmında geçici bir bildirim gösterir
 */
function showNotification(title, message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `<strong>${title}</strong> ${message}`;
    
    document.body.appendChild(notification);
    
    // 5 saniye sonra kaybolacak
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 5000);
}

/**
 * Backend'den en güncel özet verilerini alır ve sayfayı günceller
 */
function fetchSummaries() {
    const summaryListElement = document.getElementById('summaryList');
    
    // Yükleniyor göstergesi ekle
    if (summaryListElement) {
        summaryListElement.innerHTML = '<div class="loading">Özetler yükleniyor...</div>';
    }
    
    // API'den verileri çek - Tam URL kullanıyoruz
    fetch('http://localhost:8888/api/news/summaries')
        .then(response => {
            if (!response.ok) {
                throw new Error('API yanıt vermedi: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            updateSummaryList(data);
        })
        .catch(error => {
            console.error('Özet verileri çekilirken hata oluştu:', error);
            
            // Hata durumunda kullanıcıya bilgi ver
            if (summaryListElement) {
                summaryListElement.innerHTML = '<div class="error">Veriler yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.</div>';
            }
        });
}

/**
 * Özet listesini gelen verilerle günceller
 * @param {Array} summaries - Özet verileri dizisi
 */
function updateSummaryList(summaries) {
    const summaryListElement = document.getElementById('summaryList');
    
    if (!summaryListElement) {
        console.error('summaryList ID\'li element bulunamadı!');
        return;
    }
    
    // Liste içeriğini temizle
    summaryListElement.innerHTML = '';
    
    // Veri yoksa bilgi göster
    if (!summaries || summaries.length === 0) {
        summaryListElement.innerHTML = '<div class="no-data">Henüz analiz edilmiş özet bulunmuyor.</div>';
        return;
    }
    
    // Her özet için bir liste öğesi oluştur
    summaries.forEach(summary => {
        const summaryItem = document.createElement('div');
        summaryItem.className = 'summary-item';
        
        // Özet içeriğini oluştur
        let categoriesHtml = '';
        if (summary.assignedCategories && summary.assignedCategories.length > 0) {
            categoriesHtml = '<div class="categories">' + 
                summary.assignedCategories.map(category => 
                    `<span class="category-tag" onclick="filterByCategory('${category}')">${category}</span>`
                ).join('') + 
                '</div>';
        }
        
        // Tarih formatını düzenle
        const publicationDate = new Date(summary.publicationDate).toLocaleDateString('tr-TR', {
            year: 'numeric', 
            month: 'long', 
            day: 'numeric'
        });
        
        // Özet HTML içeriğini oluştur
        summaryItem.innerHTML = `
            <h2 class="summary-title">
                <a href="#" onclick="showSummaryDetail(${summary.id}); return false;">${summary.storyTitle}</a>
            </h2>
            <div class="summary-meta">
                <span class="publication-date">${publicationDate}</span>
                ${categoriesHtml}
            </div>
            <div class="summary-content">
                ${summary.storyContent}
            </div>
            
            ${summary.sourceUrls && summary.sourceUrls.length > 0 ? `
                <div class="source-references">
                    <h3>Kaynaklar:</h3>
                    <ul class="source-list">
                        ${summary.sourceUrls.map(url => `<li><a href="${url}" target="_blank">${url}</a></li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
        
        summaryListElement.appendChild(summaryItem);
    });
}

/**
 * Özet metninin önizlemesini oluşturur (ilk 200 karakter)
 * @param {string} text - Özet metni
 * @returns {string} - HTML formatında önizleme metni
 */
function getSummaryPreview(text) {
    if (!text) return '';
    
    // İlk 200 karakteri al ve ellipsis ekle
    const maxLength = 200;
    let preview = text.substring(0, maxLength);
    
    if (text.length > maxLength) {
        preview += '...';
    }
    
    return preview;
}

/**
 * Belirli bir kategoriye göre özet listesini filtreler
 * @param {string} category - Filtrelenecek kategori 
 */
function filterByCategory(category) {
    // URL'yi değiştirmek yerine, doğrudan API'ye filtreli istek yapalım
    document.getElementById('filterCategory').value = category;
    applyFilters();
}

/**
 * Özet detayını gösterir
 * @param {number} id - Özet ID'si
 */
function showSummaryDetail(id) {
    const summaryListElement = document.getElementById('summaryList');
    
    // Yükleniyor göstergesi ekle
    if (summaryListElement) {
        summaryListElement.innerHTML = '<div class="loading">Özet detayı yükleniyor...</div>';
    }
    
    // API'den özet detayını çek
    fetch(`http://localhost:8888/api/news/summary/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('API yanıt vermedi: ' + response.status);
            }
            return response.json();
        })
        .then(summary => {
            displaySummaryDetail(summary);
        })
        .catch(error => {
            console.error('Özet detayı çekilirken hata oluştu:', error);
            
            // Hata durumunda kullanıcıya bilgi ver ve geri dönüş linki ekle
            if (summaryListElement) {
                summaryListElement.innerHTML = `
                    <div class="error">Özet detayları yüklenirken bir hata oluştu.</div>
                    <button onclick="fetchSummaries()" class="back-button">Özet Listesine Dön</button>
                `;
            }
        });
}

/**
 * Özet detayını ekranda gösterir
 * @param {Object} summary - Özet verisi
 */
function displaySummaryDetail(summary) {
    const summaryListElement = document.getElementById('summaryList');
    
    if (!summaryListElement) return;
    
    // Tarih formatını düzenle
    const publicationDate = new Date(summary.publicationDate).toLocaleDateString('tr-TR', {
        year: 'numeric', 
        month: 'long', 
        day: 'numeric'
    });
    
    // Kategorileri hazırla
    let categoriesHtml = '';
    if (summary.assignedCategories && summary.assignedCategories.length > 0) {
        categoriesHtml = '<div class="categories">' + 
            summary.assignedCategories.map(category => 
                `<span class="category-tag" onclick="filterByCategory('${category}')">${category}</span>`
            ).join('') + 
            '</div>';
    }
    
    // Kaynaklar/Referanslar bölümü
    let sourcesHtml = '';
    if (summary.sourceUrls && summary.sourceUrls.length > 0) {
        sourcesHtml = `
            <div class="source-references">
                <h3>Kaynaklar:</h3>
                <ul class="source-list">
                    ${summary.sourceUrls.map(url => `<li><a href="${url}" target="_blank">${url}</a></li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Özet detay içeriğini hazırla
    summaryListElement.innerHTML = `
        <div class="summary-detail">
            <button onclick="fetchSummaries()" class="back-button">&#8592; Özet Listesine Dön</button>
            
            <h1>${summary.storyTitle}</h1>
            
            <div class="meta-info">
                <span class="publication-date">${publicationDate}</span>
                ${categoriesHtml}
            </div>
            
            <div class="summary-content">
                ${summary.summaryText.split('\n').map(para => `<p>${para}</p>`).join('')}
            </div>
            
            ${sourcesHtml}
        </div>
    `;
}

/**
 * Filtreleri uygular ve özet listesini günceller
 */
function applyFilters() {
    const dateFilter = document.getElementById('filterDate').value;
    const categoryFilter = document.getElementById('filterCategory').value;
    
    // Query parametreleri oluştur
    let queryParams = [];
    
    if (dateFilter) {
        queryParams.push(`date=${dateFilter}`);
    }
    
    if (categoryFilter) {
        queryParams.push(`category=${encodeURIComponent(categoryFilter)}`);
    }
    
    // API URL'yi oluştur
    let apiUrl = 'http://localhost:8888/api/news/summaries';
    if (queryParams.length > 0) {
        apiUrl += '?' + queryParams.join('&');
    }
    
    // Yükleniyor göstergesi ekle
    const summaryListElement = document.getElementById('summaryList');
    if (summaryListElement) {
        summaryListElement.innerHTML = '<div class="loading">Filtrelenmiş özetler yükleniyor...</div>';
    }
    
    // Filtrelenmiş verileri çek
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('API yanıt vermedi: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            updateSummaryList(data);
        })
        .catch(error => {
            console.error('Filtrelenmiş veriler çekilirken hata oluştu:', error);
            if (summaryListElement) {
                summaryListElement.innerHTML = '<div class="error">Veriler filtrelenirken bir hata oluştu.</div>';
            }
        });
}

/**
 * SummaryFinance - Frontend Script
 * Bu script, Spring Boot backend'i ile SSE bağlantısı kurar ve 
 * yeni özet verileri geldiğinde ana sayfa içeriğini otomatik günceller.
 * Özetler tarihe göre en yeniden eskiye doğru sıralanır.
 */

// API'nin temel URL'i - Production için
const API_BASE_URL = 'https://summaryfinance.me';

// Tüm özetleri tutan global değişken
let allSummaries = [];

// Sayfa içeriği yüklendikten sonra çalışacak kodlar
document.addEventListener('DOMContentLoaded', function() {
    fetchSummaries(); // Sayfa yüklendiğinde özet listesini çek ve sırala
    setupSseConnection(); // SSE bağlantısını başlat
    
    const applyFiltersButton = document.getElementById('applyFiltersButton');
    if (applyFiltersButton) {
        applyFiltersButton.addEventListener('click', applyFilters);
    }
    
    const clearFiltersButton = document.getElementById('clearFiltersButton');
    if (clearFiltersButton) {
        clearFiltersButton.addEventListener('click', function() {
            const filterDateInput = document.getElementById('filterDate');
            const filterCategorySelect = document.getElementById('filterCategory');
            if (filterDateInput) filterDateInput.value = '';
            if (filterCategorySelect) filterCategorySelect.value = '';
            
            // Filtreleri temizledikten sonra sıralanmış tüm özetleri göster
            updateSummaryList(allSummaries); 
        });
    }
});

/**
 * Server-Sent Events (SSE) bağlantısını kurar ve olay dinleyicilerini ekler
 */
let evtSource = null;
let reconnectAttempts = 0;
const maxReconnectDelay = 300000; // 5 dakika
const baseDelay = 15000; // 15 saniye

function setupSseConnection() {
    if (evtSource !== null && evtSource.readyState !== EventSource.CLOSED) {
        evtSource.close();
    }
    
    console.log("SSE bağlantısı kuruluyor...");
    evtSource = new EventSource(`${API_BASE_URL}/api/summary-updates`);
    
    evtSource.onopen = function() {
        console.log("SSE bağlantısı başarıyla kuruldu.");
        reconnectAttempts = 0;
    };
    
    evtSource.addEventListener('connect', function(e) {
        console.log("Sunucu bağlantısı sağlandı (connect event):", e.data);
    });
    
    evtSource.addEventListener('new_summaries_available', function(e) {
        console.log("Yeni özetler mevcut (new_summaries_available event), sayfa güncelleniyor...");
        try {
            const data = JSON.parse(e.data);
            console.log("Güncelleme bilgisi:", data);
            fetchSummaries(); 
            showNotification("Yeni Finans Analizleri", "Sayfa güncellendi, yeni özetler eklendi.");
        } catch (error) {
            console.error("SSE veri işleme hatası:", error);
        }
    });
    
    evtSource.onerror = function(e) {
        console.error("SSE bağlantı hatası:", e);
        if (evtSource.readyState === EventSource.CLOSED || evtSource.readyState === EventSource.CONNECTING) {
            console.log("SSE bağlantısı kapalı veya bağlanıyor, yeniden bağlanma deneniyor...");
            handleReconnection();
        }
    };
    
    window.addEventListener('beforeunload', function() {
        if (evtSource !== null) {
            evtSource.close();
            evtSource = null;
            console.log("Sayfa kapatılırken SSE bağlantısı kapatıldı.");
        }
    });
}

function handleReconnection() {
    if (evtSource !== null && evtSource.readyState !== EventSource.CLOSED) {
        evtSource.close(); 
    }
    reconnectAttempts++;
    const delay = Math.min(baseDelay * Math.pow(1.5, reconnectAttempts -1 ), maxReconnectDelay); 
    console.log(`SSE bağlantısı kesildi. ${Math.round(delay/1000)} saniye sonra yeniden bağlanma deneme ${reconnectAttempts}`);
    
    setTimeout(function() {
        console.log(`Yeniden bağlanma denemesi (${reconnectAttempts}) başlıyor...`);
        setupSseConnection();
    }, delay);
}

function showNotification(title, message) {
    const notificationArea = document.body; 
    const existingNotification = notificationArea.querySelector('.notification');
    if (existingNotification) { 
        existingNotification.remove();
    }

    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.innerHTML = `<strong>${title}</strong><p>${message}</p>`;
    
    notificationArea.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 600); 
    }, 5000);
}

function sortSummaries(summaries) {
    if (!summaries || !Array.isArray(summaries)) {
        console.warn("sortSummaries: Geçersiz veya boş özet dizisi alındı.");
        return [];
    }
    return [...summaries].sort((a, b) => { 
        try {
            // publicationDate null veya geçersizse en eski tarihi varsay
            const dateAValid = a.publicationDate && !isNaN(new Date(a.publicationDate).getTime());
            const dateBValid = b.publicationDate && !isNaN(new Date(b.publicationDate).getTime());

            const dateA = dateAValid ? new Date(a.publicationDate) : new Date(0); 
            const dateB = dateBValid ? new Date(b.publicationDate) : new Date(0);
            
            if (dateB.getTime() !== dateA.getTime()) {
                return dateB - dateA; 
            }

            // publicationDate aynı ise, generatedAt'e göre sırala (varsa ve geçerliyse)
            const generatedAValid = a.generatedAt && !isNaN(new Date(a.generatedAt).getTime());
            const generatedBValid = b.generatedAt && !isNaN(new Date(b.generatedAt).getTime());

            if (generatedAValid && generatedBValid) {
                const generatedA = new Date(a.generatedAt);
                const generatedB = new Date(b.generatedAt);
                return generatedB - generatedA; 
            } else if (generatedBValid) { // Sadece B'de generatedAt var, o zaman B daha yeni sayılır
                return 1;
            } else if (generatedAValid) { // Sadece A'da generatedAt var, o zaman A daha yeni sayılır
                return -1;
            }
            return 0;
        } catch (e) {
            console.error("Tarih sıralama hatası:", e, "Özet A:", a, "Özet B:", b);
            return 0; 
        }
    });
}

function fetchSummaries() {
    const summaryListElement = document.getElementById('summaryList');
    const filterBarElement = document.getElementById('filterBar');

    if (filterBarElement) {
        filterBarElement.style.display = 'flex';
    }
    
    if (summaryListElement) {
        summaryListElement.innerHTML = '<div class="loading-message">Özetler yükleniyor...</div>';
    }
    
    fetch(`${API_BASE_URL}/api/news/summaries`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`API yanıtı başarısız: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (!Array.isArray(data)) {
                console.error("API'den dizi beklenirken farklı formatta veri alındı:", data);
                allSummaries = []; 
            } else {
                allSummaries = sortSummaries(data); 
            }
            
            console.log('Tüm özetler yüklendi ve sıralandı. Toplam:', allSummaries.length);
            updateSummaryList(allSummaries); 
        })
        .catch(error => {
            console.error('Özet verileri çekilirken hata oluştu:', error);
            if (summaryListElement) {
                summaryListElement.innerHTML = `<div class="error-message">Veriler yüklenirken bir hata oluştu: ${error.message}. Lütfen sayfayı yenileyin veya daha sonra tekrar deneyin.</div>`;
            }
        });
}

function updateSummaryList(summariesToDisplay) {
    const summaryListElement = document.getElementById('summaryList');
    
    if (!summaryListElement) {
        console.error('summaryList ID\'li element bulunamadı!');
        return;
    }
    
    summaryListElement.innerHTML = ''; 
    
    if (!summariesToDisplay || !Array.isArray(summariesToDisplay) || summariesToDisplay.length === 0) {
        console.log('Görüntülenecek özet bulunmuyor veya geçersiz format.');
        summaryListElement.innerHTML = '<div class="no-data">Analiz edilmiş özet bulunmuyor.</div>';
        return;
    }
    
    summariesToDisplay.forEach(summary => {
        if (!summary || typeof summary.id === 'undefined' || !summary.storyTitle) {
            console.warn("Geçersiz özet verisi atlanıyor:", summary);
            return; 
        }

        const summaryItem = document.createElement('div');
        summaryItem.className = 'summary-item';
        
        let categoriesHtml = '';
        if (summary.assignedCategories && Array.isArray(summary.assignedCategories) && summary.assignedCategories.length > 0) {
            categoriesHtml = '<div class="categories">' + 
                summary.assignedCategories.map(category => {
                    const escapedCategory = category.replace(/'/g, "\\'"); // Tek tırnakları escape et
                    return `<span class="category-tag" onclick="filterByCategory('${escapedCategory}')">${category}</span>`;
                }).join('') + 
                '</div>';
        }
        
        const formattedPublicationDate = summary.publicationDate ? 
            new Date(summary.publicationDate).toLocaleDateString('tr-TR', {
                year: 'numeric', 
                month: 'long', 
                day: 'numeric'
            }) : 'Tarih bilgisi yok';
        
        summaryItem.innerHTML = `
            <h3 class="summary-title">
                <a href="#" onclick="showSummaryDetail(${summary.id}); return false;">${summary.storyTitle}</a>
            </h3>
            <div class="summary-meta">
                <span class="publication-date">${formattedPublicationDate}</span>
                ${categoriesHtml}
            </div>
            <p class="summary-preview">${getSummaryPreview(summary.summaryText)}</p>
            <a href="#" onclick="showSummaryDetail(${summary.id}); return false;" class="read-more">Devamını Oku →</a>
        `;
        
        summaryListElement.appendChild(summaryItem);
    });
}

function getSummaryPreview(text) {
    if (!text || typeof text !== 'string') return 'Özet mevcut değil.';
    const maxLength = 150; 
    let preview = text.substring(0, maxLength);
    if (text.length > maxLength) {
        preview += '...';
    }
    return preview;
}

function filterByCategory(category) {
    const filterCategorySelect = document.getElementById('filterCategory');
    if (filterCategorySelect) {
        filterCategorySelect.value = category; 
    }
    applyFilters(); 
}

function showSummaryDetail(id) {
    const summaryListElement = document.getElementById('summaryList');
    const filterBarElement = document.getElementById('filterBar');

    if (filterBarElement) {
      filterBarElement.style.display = 'none'; 
    }
    
    if (summaryListElement) {
        summaryListElement.innerHTML = '<div class="loading-message">Özet detayı yükleniyor...</div>';
    }
    
    fetch(`${API_BASE_URL}/api/news/summary/${id}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`API yanıtı başarısız: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(summary => {
            if (!summary || typeof summary.id === 'undefined') {
                throw new Error("Geçersiz özet detayı verisi alındı.");
            }
            displaySummaryDetail(summary);
        })
        .catch(error => {
            console.error('Özet detayı çekilirken hata oluştu:', error);
            if (summaryListElement) {
                summaryListElement.innerHTML = `
                    <div class="error-message">Özet detayları yüklenirken bir hata oluştu: ${error.message}.</div>
                    <button onclick="fetchSummaries()" class="filter-button secondary" style="margin-top:15px;">← Özet Listesine Dön</button>
                `;
            }
        });
}

function displaySummaryDetail(summary) {
    const summaryListElement = document.getElementById('summaryList');
    if (!summaryListElement) return;

    const formattedPublicationDate = summary.publicationDate ? 
        new Date(summary.publicationDate).toLocaleDateString('tr-TR', {
            year: 'numeric', 
            month: 'long', 
            day: 'numeric'
        }) : 'Tarih bilgisi yok';
    
    let categoriesHtml = '';
    if (summary.assignedCategories && Array.isArray(summary.assignedCategories) && summary.assignedCategories.length > 0) {
        categoriesHtml = '<div class="categories detail-categories">' + 
            summary.assignedCategories.map(category => {
                const escapedCategory = category.replace(/'/g, "\\'");
                // Detay sayfasındaki kategoriye tıklanınca listeye dönüp filtre uygulasın
                return `<span class="category-tag" onclick="fetchSummaries(); setTimeout(() => filterByCategory('${escapedCategory}'), 100);">${category}</span>`;
            }).join('') + 
            '</div>';
    }
    
    let sourcesHtml = '';
    if (summary.sourceUrls && Array.isArray(summary.sourceUrls) && summary.sourceUrls.length > 0) {
        sourcesHtml = `
            <div class="detail-section source-references">
                <h2>Kaynak Haberler:</h2>
                <ul class="source-list"> 
                    ${summary.sourceUrls.map(url => `<li><a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a></li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Kategori listesini metin olarak da hazırlayalım (title altına)
    const categoriesText = (summary.assignedCategories && Array.isArray(summary.assignedCategories) && summary.assignedCategories.length > 0) ?
        summary.assignedCategories.map(cat => {
            let properCat = cat.toLowerCase();
            return properCat.charAt(0).toUpperCase() + properCat.slice(1);
        }).join(', ') : 'Belirtilmemiş';

    summaryListElement.innerHTML = `
    <div class="summary-detail-container">
        <button onclick="fetchSummaries()" class="filter-button secondary" style="margin-bottom:20px;">← Tüm Özetlere Dön</button>
        <h1>${summary.storyTitle || 'Başlık Yok'}</h1>
        <div class="meta-info" style="margin-bottom: 15px;">
            <span class="publication-date">${formattedPublicationDate}</span>
            ${categoriesHtml}
        </div>
        <div class="detail-section analysis-text">
            <h2>Analiz:</h2>
            ${(summary.summaryText || 'Analiz metni bulunmuyor.').split('\n').filter(p => p.trim() !== '').map(para => `<p>${para}</p>`).join('')}
        </div>
        ${sourcesHtml}
        <button onclick="fetchSummaries()" class="filter-button secondary" style="margin-top:20px;">← Tüm Özetlere Dön</button>
    </div>
    `;
}

function applyFilters() {
    const dateFilterInput = document.getElementById('filterDate');
    const categoryFilterSelect = document.getElementById('filterCategory');
    
    const dateFilterValue = dateFilterInput ? dateFilterInput.value : '';
    const categoryFilterValue = categoryFilterSelect ? categoryFilterSelect.value : '';
    
    const summaryListElement = document.getElementById('summaryList');
    if (summaryListElement) {
        summaryListElement.innerHTML = '<div class="loading-message">Filtrelenmiş özetler yükleniyor...</div>';
    }
    
    let filteredSummaries = [...allSummaries]; 
    
    console.log('Filtreleme uygulanıyor. Başlangıç özet sayısı:', filteredSummaries.length);
    
    if (dateFilterValue) {
        try {
            // Tarih stringlerini (YYYY-AA-GG) doğrudan karşılaştır
            const filterDateString = dateFilterValue;
            console.log('Filtreleme tarihi string:', filterDateString);
            
            filteredSummaries = filteredSummaries.filter(summary => {
                if (!summary.publicationDate) return false;
                // Backend'den gelen tarih de YYYY-AA-GG formatında bir string ise
                const summaryDateString = summary.publicationDate.split('T')[0]; // Sadece tarih kısmını al
                return summaryDateString === filterDateString;
            });
            console.log('Tarih filtresinden sonra kalan özet sayısı:', filteredSummaries.length);
        } catch (e) {
            console.error("Tarih filtresi uygulanırken hata:", e);
        }
    }
    
    if (categoryFilterValue && categoryFilterValue !== "") { 
        filteredSummaries = filteredSummaries.filter(summary => {
            return summary.assignedCategories && 
                   Array.isArray(summary.assignedCategories) &&
                   summary.assignedCategories.map(c => c.toUpperCase()).includes(categoryFilterValue.toUpperCase()); 
        });
        console.log('Kategori filtresinden sonra kalan özet sayısı:', filteredSummaries.length);
    }
    
    updateSummaryList(filteredSummaries);
}

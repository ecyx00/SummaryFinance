package com.example.summaryfinance.repository;

import com.example.summaryfinance.entity.News;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.ZonedDateTime;
import java.util.List;
import java.util.Optional;
import java.util.Set;

@Repository
public interface NewsRepository extends JpaRepository<News, Long> { // <--- ID tipi Long olarak güncellendi

    // Belirli bir bölüme (API'den gelen ham section değeri) göre haberleri bulur
    List<News> findBySection(String section);

    // Belirli bir tarih aralığındaki haberleri bulur
    List<News> findByPublicationDateBetween(ZonedDateTime start, ZonedDateTime end);

    // Belirli bir kaynağa göre haberleri bulur
    List<News> findBySource(String source);

    // Belirli bir bölüm ve tarih aralığındaki haberleri bulur
    @Deprecated // section alanı entity'de artık yok, ileride kaldırılacak
    List<News> findBySectionAndPublicationDateBetween(String section, ZonedDateTime start, ZonedDateTime end);

    // Belirli bir URL'e sahip haberi bulur (tekilleştirme için)
    Optional<News> findByUrl(String url);

    /**
     * Verilen URL listesi içinde veritabanında zaten var olan URL'leri bulur.
     * Tekilleştirme işlemi için NewsService tarafından kullanılır.
     *
     * @param urls Kontrol edilecek URL'lerin seti.
     * @return Veritabanında zaten bulunan URL'lerin seti.
     */
    @Query("SELECT n.url FROM News n WHERE n.url IN :urls")
    Set<String> findExistingUrls(@Param("urls") Set<String> urls);

}
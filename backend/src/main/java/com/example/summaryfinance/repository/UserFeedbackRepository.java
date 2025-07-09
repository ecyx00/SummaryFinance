package com.example.summaryfinance.repository;

import com.example.summaryfinance.entity.UserFeedback;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserFeedbackRepository extends JpaRepository<UserFeedback, Long> {
    
    /**
     * Belirli bir hikaye için belirli bir IP adresinden gelen geri bildirimi arar
     * 
     * @param storyId Hikaye ID'si
     * @param ipAddress Kullanıcı IP adresi
     * @return Geri bildirim varsa Optional içinde döner, yoksa Optional.empty()
     */
    Optional<UserFeedback> findByStory_IdAndIpAddress(Long storyId, String ipAddress);
    
    /**
     * Belirli bir hikaye için tüm geri bildirimlerin sayısını döndürür
     * 
     * @param storyId Hikaye ID'si
     * @return Toplam geri bildirim sayısı
     */
    long countByStory_Id(Long storyId);
    
    /**
     * Belirli bir hikaye için ortalama puanı hesaplar (null olmayan puanlar için)
     * 
     * @param storyId Hikaye ID'si
     * @return Ortalama puan veya null (hiç puan yoksa)
     */
    @Query("SELECT AVG(u.rating) FROM UserFeedback u WHERE u.story.id = :storyId AND u.rating IS NOT NULL")
    Double findAverageRatingByStoryId(@Param("storyId") Long storyId);
}

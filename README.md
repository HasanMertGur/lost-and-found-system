# Lost and Found System - Veritabanı ve API Dokümantasyonu

Bu proje, kullanıcıların kayıp ve buluntu eşya bildiriminde bulunabildiği, ilanlar arasında arama yapabildiği ve eşya sahipleriyle bulucuların sistem üzerinden iletişim kurabildiği web tabanlı bir "Kayıp ve Buluntu Eşya Takip Sistemi" uygulamasıdır.

Bu dokümantasyon, projenin **Veritabanı Mimarisi (PostgreSQL)** ve **Backend Entegrasyonu (Python Flask REST API)** süreçlerini, veri yapılarını ve backend uç noktalarını (endpoints) içermektedir.

---

## Teknoloji

* **Backend:** Python Flask
* **Veritabanı:** PostgreSQL (Cloud/Bulut Altyapısı - Neon.tech)
* **Sürücü/Köprü Kütüphanesi:** `psycopg2-binary` (Python-PostgreSQL entegrasyonu için)
* **Güvenlik/Şifreleme:** `Werkzeug` (Şifrelerin güvenli şekilde hash'lenmesi için)

---

## Veritabanı Şeması ve İlişkileri

Veritabanı, verilerin tutarlılığını ve ilişkisel bütünlüğünü (Data Integrity) korumak adına yabancı anahtarlar (Foreign Keys) ve kısıtlamalar (Constraints) ile optimize edilmiştir. Projede kullanılan tablolar ve sütun yapıları aşağıda listelenmiştir:

### 1. `users` Tablosu
Kullanıcı hesap bilgilerini ve durumlarını saklar.
* `user_id` (SERIAL, PRIMARY KEY): Benzersiz kullanıcı kimliği.
* `full_name` (VARCHAR): Kullanıcının adı ve soyadı.
* `email` (VARCHAR, UNIQUE): Benzersiz e-posta adresi (Aynı e-posta ile ikinci kayıt engellenmiştir).
* `password_hash` (VARCHAR): Güvenlik amacıyla hash'lenmiş şifre.
* `phone_number` (VARCHAR, NULLABLE): Telefon numarası.
* `is_active` (BOOLEAN): Hesabın aktiflik durumu (Varsayılan: `TRUE`).
* `created_at` (TIMESTAMP): Hesabın oluşturulma tarihi.

### 2. `category` Tablosu
Eşyaların sınıflandırılması için önceden tanımlanmış kategorileri içerir.
* `category_id` (SERIAL, PRIMARY KEY): Benzersiz kategori kimliği.
* `name` (VARCHAR): Kategori adı (Örn: Elektronik, Cüzdan & Çanta, Anahtarlık).

### 3. `item` Tablosu
Bildirilen eşyaların teknik özelliklerini saklar.
* `item_id` (SERIAL, PRIMARY KEY): Benzersiz eşya kimliği.
* `name` (VARCHAR): Eşyanın adı veya kısa başlığı.
* `description` (TEXT): Eşyaya ait detaylı açıklama.
* `category_id` (INT, FOREIGN KEY): `category(category_id)` tablosuna bağlıdır.

### 4. `report` Tablosu
İlanların kayıp mı yoksa buluntu mu olduğunu, konum ve tarih bilgileriyle eşleştirir.
* `report_id` (SERIAL, PRIMARY KEY): Benzersiz rapor kimliği.
* `type` (VARCHAR): İlan türü (`lost` veya `found` değerlerini alır).
* `location` (VARCHAR): Olayın gerçekleştiği konum/yer.
* `date` (TIMESTAMP): İlanın oluşturulma tarihi.
* `status` (VARCHAR): İlanın durumu (Varsayılan: `active`).
* `user_id` (INT, FOREIGN KEY): İlanı açan kullanıcıyı belirtir, `users(user_id)` tablosuna bağlıdır.
* `item_id` (INT, UNIQUE, FOREIGN KEY): İlanı eşya ile bağlar, `item(item_id)` tablosuna bağlıdır (1:1 ilişki).

### 5. `message` Tablosu
Kullanıcılar arasındaki dahili mesajlaşma geçmişini tutar.
* `message_id` (SERIAL, PRIMARY KEY): Benzersiz mesaj kimliği.
* `content` (TEXT): Mesaj içeriği.
* `date` (TIMESTAMP): Mesajın gönderilme zamanı.
* `sender_id` (INT, FOREIGN KEY): Mesajı gönderen kullanıcı, `users(user_id)` tablosuna bağlıdır.
* `receiver_id` (INT, FOREIGN KEY): Mesajı alan kullanıcı, `users(user_id)` tablosuna bağlıdır.

### 6. `matches` Tablosu
Sistem veya kullanıcılar tarafından tespit edilen olası kayıp-buluntu eşleşmelerini saklar.
* `match_id` (SERIAL, PRIMARY KEY): Benzersiz eşleşme kimliği.
* `lost_report_id` (INT, FOREIGN KEY): İlgili kayıp ilanı, `report(report_id)` tablosuna bağlıdır.
* `found_report_id` (INT, FOREIGN KEY): İlgili buluntu ilanı, `report(report_id)` tablosuna bağlıdır.
* `is_confirmed` (BOOLEAN): Eşleşmenin taraflarca onaylanma durumu (Varsayılan: `FALSE`).

---

## API Endpoints Dokümantasyonu

Frontend ile iletişim tamamen JSON formatında gerçekleştirilmektedir. Aşağıda mevcut uç noktalar ve kabul ettikleri veri yapıları yer almaktadır:

### 1. Kullanıcı Kayıt Sistemi
* **URL:** `/register`
* **Metot:** `POST`
* **İstek Gövdesi (JSON):**
    ```json
    {
      "full_name": "Mert Gur",
      "email": "mert@test.com",
      "password": "securepassword123",
      "phone_number": "5551234567"
    }
    ```
* **Başarılı Yanıt (201 Created):**
    ```json
    {
      "durum": "Başarılı",
      "kullanici": {
        "created_at": "Thu, 21 May 2026 20:29:08 GMT",
        "email": "mert@test.com",
        "user_id": 1
      },
      "mesaj": "Kullanıcı başarıyla kaydedildi!"
    }
    ```

### 2. Kullanıcı Giriş Sistemi
* **URL:** `/login`
* **Metot:** `POST`
* **İstek Gövdesi (JSON):**
    ```json
    {
      "email": "mert@test.com",
      "password": "securepassword123"
    }
    ```
* **Başarılı Yanıt (200 OK):**
    ```json
    {
      "durum": "Başarılı",
      "kullanici_id": 1,
      "mesaj": "Hoş geldin, Mert Gur!"
    }
    ```

### 3. İlan Oluşturma (Kayıp veya Bulunan)
* **URL:** `/create-report`
* **Metot:** `POST`
* **İstek Gövdesi (JSON):**
    ```json
    {
      "user_id": 1,
      "category_id": 2,
      "item_name": "Siyah Deri Cuzdan",
      "description": "Icinde kimligim var, kütüphane önünde düşürüldü.",
      "type": "lost", 
      "location": "Merkez Kutuphane Onu"
    }
    ```
    *(Not: `type` alanı eşyasını arayanlar için `"lost"`, eşya bulanlar için `"found"` olarak gönderilmelidir.)*
* **Başarılı Yanıt (201 Created):**
    ```json
    {
      "durum": "Başarılı",
      "mesaj": "İlan başarıyla oluşturuldu!",
      "rapor_detaylari": {
        "report_id": 1,
        "status": "active"
      }
    }
    ```

### 4. İlanları Listeleme
* **URL:** `/reports`
* **Metot:** `GET`
* **Açıklama:** Sistemdeki tüm aktif ilanları ilişkili tablolarla (`item`, `category`, `users`) birleştirerek (JOIN) getirir.
* **Başarılı Yanıt (200 OK):**
    ```json
    {
      "durum": "Başarılı",
      "toplam_ilan": 1,
      "ilanlar": [
        {
          "category_name": "Cüzdan & Çanta",
          "date": "Thu, 21 May 2026 20:35:12 GMT",
          "description": "Icinde kimligim var, kütüphane önünde düşürüldü.",
          "item_name": "Siyah Deri Cuzdan",
          "location": "Merkez Kutuphane Onu",
          "report_id": 1,
          "reported_by": "Mert Gur",
          "status": "active",
          "type": "lost"
        }
      ]
    }
    ```

### 5. Mesaj Gönderme
* **URL:** `/send-message`
* **Metot:** `POST`
* **İstek Gövdesi (JSON):**
    ```json
    {
      "sender_id": 1,
      "receiver_id": 2,
      "content": "Merhaba, ilanınızdaki cüzdanı buldum."
    }
    ```
* **Başarılı Yanıt (201 Created):**
    ```json
    {
      "durum": "Başarılı",
      "mesaj": "Mesaj başarıyla iletildi!",
      "mesaj_detayi": {
        "date": "Thu, 21 May 2026 20:42:00 GMT",
        "message_id": 1
      }
    }
    ```

### 6. Kullanıcıya Ait Gelen Mesajları Çekme
* **URL:** `/messages/<int:user_id>`
* **Metot:** `GET`
* **Örnek:** `/messages/1` (ID'si 1 olan kullanıcıya gelen mesajlar)
* **Başarılı Yanıt (200 OK):**
    ```json
    {
      "durum": "Başarılı",
      "toplam_mesaj": 1,
      "mesajlar": [
        {
          "content": "Merhaba, ilanınızdaki cüzdanı buldum.",
          "date": "Thu, 21 May 2026 20:42:00 GMT",
          "message_id": 1,
          "sender_name": "Ahmet Yilmaz"
        }
      ]
    }
    ```

### 7. Eşleşme Kaydı Oluşturma
* **URL:** `/create-match`
* **Metot:** `POST`
* **İstek Gövdesi (JSON):**
    ```json
    {
      "lost_report_id": 1,
      "found_report_id": 2
    }
    ```
* **Başarılı Yanıt (201 Created):**
    ```json
    {
      "durum": "Başarılı",
      "eslesme_detayi": {
        "is_confirmed": false,
        "match_id": 1
      },
      "mesaj": "Eşleşme başarıyla kaydedildi! Karşı tarafın onayı bekleniyor."
    }
    ```

---

## Kurulum ve Yerel Çalıştırma Esasları

Backend servisinin yerelde çalıştırılması ve bulut veritabanına bağlanması için aşağıdaki adımların izlenmesi gerekmektedir:

1.  **Gerekli Bağımlılıkların Kurulması:**
    ```bash
    pip install Flask psycopg2-binary
    ```
2.  **Veritabanı Yapılandırması:**
    `app.py` dosyası içerisindeki `DB_URL` değişkenine Neon.tech üzerinden temin edilen PostgreSQL bağlantı dizesi (Connection String) eklenmelidir.
3.  **Uygulamanın Başlatılması:**
    ```bash
    python app.py
    ```
    Uygulama yerelde varsayılan olarak `http://127.0.0.1:5000` adresi üzerinde dinlemeye başlayacaktır.
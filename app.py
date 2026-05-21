from flask import Flask, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash # Şifreleri gizlemek için eklendi

app = Flask(__name__)

# BÖLÜM A: BULUT VERİTABANI BAĞLANTI BİLGİSİ
# Neon.tech'ten aldığın o uzun bağlantı adresini buraya yapıştır kanka.
DB_URL = "postgresql://neondb_owner:npg_TAWSX45LkoFz@ep-round-mud-abh152jo.eu-west-2.aws.neon.tech/neondb?sslmode=require"

# BÖLÜM B: VERİTABANINA BAĞLANMA FONKSİYONU
def get_db_connection():
    """
    Bu fonksiyon, her veritabanı işlemi yapmak istediğimizde buluta gidip
    kapıyı çalacak ve bağlantıyı açacak olan yardımcı fonksiyondur.

    """
    try:
        # psycopg2 kütüphanesi kullanarak internetteki veritabanımıza bağlanıyoruz
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"Veritabanına bağlanırken hata oluştu: {e}")
        return None

# BÖLÜM C: İLK DENEME ROUTE'U (BAĞLANTI TESTİ)
@app.route('/test-db', methods=['GET'])
def test_db():
    """
    Tarayıcıdan 'http://127.0.0.1:5000/test-db' adresine gidildiğinde çalışır.
    Veritabanının çalışıp çalışmadığını test eder.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı köprüsü kurulamadı!"}), 500
    
    # Cursor (İmleç): SQL sorgularını veritabanı içinde çalıştıran elimiz kolumuzdur.
    # RealDictCursor kullanıyoruz çünkü veritabanından gelen sonuçları bize Python sözlüğü (JSON) olarak süslü getirir.
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Basit bir test sorgusu: Veritabanı versiyonunu öğrenelim
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone() # Gelen tek satırlık sonucu alıyoruz
        
        # İşimiz bittiğinde kapıları kapatıyoruz (Güvenlik ve performans için şart!)
        cursor.close()
        conn.close()
        
        return jsonify({
            "durum": "Başarılı",
            "mesaj": "Bulut veritabanına başarıyla bağlandık!",
            "veritabanı_versiyonu": db_version
        }), 200
        
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": str(e)}), 500

# BÖLÜM D: KULLANICI KAYIT SİSTEMİ (REGISTER)
@app.route('/register', methods=['POST'])
def register_user():
    """
    Frontend'den gelen JSON verisini alıp veritabanındaki 'users' tablosuna kaydeder.
    """
    # 1. Frontend'den gelen veriyi (JSON) yakala
    data = request.get_json()
    
    # 2. Verilerin içinden gerekli alanları çek
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    phone_number = data.get('phone_number', '') # Telefon zorunlu değilse boş kalabilir
    
    # 3. Zorunlu alanlar boş mu diye kontrol et
    if not full_name or not email or not password:
        return jsonify({"durum": "Hata", "mesaj": "Ad, E-posta ve Şifre zorunludur!"}), 400
        
    # 4. Şifreyi şifrele (Hashleme)
    hashed_password = generate_password_hash(password)
    
    # 5. Veritabanına bağlan
    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı bağlantısı koptu!"}), 500
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 6. SQL İNSERT SORGUSU YAZIYORUZ
        # %s işaretleri dışarıdan gelecek verileri temsil eder. (Güvenlik için SQL Injection'ı önler)
        # RETURNING user_id: Kayıt başarılı olursa, otomatik oluşturulan yeni ID'yi bize geri ver demektir.
        insert_query = """
            INSERT INTO users (full_name, email, password_hash, phone_number)
            VALUES (%s, %s, %s, %s) 
            RETURNING user_id, email, created_at;
        """
        
        # Sorguyu ve verileri çalıştır
        cursor.execute(insert_query, (full_name, email, hashed_password, phone_number))
        
        # Yeni eklenen kullanıcının bilgilerini al
        new_user = cursor.fetchone()
        
        # 7. DEĞİŞİKLİĞİ VERİTABANINA KALICI OLARAK KAYDET (Çok Önemli!)
        conn.commit()
        
        # Kapıları kapat
        cursor.close()
        conn.close()
        
        return jsonify({
            "durum": "Başarılı",
            "mesaj": "Kullanıcı başarıyla kaydedildi!",
            "kullanici": new_user
        }), 201 # 201: 'Yeni bir şey oluşturuldu' anlamına gelen HTTP kodudur.
        
    except psycopg2.errors.UniqueViolation:
        # Eğer birisi veritabanında zaten var olan (UNIQUE) bir e-posta ile kayıt olmaya çalışırsa:
        conn.rollback() # İşlemi iptal et
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": "Bu e-posta adresi sistemde zaten kayıtlı!"}), 400
        
    except Exception as e:
        # Başka bilinmeyen bir hata çıkarsa
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": str(e)}), 500


# Uygulamayı başlatma kısmı
if __name__ == '__main__':
    app.run(debug=True)
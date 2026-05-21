from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


DB_URL = "postgresql://neondb_owner:npg_TAWSX45LkoFz@ep-round-mud-abh152jo.eu-west-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    """
    Bu fonksiyon, her veritabanı işlemi yapmak istediğimizde buluta gidip
    kapıyı çalacak ve bağlantıyı açacak olan yardımcı fonksiyondur.

    """
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"Veritabanına bağlanırken hata oluştu: {e}")
        return None

@app.route('/test-db', methods=['GET'])
def test_db():
    """
    Tarayıcıdan 'http://127.0.0.1:5000/test-db' adresine gidildiğinde çalışır.
    Veritabanının çalışıp çalışmadığını test eder.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı köprüsü kurulamadı!"}), 500
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
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

@app.route('/register', methods=['POST'])
def register_user():
    """
    Frontend'den gelen JSON verisini alıp veritabanındaki 'users' tablosuna kaydeder.
    """
    data = request.get_json()

    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')
    phone_number = data.get('phone_number', '')
    
    if not full_name or not email or not password:
        return jsonify({"durum": "Hata", "mesaj": "Ad, E-posta ve Şifre zorunludur!"}), 400
        
    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı bağlantısı koptu!"}), 500
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        insert_query = """
            INSERT INTO users (full_name, email, password_hash, phone_number)
            VALUES (%s, %s, %s, %s) 
            RETURNING user_id, email, created_at;
        """
        
        cursor.execute(insert_query, (full_name, email, hashed_password, phone_number))
        
        new_user = cursor.fetchone()
        
        conn.commit()

        cursor.close()
        conn.close()
        
        return jsonify({
            "durum": "Başarılı",
            "mesaj": "Kullanıcı başarıyla kaydedildi!",
            "kullanici": new_user
        }), 201
        
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": "Bu e-posta adresi sistemde zaten kayıtlı!"}), 400
        
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": str(e)}), 500


@app.route('/login', methods=['POST'])
def login_user():
    """
    Frontend'den gelen e-posta ve şifreyi kontrol edip sisteme giriş yaptırır.
    """
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"durum": "Hata", "mesaj": "E-posta ve şifre zorunludur!"}), 400
        
    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı bağlantısı koptu!"}), 500
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:

        cursor.execute("SELECT user_id, full_name, password_hash, is_active FROM users WHERE email = %s;", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user is None:
            return jsonify({"durum": "Hata", "mesaj": "Bu e-posta ile kayıtlı bir kullanıcı bulunamadı."}), 401
            
        if not user['is_active']:
            return jsonify({"durum": "Hata", "mesaj": "Bu hesap dondurulmuş veya kapatılmış."}), 403
            
        if check_password_hash(user['password_hash'], password):
            return jsonify({
                "durum": "Başarılı",
                "mesaj": f"Hoş geldin, {user['full_name']}!",
                "kullanici_id": user['user_id']
            }), 200
        else:
            return jsonify({"durum": "Hata", "mesaj": "Hatalı şifre girdiniz."}), 401
            
    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": str(e)}), 500

@app.route('/create-report', methods=['POST'])
def create_report():
    """
    Kullanıcıdan gelen eşya ve rapor bilgilerini alır.
    Önce 'item' tablosuna, sonra 'report' tablosuna yazar.
    """
    data = request.get_json()
    
    user_id = data.get('user_id')           
    category_id = data.get('category_id')   
    item_name = data.get('item_name')       
    description = data.get('description')  
    report_type = data.get('type')          
    location = data.get('location')         
    
    if not all([user_id, category_id, item_name, report_type, location]):
        return jsonify({"durum": "Hata", "mesaj": "Eksik bilgi girdiniz. Lütfen zorunlu alanları doldurun."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı bağlantısı koptu!"}), 500
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        insert_item_query = """
            INSERT INTO item (name, description, category_id)
            VALUES (%s, %s, %s)
            RETURNING item_id;
        """
        cursor.execute(insert_item_query, (item_name, description, category_id))
        new_item = cursor.fetchone()
        created_item_id = new_item['item_id']
        insert_report_query = """
            INSERT INTO report (type, location, date, user_id, item_id)
            VALUES (%s, %s, NOW(), %s, %s)
            RETURNING report_id, status;
        """
        cursor.execute(insert_report_query, (report_type, location, user_id, created_item_id))
        new_report = cursor.fetchone()

        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "durum": "Başarılı",
            "mesaj": "İlan başarıyla oluşturuldu!",
            "rapor_detaylari": new_report
        }), 201

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": f"Rapor oluşturulurken hata meydana geldi: {str(e)}"}), 500

@app.route('/reports', methods=['GET'])
def get_reports():
    """
    Veritabanındaki tüm aktif ilanları (kayıp ve bulunan) 
    eşya bilgileri ve oluşturan kişinin adıyla birlikte getirir.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı bağlantısı koptu!"}), 500
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        get_reports_query = """
            SELECT 
                r.report_id, r.type, r.location, r.date, r.status,
                i.name AS item_name, i.description,
                c.name AS category_name,
                u.full_name AS reported_by
            FROM report r
            JOIN item i ON r.item_id = i.item_id
            JOIN category c ON i.category_id = c.category_id
            JOIN users u ON r.user_id = u.user_id
            WHERE r.status = 'active'
            ORDER BY r.date DESC; -- En yeni ilanlar en üstte görünsün
        """
        
        cursor.execute(get_reports_query)
        reports = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "durum": "Başarılı",
            "toplam_ilan": len(reports),
            "ilanlar": reports
        }), 200

    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": str(e)}), 500

@app.route('/send-message', methods=['POST'])
def send_message():
    """
    Bir kullanıcının diğerine sistem üzerinden mesaj atmasını sağlar.
    'message' tablosuna kayıt yapar.
    """
    data = request.get_json()
    
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not all([sender_id, receiver_id, content]):
        return jsonify({"durum": "Hata", "mesaj": "Gönderen, alıcı ve mesaj içeriği zorunludur!"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı bağlantısı koptu!"}), 500
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        insert_msg_query = """
            INSERT INTO message (sender_id, receiver_id, content)
            VALUES (%s, %s, %s)
            RETURNING message_id, date;
        """
        cursor.execute(insert_msg_query, (sender_id, receiver_id, content))
        new_message = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "durum": "Başarılı",
            "mesaj": "Mesaj başarıyla iletildi!",
            "mesaj_detayi": new_message
        }), 201

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": f"Mesaj gönderilemedi: {str(e)}"}), 500

@app.route('/messages/<int:user_id>', methods=['GET'])
def get_messages(user_id):
    """
    Belirli bir kullanıcıya gelen tüm mesajları listeler.
    Gönderenin adını da users tablosundan çekerek ekler.
    """
    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı bağlantısı koptu!"}), 500
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        get_msgs_query = """
            SELECT 
                m.message_id, m.content, m.date,
                u.full_name AS sender_name
            FROM message m
            JOIN users u ON m.sender_id = u.user_id
            WHERE m.receiver_id = %s
            ORDER BY m.date DESC;
        """
        
        cursor.execute(get_msgs_query, (user_id,))
        messages = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "durum": "Başarılı",
            "toplam_mesaj": len(messages),
            "mesajlar": messages
        }), 200

    except Exception as e:
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": str(e)}), 500


@app.route('/create-match', methods=['POST'])
def create_match():
    """
    Bir kayıp ilanı ile bir bulunan ilanını eşleştirir.
    Onay durumu varsayılan olarak FALSE (Beklemede) başlar.
    """
    data = request.get_json()
    
    lost_report_id = data.get('lost_report_id')
    found_report_id = data.get('found_report_id')
    
    if not lost_report_id or not found_report_id:
        return jsonify({"durum": "Hata", "mesaj": "Kayıp ve Bulunan rapor ID'leri zorunludur!"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"durum": "Hata", "mesaj": "Veritabanı bağlantısı koptu!"}), 500
        
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        insert_match_query = """
            INSERT INTO matches (lost_report_id, found_report_id, is_confirmed)
            VALUES (%s, %s, FALSE)
            RETURNING match_id, is_confirmed;
        """
        cursor.execute(insert_match_query, (lost_report_id, found_report_id))
        new_match = cursor.fetchone()
        
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "durum": "Başarılı",
            "mesaj": "Eşleşme başarıyla kaydedildi! Karşı tarafın onayı bekleniyor.",
            "eslesme_detayi": new_match
        }), 201

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"durum": "Hata", "mesaj": f"Eşleşme oluşturulamadı: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
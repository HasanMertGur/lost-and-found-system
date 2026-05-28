import os
from flask import Flask, jsonify, request, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(
    __name__,
    template_folder="templates", # HTML dosyalarının aranacağı klasör
    static_folder="static"       # CSS/JS dosyalarının aranacağı klasör
)

# ── BULUT VERİTABANI BAĞLANTI BİLGİSİ ──────────────────────────────────
DB_URL = "postgresql://neondb_owner:BURAYA_KENDİ_ŞİFREN_GELECEK@ep-cool-water-a2b3c4.eu-central-1.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        return None

# ── SAYFA YÖNLENDİRMELERİ (PAGE ROUTES) ──────────────────────────────────
# Arkadaşının frontend şablonlarını (HTML) ekrana getiren kısım

@app.route('/')
def home(): 
    return render_template("index.html")

@app.route('/auth')
def auth_page(): 
    return render_template("auth.html")

@app.route('/reports')
def reports_page(): 
    return render_template("reports.html")

@app.route('/create')
def create_page(): 
    return render_template("create.html")

@app.route('/messages')
def messages_page(): 
    return render_template("messages.html")


# ── API UÇ NOKTALARI (API ROUTES) ────────────────────────────────────────

# 1. Kullanıcı Kayıt (Şifre Hash'leme Korunuyor)
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    full_name = data.get('full_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password')
    phone_number = data.get('phone_number')
    
    if not full_name or not email or not password:
        return jsonify({"message": "Ad, e-posta ve şifre alanları zorunludur."}), 400
        
    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute(
            """INSERT INTO users (full_name, email, password_hash, phone_number) 
               VALUES (%s, %s, %s, %s) RETURNING user_id;""",
            (full_name, email, hashed_password, phone_number)
        )
        uid = cursor.fetchone()['user_id']
        conn.commit()
        return jsonify({"message": "Kayit basarili.", "kullanici_id": uid}), 201
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"message": "Bu e-posta zaten kayitli."}), 409
    finally:
        cursor.close()
        conn.close()

# 2. Kullanıcı Giriş (Güvenli Şifre Kontrolü Çarpıştırması)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password')
    
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT user_id, full_name, email, password_hash FROM users WHERE email = %s;", (email,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        return jsonify({
            "kullanici_id": user['user_id'],
            "full_name": user['full_name'],
            "email": user['email']
        }), 200
    else:
        return jsonify({"message": "Gecersiz e-posta veya sifre."}), 401

# 3. Kategorileri Listeleme Yardımcısı (Arkadaşının eklediği yeni API)
@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT category_id AS id, name FROM category ORDER BY category_id;")
    categories = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(categories), 200

# 4. Dinamik Arama ve Filtreleme Destekli İlan Listeleme
@app.route('/api/reports', methods=['GET'])
def get_reports():
    # URL parametrelerini yakalama (Örn: /api/reports?type=lost&q=cüzdan)
    report_type = request.args.get('type')
    search_query = request.args.get('q')
    
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # ER Diyagramındaki 1:1 Item-Report ilişkisini koruyarak JOIN yapıyoruz
    sql = """
        SELECT r.report_id AS id, i.name AS item_name, i.description, r.type, r.location, r.status,
               r.date AS created_at, i.category_id, c.name AS category_name,
               r.user_id, u.full_name AS reported_by
        FROM report r
        JOIN item i ON r.item_id = i.item_id
        JOIN category c ON i.category_id = c.category_id
        JOIN users u ON r.user_id = u.user_id
        WHERE r.status = 'active'
    """
    params = []
    
    # Arkadaşının eklediği dinamik filtreleme mantığı:
    if report_type in ("lost", "found"):
        sql += " AND r.type = %s"
        params.append(report_type)
        
    if search_query:
        sql += " AND (i.name ILIKE %s OR i.description ILIKE %s OR r.location ILIKE %s)"
        search_param = f"%{search_query}%"
        params += [search_param, search_param, search_param]
        
    sql += " ORDER BY r.date DESC;"
    
    cursor.execute(sql, params)
    reports = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(reports), 200

# 5. İlan Oluşturma (Güvenli Çift Tablo İşlemi / Transaction Korunuyor)
@app.route('/api/reports', methods=['POST'])
def create_report():
    data = request.get_json()
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    item_name = data.get('item_name', '').strip()
    description = data.get('description')
    report_type = data.get('type')
    location = data.get('location')
    
    if report_type not in ("lost", "found"):
        return jsonify({"message": "type 'lost' veya 'found' olmali."}), 400
        
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Kullanıcı kontrolü
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
        if not cursor.fetchone():
            return jsonify({"message": "Kullanici bulunamadi."}), 404
            
        # 1. Adım: Item tablosuna ekleme
        cursor.execute(
            "INSERT INTO item (name, description, category_id) VALUES (%s, %s, %s) RETURNING item_id;",
            (item_name, description, category_id)
        )
        item_id = cursor.fetchone()['item_id']
        
        # 2. Adım: Report tablosuna ekleme
        cursor.execute(
            "INSERT INTO report (type, location, date, user_id, item_id) VALUES (%s, %s, NOW(), %s, %s) RETURNING report_id;",
            (report_type, location, user_id, item_id)
        )
        rid = cursor.fetchone()['report_id']
        
        conn.commit()
        return jsonify({"message": "Ilan olusturuldu.", "report_id": rid}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Hata oluştu: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

# 6. Mesaj Gönderme
@app.route('/api/messages', methods=['POST'])
def send_message():
    data = request.get_json()
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Gönderici ve alıcı kontrolü
        for uid, label in [(sender_id, "sender_id"), (receiver_id, "receiver_id")]:
            cursor.execute("SELECT user_id FROM users WHERE user_id = %s;", (uid,))
            if not cursor.fetchone():
                return jsonify({"message": f"{label}={uid} bulunamadi."}), 404
                
        cursor.execute(
            "INSERT INTO message (sender_id, receiver_id, content) VALUES (%s, %s, %s) RETURNING message_id;",
            (sender_id, receiver_id, content)
        )
        mid = cursor.fetchone()['message_id']
        conn.commit()
        return jsonify({"message": "Mesaj gonderildi.", "message_id": mid}), 201
    finally:
        cursor.close()
        conn.close()

# 7. Gelen Kutusu (Inbox) ve Giden Kutusu (Sent) Filtrelemeli Mesaj Çekme
@app.route('/api/messages/<int:user_id>', methods=['GET'])
def get_messages(user_id):
    box = request.args.get('box', 'inbox') # Varsayılan olarak gelen kutusu
    
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Kullanici bulunamadi."}), 404
        
    if box == "sent":
        # Giden kutusu sorgusu
        sql = """
            SELECT m.message_id AS id, m.content, m.date AS created_at,
                   m.receiver_id, u.full_name AS receiver_name, m.sender_id
            FROM message m
            LEFT JOIN users u ON u.user_id = m.receiver_id
            WHERE m.sender_id = %s
            ORDER BY m.date DESC;
        """
    else:
        # Gelen kutusu sorgusu
        sql = """
            SELECT m.message_id AS id, m.content, m.date AS created_at,
                   m.sender_id, u.full_name AS sender_name, m.receiver_id
            FROM message m
            LEFT JOIN users u ON u.user_id = m.sender_id
            WHERE m.receiver_id = %s
            ORDER BY m.date DESC;
        """
        
    cursor.execute(sql, (user_id,))
    messages = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(messages), 200

# 8. Eşleşme Kaydı Oluşturma
@app.route('/api/matches', methods=['POST'])
def create_match():
    data = request.get_json()
    lost_report_id = data.get('lost_report_id')
    found_report_id = data.get('found_report_id')
    
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT report_id, type FROM report WHERE report_id = %s;", (lost_report_id,))
        lost = cursor.fetchone()
        
        cursor.execute("SELECT report_id, type FROM report WHERE report_id = %s;", (found_report_id,))
        found = cursor.fetchone()
        
        if not lost: return jsonify({"message": f"lost_report_id={lost_report_id} bulunamadi."}), 404
        if not found: return jsonify({"message": f"found_report_id={found_report_id} bulunamadi."}), 404
        
        if lost["type"] != "lost": return jsonify({"message": "lost_report_id 'lost' turunde degil."}), 400
        if found["type"] != "found": return jsonify({"message": "found_report_id 'found' turunde degil."}), 400
        
        cursor.execute(
            "INSERT INTO matches (lost_report_id, found_report_id, is_confirmed) VALUES (%s, %s, FALSE) RETURNING match_id;",
            (lost_report_id, found_report_id)
        )
        mid = cursor.fetchone()['match_id']
        conn.commit()
        return jsonify({"message": "Eslasme olusturuldu.", "match_id": mid}), 201
    finally:
        cursor.close()
        conn.close()

# 9. Spesifik İlan Detaylarını Çekme (ItemDetail sayfası için)
@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Sadece istenen ID'ye sahip ilanı getir
    sql = """
        SELECT r.report_id AS id, i.name AS item_name, i.description, r.type, r.location, r.status,
               r.date AS created_at, i.category_id, c.name AS category_name,
               r.user_id, u.full_name AS reported_by
        FROM report r
        JOIN item i ON r.item_id = i.item_id
        JOIN category c ON i.category_id = c.category_id
        JOIN users u ON r.user_id = u.user_id
        WHERE r.report_id = %s
    """
    cursor.execute(sql, (report_id,))
    report = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if report:
        return jsonify(report), 200
    else:
        return jsonify({"message": "İlan bulunamadı."}), 404


if __name__ == '__main__':
    app.run(debug=True)
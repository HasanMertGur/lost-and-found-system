import os
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_gizli_anahtar"


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/reports')
def reports_page():
    return render_template('reports.html')

@app.route('/create')
def create_page():
    return render_template('create.html')

@app.route('/messages')
def messages_page():
    return render_template('messages.html')

@app.route('/matches')
def matches_page():
    return render_template('matches.html')


CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


DB_URL = "postgresql://neondb_owner:npg_TAWSX45LkoFz@ep-round-mud-abh152jo.eu-west-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        return None




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


@app.route('/api/reports', methods=['GET'])
def get_reports():
    report_type = request.args.get('type')
    search_query = request.args.get('q')
    
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
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

@app.route('/api/reports', methods=['POST'])
def create_report():
    data = request.get_json()
    print("⚡ [FLASK] React'tan bir POST isteği geldi! Alınan Veri:", data) # Terminalde görmek için ekledik
    
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    item_name = data.get('item_name', '').strip()
    description = data.get('description')
    report_type = data.get('type')
    location = data.get('location')
    
    if report_type not in ("lost", "found"):
        print("[FLASK] Hata: İlan türü 'lost' ya da 'found' değil!")
        return jsonify({"message": "type 'lost' veya 'found' olmali."}), 400
        
    conn = get_db_connection()
    if conn is None: 
        print("[FLASK] Hata: Veritabanı bağlantısı kurulamadı!")
        return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
        if not cursor.fetchone():
            print(f"[FLASK] Hata: user_id {user_id} veritabanında yok!")
            return jsonify({"message": "Kullanici bulunamadi."}), 404
            
        cursor.execute(
            "INSERT INTO item (name, description, category_id) VALUES (%s, %s, %s) RETURNING item_id;",
            (item_name, description, category_id)
        )
        item_id = cursor.fetchone()['item_id']
        
        cursor.execute(
            "INSERT INTO report (type, location, date, user_id, item_id) VALUES (%s, %s, NOW(), %s, %s) RETURNING report_id;",
            (report_type, location, user_id, item_id)
        )
        rid = cursor.fetchone()['report_id']
        
        conn.commit()
        print(f"[FLASK] İlan başarıyla DB'ye yazıldı! Rapor ID: {rid}")
        return jsonify({"message": "Ilan olusturuldu.", "report_id": rid}), 201
    except Exception as e:
        conn.rollback()
        print("[FLASK] SQL Hatası oluştu:", str(e))
        return jsonify({"message": f"Hata oluştu: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

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


@app.route('/api/messages/<int:user_id>', methods=['GET'])
def get_messages(user_id):
    box = request.args.get('box', 'inbox')
    
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"message": "Kullanici bulunamadi."}), 404
        
    if box == "sent":
        sql = """
            SELECT m.message_id AS id, m.content, m.date AS created_at,
                   m.receiver_id, u.full_name AS receiver_name, m.sender_id
            FROM message m
            LEFT JOIN users u ON u.user_id = m.receiver_id
            WHERE m.sender_id = %s
            ORDER BY m.date DESC;
        """
    else:
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


@app.route('/api/matches', methods=['POST'])
def create_match():
    data = request.get_json()
    lost_report_id = data.get('lost_report_id')
    found_report_id = data.get('found_report_id')
    

    if not lost_report_id and not found_report_id:
        return jsonify({"message": "Eşleşme oluşturabilmek için en least bir ilan ID'si gereklidir."}), 400
        
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:

        if lost_report_id:
            cursor.execute("SELECT report_id, type FROM report WHERE report_id = %s;", (lost_report_id,))
            lost = cursor.fetchone()
            if not lost: return jsonify({"message": f"lost_report_id={lost_report_id} bulunamadi."}), 404
            if lost["type"] != "lost": return jsonify({"message": "lost_report_id 'lost' turunde degil."}), 400
            

        if found_report_id:
            cursor.execute("SELECT report_id, type FROM report WHERE report_id = %s;", (found_report_id,))
            found = cursor.fetchone()
            if not found: return jsonify({"message": f"found_report_id={found_report_id} bulunamadi."}), 404
            if found["type"] != "found": return jsonify({"message": "found_report_id 'found' turunde degil."}), 400
            

        cursor.execute(
            """INSERT INTO matches (lost_report_id, found_report_id, is_confirmed) 
               VALUES (%s, %s, FALSE) RETURNING match_id;""",
            (lost_report_id, found_report_id)
        )
        mid = cursor.fetchone()['match_id']
        conn.commit()
        return jsonify({"message": "Eslasme olusturuldu.", "match_id": mid}), 201
    finally:
        cursor.close()
        conn.close()


@app.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report_detail(report_id):
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
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


@app.route('/api/matches/<int:user_id>', methods=['GET'])
def get_user_matches(user_id):
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    

    sql = """
        SELECT 
            m.match_id, 
            m.is_confirmed,
            -- Kayıp ilanı bilgileri
            m.lost_report_id,
            i_lost.name AS lost_item_name,
            u_lost.full_name AS lost_user_name,
            u_lost.user_id AS lost_user_id,
            -- Bulunan ilan bilgileri
            m.found_report_id,
            i_found.name AS found_item_name,
            u_found.full_name AS found_user_name,
            u_found.user_id AS found_user_id
        FROM matches m
        LEFT JOIN report r_lost ON m.lost_report_id = r_lost.report_id
        LEFT JOIN item i_lost ON r_lost.item_id = i_lost.item_id
        LEFT JOIN users u_lost ON r_lost.user_id = u_lost.user_id
        
        LEFT JOIN report r_found ON m.found_report_id = r_found.report_id
        LEFT JOIN item i_found ON r_found.item_id = i_found.item_id
        LEFT JOIN users u_found ON r_found.user_id = u_found.user_id
        
        WHERE r_lost.user_id = %s OR r_found.user_id = %s
        ORDER BY m.match_id DESC;
    """
    
    try:
        cursor.execute(sql, (user_id, user_id))
        matches = cursor.fetchall()
        return jsonify(matches), 200
    except Exception as e:
        return jsonify({"message": f"Hata oluştu: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/api/matches/<int:match_id>/confirm', methods=['POST'])
def confirm_match(match_id):
    conn = get_db_connection()
    if conn is None: return jsonify({"message": "Veritabanı bağlantı hatası."}), 500
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:

        cursor.execute(
            "UPDATE matches SET is_confirmed = TRUE WHERE match_id = %s RETURNING match_id, lost_report_id, found_report_id;",
            (match_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            return jsonify({"message": "Eşleşme kaydı bulunamadı."}), 404
            
       
        if row['lost_report_id']:
            cursor.execute("UPDATE report SET status = 'resolved' WHERE report_id = %s;", (row['lost_report_id'],))
        if row['found_report_id']:
            cursor.execute("UPDATE report SET status = 'resolved' WHERE report_id = %s;", (row['found_report_id'],))
            
        conn.commit()
        return jsonify({"message": "Eşleşme başarıyla onaylandı ve ilanlar kapatıldı.", "match_id": match_id}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"message": f"Hata oluştu: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':

    app.run(debug=True, port=5000)
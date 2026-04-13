from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sqlite3

# Создаём приложение Flask
app = Flask(__name__)
CORS(app)

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect('/tmp/parking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            event_type TEXT,
            latitude REAL,
            longitude REAL,
            timestamp INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_spots (
            spot_id TEXT PRIMARY KEY,
            is_occupied INTEGER,
            last_updated INTEGER,
            latitude REAL,
            longitude REAL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("База данных инициализирована")

# === ПРИЁМ СОБЫТИЙ С ТЕЛЕФОНА ===
@app.route('/api/event', methods=['POST'])
def receive_event():
    data = request.json
    
    user_id = data.get('user_id', 'unknown')
    event_type = data.get('type')
    latitude = data.get('lat')
    longitude = data.get('lng')
    timestamp = data.get('timestamp', datetime.now().timestamp())
    
    conn = sqlite3.connect('/tmp/parking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO events (user_id, event_type, latitude, longitude, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, event_type, latitude, longitude, timestamp))
    
    conn.commit()
    conn.close()
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {event_type} от {user_id}")
    
    return jsonify({'status': 'ok', 'message': 'Событие сохранено'})

# === ПОЛУЧИТЬ ВСЕ ПАРКОВОЧНЫЕ МЕСТА ===
@app.route('/api/all_spots', methods=['GET'])
def all_spots():
    conn = sqlite3.connect('/tmp/parking.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT spot_id, is_occupied, last_updated, latitude, longitude FROM parking_spots')
    
    spots = []
    for row in cursor.fetchall():
        spots.append({
            'spot_id': row[0],
            'is_occupied': bool(row[1]),
            'last_updated': row[2],
            'latitude': row[3],
            'longitude': row[4]
        })
    
    conn.close()
    
    return jsonify({'status': 'ok', 'spots': spots})

# === СТАТУС КОНКРЕТНОЙ ПАРКОВКИ ===
@app.route('/api/status', methods=['GET'])
def get_status():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    
    if not lat or not lng:
        return jsonify({'error': 'lat and lng required'}), 400
    
    conn = sqlite3.connect('/tmp/parking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT spot_id, is_occupied, last_updated, latitude, longitude
        FROM parking_spots
        ORDER BY ((latitude - ?) * (latitude - ?) + (longitude - ?) * (longitude - ?)) ASC
        LIMIT 5
    ''', (lat, lat, lng, lng))
    
    spots = []
    for row in cursor.fetchall():
        spots.append({
            'spot_id': row[0],
            'is_occupied': bool(row[1]),
            'last_updated': row[2],
            'latitude': row[3],
            'longitude': row[4]
        })
    
    conn.close()
    
    return jsonify({'status': 'ok', 'spots': spots})

# === ГЛАВНАЯ СТРАНИЦА ===
@app.route('/')
def home():
    return '''
    <h1>PocketParker Server</h1>
    <p>Сервер работает!</p>
    <p>Доступные endpoints:</p>
    <ul>
        <li><b>POST /api/event</b> - отправить событие</li>
        <li><b>GET /api/all_spots</b> - все парковочные места</li>
        <li><b>GET /api/status?lat=X&lng=Y</b> - статус рядом с координатами</li>
    </ul>
    '''

# Инициализация БД при запуске
init_db()
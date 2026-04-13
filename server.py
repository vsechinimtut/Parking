from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('parking.db')
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

@app.route('/api/event', methods=['POST'])
def receive_event():
    data = request.json
    user_id = data.get('user_id', 'unknown')
    event_type = data.get('type')
    latitude = data.get('lat')
    longitude = data.get('lng')
    timestamp = data.get('timestamp', datetime.now().timestamp())
    
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO events (user_id, event_type, latitude, longitude, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, event_type, latitude, longitude, timestamp))
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'ok'})

@app.route('/api/status', methods=['GET'])
def get_status():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT spot_id, is_occupied, last_updated, latitude, longitude
        FROM parking_spots
    ''')
    spots = [{'spot_id': row[0], 'is_occupied': bool(row[1]), 
              'last_updated': row[2], 'latitude': row[3], 'longitude': row[4]}
             for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'status': 'ok', 'spots': spots})

@app.route('/api/all_spots', methods=['GET'])
def all_spots():
    conn = sqlite3.connect('parking.db')
    cursor = conn.cursor()
    cursor.execute('SELECT spot_id, is_occupied, last_updated, latitude, longitude FROM parking_spots')
    spots = [{'spot_id': row[0], 'is_occupied': bool(row[1]), 
              'last_updated': row[2], 'latitude': row[3], 'longitude': row[4]}
             for row in cursor.fetchall()]
    conn.close()
    return jsonify({'status': 'ok', 'spots': spots})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, request, render_template, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')

# Database path
def get_db_path():
    return 'events.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(get_db_path())
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            description TEXT NOT NULL,
            color TEXT DEFAULT '#4361ee',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_event():
    try:
        date = request.form['event_date']
        desc = request.form['description']
        color = request.form.get('color', '#4361ee')
        
        if not date or not desc:
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (event_date, description, color) VALUES (?, ?, ?)", 
            (date, desc, color)
        )
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Sự kiện đã lưu cho ngày {date}!',
            'event_id': event_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view', methods=['GET'])
def view_event():
    date = request.args.get('event_date')
    
    if not date:
        return "Vui lòng chọn ngày", 400
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.execute(
        "SELECT id, description, color, created_at FROM events WHERE event_date = ? ORDER BY created_at DESC", 
        (date,)
    )
    events = cursor.fetchall()
    conn.close()
    
    if not events:
        return f"""
        <div class="empty-state">
            <i class="far fa-calendar-times"></i>
            <p>Không có sự kiện nào vào ngày {date}</p>
        </div>
        """
    
    html = f"<h4 class='mb-3'>Sự kiện ngày {date} ({len(events)} sự kiện)</h4>"
    html += "<div class='events-list'>"
    
    for e in events:
        event_id, description, color, created_at = e
        created_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
        
        html += f"""
        <div class="event-item" style="border-left-color: {color or '#4361ee'}">
            <div class="event-date">{created_time}</div>
            <div class="event-description">{description}</div>
            <div class="event-actions">
                <button class="event-action-btn view-event" data-id="{event_id}">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="event-action-btn delete delete-event" data-id="{event_id}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        """
    
    html += "</div>"
    return html

@app.route('/api/events', methods=['GET'])
def get_all_events():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.execute(
        "SELECT event_date, description, color FROM events ORDER BY event_date"
    )
    events = cursor.fetchall()
    conn.close()
    
    events_dict = {}
    for event_date, description, color in events:
        if event_date not in events_dict:
            events_dict[event_date] = []
        events_dict[event_date].append({
            'description': description,
            'color': color
        })
    
    return jsonify(events_dict)

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event_by_id(event_id):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.execute(
        "SELECT id, event_date, description, color, created_at FROM events WHERE id = ?", 
        (event_id,)
    )
    event = cursor.fetchone()
    conn.close()
    
    if not event:
        return jsonify({'error': 'Không tìm thấy sự kiện'}), 404
    
    return jsonify({
        'id': event[0],
        'event_date': event[1],
        'description': event[2],
        'color': event[3],
        'created_at': event[4]
    })

@app.route('/api/events/upcoming', methods=['GET'])
def get_upcoming_events():
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    conn = sqlite3.connect(get_db_path())
    cursor = conn.execute(
        "SELECT id, event_date, description, color FROM events WHERE event_date BETWEEN ? AND ? ORDER BY event_date",
        (today.isoformat(), next_week.isoformat())
    )
    events = cursor.fetchall()
    conn.close()
    
    events_list = []
    for event_id, event_date, description, color in events:
        events_list.append({
            'id': event_id,
            'event_date': event_date,
            'description': description,
            'color': color
        })
    
    return jsonify(events_list)

@app.route('/delete/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT event_date FROM events WHERE id = ?", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            return jsonify({'error': 'Không tìm thấy sự kiện'}), 404
        
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Đã xóa sự kiện thành công'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    try:
        data = request.get_json()
        date = data.get('event_date')
        desc = data.get('description')
        color = data.get('color', '#4361ee')
        
        if not date or not desc:
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM events WHERE id = ?", (event_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Không tìm thấy sự kiện'}), 404
        
        cursor.execute(
            "UPDATE events SET event_date = ?, description = ?, color = ? WHERE id = ?",
            (date, desc, color, event_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Đã cập nhật sự kiện thành công'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

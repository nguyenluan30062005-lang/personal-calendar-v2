from flask import Flask, request, render_template, jsonify, send_from_directory
import sqlite3
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__, 
            static_folder='static',
            static_url_path='/static')

# Database
DATABASE = 'events.db'

def init_db():
    """Khởi tạo database với đầy đủ field"""
    conn = sqlite3.connect(DATABASE)
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
    """Trang chủ"""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Phục vụ file tĩnh"""
    return send_from_directory('static', filename)

@app.route('/add', methods=['POST'])
def add_event():
    """Thêm sự kiện (AJAX support)"""
    try:
        date = request.form['event_date']
        desc = request.form['description']
        color = request.form.get('color', '#4361ee')
        
        if not date or not desc:
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (event_date, description, color) VALUES (?, ?, ?)", 
            (date, desc, color)
        )
        conn.commit()
        event_id = cursor.lastrowid
        conn.close()
        
        # Trả về JSON cho AJAX
        return jsonify({
            'success': True,
            'message': f'Sự kiện đã lưu cho ngày {date}!',
            'event_id': event_id,
            'event': {
                'id': event_id,
                'date': date,
                'description': desc,
                'color': color
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/view', methods=['GET'])
def view_event():
    """Xem sự kiện theo ngày (AJAX)"""
    try:
        date = request.args.get('event_date')
        
        if not date:
            return jsonify({'error': 'Vui lòng chọn ngày'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.execute(
            """SELECT id, description, color, created_at 
               FROM events WHERE event_date = ? 
               ORDER BY created_at DESC""", 
            (date,)
        )
        events = cursor.fetchall()
        conn.close()
        
        # Format events
        formatted_events = []
        for e in events:
            event_id, description, color, created_at = e
            try:
                time_str = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%H:%M')
            except:
                time_str = created_at
            
            formatted_events.append({
                'id': event_id,
                'description': description,
                'color': color or '#4361ee',
                'time': time_str,
                'created_at': created_at
            })
        
        return jsonify({
            'success': True,
            'date': date,
            'events': formatted_events,
            'count': len(formatted_events)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['GET'])
def get_all_events():
    """API lấy tất cả sự kiện (cho lịch)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.execute(
            "SELECT event_date, description, color FROM events ORDER BY event_date"
        )
        events = cursor.fetchall()
        conn.close()
        
        # Group by date
        events_dict = {}
        for event_date, description, color in events:
            if event_date not in events_dict:
                events_dict[event_date] = []
            events_dict[event_date].append({
                'description': description,
                'color': color or '#4361ee'
            })
        
        return jsonify(events_dict)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event_by_id(event_id):
    """API lấy chi tiết sự kiện"""
    try:
        conn = sqlite3.connect(DATABASE)
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
            'color': event[3] or '#4361ee',
            'created_at': event[4]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/upcoming', methods=['GET'])
def get_upcoming_events():
    """API lấy sự kiện 7 ngày tới"""
    try:
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.execute(
            """SELECT id, event_date, description, color 
               FROM events WHERE event_date BETWEEN ? AND ? 
               ORDER BY event_date""",
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
                'color': color or '#4361ee'
            })
        
        return jsonify(events_list)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """API xóa sự kiện"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get event date before deleting
        cursor.execute("SELECT event_date FROM events WHERE id = ?", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            return jsonify({'error': 'Không tìm thấy sự kiện'}), 404
        
        # Delete event
        cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Đã xóa sự kiện thành công',
            'event_date': event[0]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """API cập nhật sự kiện"""
    try:
        data = request.get_json()
        date = data.get('event_date')
        desc = data.get('description')
        color = data.get('color', '#4361ee')
        
        if not date or not desc:
            return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if event exists
        cursor.execute("SELECT id FROM events WHERE id = ?", (event_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Không tìm thấy sự kiện'}), 404
        
        # Update event
        cursor.execute(
            "UPDATE events SET event_date = ?, description = ?, color = ? WHERE id = ?",
            (date, desc, color, event_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Đã cập nhật sự kiện thành công'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """API thống kê"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Total events
        cursor.execute("SELECT COUNT(*) FROM events")
        total = cursor.fetchone()[0]
        
        # Today's events
        today = datetime.now().date().isoformat()
        cursor.execute("SELECT COUNT(*) FROM events WHERE event_date = ?", (today,))
        today_count = cursor.fetchone()[0]
        
        # Busiest day
        cursor.execute("""
            SELECT event_date, COUNT(*) as count 
            FROM events 
            GROUP BY event_date 
            ORDER BY count DESC 
            LIMIT 1
        """)
        busiest = cursor.fetchone()
        
        # Recent events
        cursor.execute("""
            SELECT event_date, description 
            FROM events 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'total_events': total,
            'today_events': today_count,
            'busiest_day': {
                'date': busiest[0] if busiest else None,
                'count': busiest[1] if busiest else 0
            },
            'recent_events': [
                {'date': r[0], 'description': r[1]} for r in recent
            ]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check cho Azure"""
    return jsonify({
        'status': 'healthy',
        'service': 'personal-calendar',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/events/month/<int:year>/<int:month>', methods=['GET'])
def get_events_by_month(year, month):
    """API lấy sự kiện theo tháng"""
    try:
        # Calculate date range
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.execute(
            """SELECT event_date, COUNT(*) as count 
               FROM events 
               WHERE event_date >= ? AND event_date < ? 
               GROUP BY event_date""",
            (start_date, end_date)
        )
        events = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary
        events_dict = {}
        for event_date, count in events:
            events_dict[event_date] = count
        
        return jsonify(events_dict)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

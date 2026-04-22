"""
Flask web service for accessing Kantech events database
    Provides REST API endpoints to retrieve data from PostgreSQL
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from database import DatabaseManager
from config import POLL_INTERVAL
from datetime import datetime

app = Flask(__name__)
CORS(app)

db = DatabaseManager()


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    connection_info = db.get_connection_info()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database_connected': db.is_connected(),
        'database': connection_info
    }), 200


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        user_count = db.fetch_one('SELECT COUNT(*) AS count FROM tblUser')['count']
        dydaktyk_count = db.fetch_one('SELECT COUNT(*) AS count FROM tblDydaktyk')['count']
        active_dydaktyk_count = db.fetch_one(
            'SELECT COUNT(*) AS count FROM tblDydaktyk WHERE is_active = 1'
        )['count']

        return jsonify({
            'total_user_accesses': user_count,
            'total_dydaktyk_sessions': dydaktyk_count,
            'active_dydaktyk_sessions': active_dydaktyk_count,
            'database': db.get_connection_info(),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['GET'])
def get_users():
    """Get latest user access events
    Query params:
    - limit: number of records to return (default: 10, max: 100)
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 100)  # Cap at 100
        
        users = db.get_latest_user_access(limit)
        
        return jsonify({
            'records': users,
            'count': len(users),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<username>', methods=['GET'])
def get_user_by_username(username):
    """Get specific user's access records"""
    try:
        records = db.fetch_all('''
                SELECT * FROM tblUser
                WHERE username = %s
                ORDER BY updated_at DESC
                LIMIT 50
            ''', (username,))
        
        return jsonify({
            'username': username,
            'records': records,
            'count': len(records),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dydaktyks', methods=['GET'])
def get_dydaktyks():
    """Get latest dydaktyk sessions
    Query params:
    - limit: number of records to return (default: 10, max: 100)
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 100)  # Cap at 100
        
        dydaktyks = db.get_latest_dydaktyk(limit)
        
        return jsonify({
            'records': dydaktyks,
            'count': len(dydaktyks),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dydaktyks/active', methods=['GET'])
def get_active_dydaktyk():
    """Get currently active dydaktyk session"""
    try:
        active = db.get_active_dydaktyk()
        
        return jsonify({
            'active_session': active,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dydaktyks/<username>', methods=['GET'])
def get_dydaktyk_by_username(username):
    """Get specific dydaktyk's sessions"""
    try:
        records = db.fetch_all('''
                SELECT * FROM tblDydaktyk
                WHERE username = %s
                ORDER BY opened_at DESC
                LIMIT 50
            ''', (username,))
        
        return jsonify({
            'username': username,
            'records': records,
            'count': len(records),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/database', methods=['GET'])
def download_database():
    """PostgreSQL does not expose a single DB file for download"""
    connection_info = db.get_connection_info()
    return jsonify({
        'error': 'Direct database file export is not supported for PostgreSQL',
        'hint': (
            f"Use pg_dump, e.g.: pg_dump -h {connection_info['host']} -p {connection_info['port']} "
            f"-U {connection_info['user']} -d {connection_info['database']} > backup.sql"
        )
    }), 410


@app.route('/api/export/users.json', methods=['GET'])
def export_users_json():
    """Export all user records as JSON"""
    try:
        records = db.fetch_all('SELECT * FROM tblUser ORDER BY updated_at DESC')
        
        return jsonify({
            'data': records,
            'count': len(records),
            'exported_at': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/dydaktyks.json', methods=['GET'])
def export_dydaktyks_json():
    """Export all dydaktyk records as JSON"""
    try:
        records = db.fetch_all('SELECT * FROM tblDydaktyk ORDER BY opened_at DESC')
        
        return jsonify({
            'data': records,
            'count': len(records),
            'exported_at': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/users', methods=['POST'])
def search_users():
    """Search users by username or card_hex
    JSON body:
    {
        "username": "optional_username",
        "card_hex": "optional_card_hex",
        "limit": 50
    }
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        card_hex = data.get('card_hex', '').strip()
        limit = data.get('limit', 50)
        limit = min(limit, 200)

        if username and card_hex:
            records = db.fetch_all('''
                    SELECT * FROM tblUser
                    WHERE username ILIKE %s AND card_hex ILIKE %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                ''', (f'%{username}%', f'%{card_hex}%', limit))
        elif username:
            records = db.fetch_all('''
                    SELECT * FROM tblUser
                    WHERE username ILIKE %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                ''', (f'%{username}%', limit))
        elif card_hex:
            records = db.fetch_all('''
                    SELECT * FROM tblUser
                    WHERE card_hex ILIKE %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                ''', (f'%{card_hex}%', limit))
        else:
            return jsonify({'error': 'Provide username or card_hex'}), 400
        
        return jsonify({
            'results': records,
            'count': len(records),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    docs = {
        'service': 'Kantech Events WebService',
        'version': '1.0',
        'endpoints': [
            {
                'path': '/api/health',
                'method': 'GET',
                'description': 'Health check'
            },
            {
                'path': '/api/stats',
                'method': 'GET',
                'description': 'Get database statistics'
            },
            {
                'path': '/api/users',
                'method': 'GET',
                'description': 'Get latest user accesses',
                'params': 'limit (default: 10, max: 100)'
            },
            {
                'path': '/api/users/<username>',
                'method': 'GET',
                'description': 'Get specific user records'
            },
            {
                'path': '/api/dydaktyks',
                'method': 'GET',
                'description': 'Get latest dydaktyk sessions',
                'params': 'limit (default: 10, max: 100)'
            },
            {
                'path': '/api/dydaktyks/active',
                'method': 'GET',
                'description': 'Get active dydaktyk session'
            },
            {
                'path': '/api/dydaktyks/<username>',
                'method': 'GET',
                'description': 'Get specific dydaktyk records'
            },
            {
                'path': '/api/export/database',
                'method': 'GET',
                'description': 'Returns PostgreSQL backup hint (pg_dump)'
            },
            {
                'path': '/api/export/users.json',
                'method': 'GET',
                'description': 'Export all user records as JSON'
            },
            {
                'path': '/api/export/dydaktyks.json',
                'method': 'GET',
                'description': 'Export all dydaktyk records as JSON'
            },
            {
                'path': '/api/search/users',
                'method': 'POST',
                'description': 'Search users by username/card_hex',
                'body': {'username': 'optional', 'card_hex': 'optional', 'limit': 50}
            }
        ]
    }
    return jsonify(docs), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found', 'path': request.path}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("Starting Kantech WebService...")
    print("API Documentation available at: http://localhost:5000/api/docs")
    app.run(host='0.0.0.0', port=5000, debug=False)

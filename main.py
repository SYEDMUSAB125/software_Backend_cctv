from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import timedelta, datetime
from urllib.parse import urlparse
import logging
from collections import defaultdict

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        # Parse the connection string
        result = urlparse("postgresql://neondb_owner:npg_xM01OzXSnBeb@ep-billowing-star-a2ozmeal-pooler.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
        
        # Establish a connection using the parsed components
        conn = psycopg2.connect(
            dbname=result.path[1:],  # Remove leading '/'
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port,
            sslmode="require"
        )
        logger.info("Successfully connected to the database")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def format_duration(duration):
    """Convert PostgreSQL interval to human-readable format"""
    if not duration:
        return "N/A"
    
    if isinstance(duration, timedelta):
        total_seconds = duration.total_seconds()
    else:
        total_seconds = duration
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    return f"{hours}h {minutes}m {seconds}s"

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                face_id, 
                status, 
                timestamp, 
                duration 
            FROM attendance 
            ORDER BY timestamp DESC
           
        """)
        
        attendance_data = cursor.fetchall()
        
        # Format the data for response
        formatted_data = []
        for record in attendance_data:
            formatted_data.append({
                "face_id": record['face_id'],
                "status": record['status'],
                "time": record['timestamp'].strftime("%I:%M %p"),  # 12-hour format
                "date": record['timestamp'].strftime("%Y-%m-%d"),  # ISO date format
                "duration": format_duration(record['duration'])
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "success": True,
            "data": formatted_data,
            "count": len(formatted_data)
        })
    
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({
            "success": False,
            "error": "Database operation failed"
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred"
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
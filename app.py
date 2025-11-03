from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', 'root'),
    'database': os.environ.get('DB_NAME', 'dbname'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_db():
    """Initialize database and create tables if they don't exist"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    status ENUM('pending', 'in-progress', 'completed') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
    finally:
        connection.close()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancers"""
    try:
        connection = get_db_connection()
        connection.close()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/todos', methods=['GET'])
def get_todos():
    """Get all todos with optional status filter"""
    try:
        status = request.args.get('status')
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            if status:
                cursor.execute("SELECT * FROM todos WHERE status = %s ORDER BY created_at DESC", (status,))
            else:
                cursor.execute("SELECT * FROM todos ORDER BY created_at DESC")
            todos = cursor.fetchall()
        
        connection.close()
        return jsonify({
            'success': True,
            'data': todos,
            'count': len(todos)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching todos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Get a specific todo by ID"""
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
            todo = cursor.fetchone()
        
        connection.close()
        
        if todo:
            return jsonify({
                'success': True,
                'data': todo
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Todo not found'
            }), 404
    except Exception as e:
        logger.error(f"Error fetching todo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/todos', methods=['POST'])
def create_todo():
    """Create a new todo"""
    try:
        data = request.get_json()
        
        if not data or 'title' not in data:
            return jsonify({
                'success': False,
                'error': 'Title is required'
            }), 400
        
        title = data['title']
        description = data.get('description', '')
        status = data.get('status', 'pending')
        
        if status not in ['pending', 'in-progress', 'completed']:
            status = 'pending'
        
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO todos (title, description, status) VALUES (%s, %s, %s)",
                (title, description, status)
            )
            connection.commit()
            todo_id = cursor.lastrowid
            
            cursor.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
            new_todo = cursor.fetchone()
        
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Todo created successfully',
            'data': new_todo
        }), 201
    except Exception as e:
        logger.error(f"Error creating todo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update an existing todo"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # Check if todo exists
            cursor.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
            if not cursor.fetchone():
                connection.close()
                return jsonify({
                    'success': False,
                    'error': 'Todo not found'
                }), 404
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            if 'title' in data:
                update_fields.append("title = %s")
                values.append(data['title'])
            
            if 'description' in data:
                update_fields.append("description = %s")
                values.append(data['description'])
            
            if 'status' in data:
                if data['status'] in ['pending', 'in-progress', 'completed']:
                    update_fields.append("status = %s")
                    values.append(data['status'])
            
            if not update_fields:
                connection.close()
                return jsonify({
                    'success': False,
                    'error': 'No valid fields to update'
                }), 400
            
            values.append(todo_id)
            query = f"UPDATE todos SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, values)
            connection.commit()
            
            cursor.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
            updated_todo = cursor.fetchone()
        
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Todo updated successfully',
            'data': updated_todo
        }), 200
    except Exception as e:
        logger.error(f"Error updating todo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo"""
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
            todo = cursor.fetchone()
            
            if not todo:
                connection.close()
                return jsonify({
                    'success': False,
                    'error': 'Todo not found'
                }), 404
            
            cursor.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
            connection.commit()
        
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Todo deleted successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error deleting todo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        'name': 'Todo List API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'get_all_todos': 'GET /api/todos',
            'get_todo': 'GET /api/todos/<id>',
            'create_todo': 'POST /api/todos',
            'update_todo': 'PUT /api/todos/<id>',
            'delete_todo': 'DELETE /api/todos/<id>'
        }
    }), 200

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Get port from environment variable
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)

from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Пути для хранения баз данных
DB_FOLDER = 'databases'
UNIVERSITY_DB_PATH = os.path.join(DB_FOLDER, 'university.db')
USER_DB_PATH = os.path.join(DB_FOLDER, 'user.db')
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

def get_db_connection(db_path):
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok'})
# --- API Маршруты ---

# --- Группы ---
@app.route('/api/get_universities', methods=['GET'])
def get_groups():
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        # Получаем группы с количеством студентов
        cursor.execute("""
            SELECT g.id, g.name, g.course, COUNT(s.id) as students_count
            FROM groups g
            LEFT JOIN students s ON s.group_id = g.id
            GROUP BY g.id
            ORDER BY g.name
        """)
        
        groups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(groups)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_group', methods=['POST'])
def add_group():
    data = request.get_json()
    name = data.get('name')
    course = data.get('course')
    
    if not name or not course:
        return jsonify({'error': 'Отсутствует название или курс'}), 400
    
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM groups WHERE name=?", (name,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Группа с таким названием уже существует'}), 400
        
        cursor.execute("INSERT INTO groups (name, course) VALUES (?, ?)", (name, course))
        conn.commit()
        group_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'message': 'Группа добавлена', 'id': group_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_group/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование группы
        cursor.execute("SELECT 1 FROM groups WHERE id=?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Группа не найдена'}), 404
        
        # Проверяем наличие студентов в группе
        cursor.execute("SELECT COUNT(*) FROM students WHERE group_id=?", (group_id,))
        student_count = cursor.fetchone()[0]
        
        if student_count > 0:
            conn.close()
            return jsonify({
                'error': 'В группе есть студенты',
                'student_count': student_count
            }), 400
        
        cursor.execute("DELETE FROM groups WHERE id=?", (group_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Группа удалена'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transfer_group', methods=['POST'])
def transfer_group():
    """Массовый перевод студентов в другую группу"""
    data = request.get_json()
    old_group_id = data.get('old_group_id')
    new_group_id = data.get('new_group_id')
    
    if not old_group_id or not new_group_id:
        return jsonify({'error': 'Не указаны ID групп'}), 400
    
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование групп
        cursor.execute("SELECT 1 FROM groups WHERE id=?", (old_group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Исходная группа не найдена'}), 404
            
        cursor.execute("SELECT 1 FROM groups WHERE id=?", (new_group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Новая группа не найдена'}), 404
        
        # Переводим студентов
        cursor.execute("""
            UPDATE students 
            SET group_id = ? 
            WHERE group_id = ?
        """, (new_group_id, old_group_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Студенты переведены'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Студенты ---

@app.route('/api/get_students', methods=['GET'])
@app.route('/api/get_students/<int:group_id>', methods=['GET'])
def get_students(group_id=None):
    """Получение студентов (всех или конкретной группы)"""
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        if group_id:
            # Для конкретной группы
            cursor.execute("""
                SELECT s.id, s.surname, s.name, s.middle_name, 
                       s.is_nonresident, g.name as group_name
                FROM students s
                JOIN groups g ON s.group_id = g.id
                WHERE s.group_id = ?
                ORDER BY s.surname, s.name
            """, (group_id,))
        else:
            # Все студенты
            cursor.execute("""
                SELECT s.id, s.surname, s.name, s.middle_name, 
                       s.is_nonresident, g.name as group_name
                FROM students s
                JOIN groups g ON s.group_id = g.id
                ORDER BY g.name, s.surname, s.name
            """)
        
        students = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(students)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_student', methods=['POST'])
def add_student():
    data = request.get_json()
    surname = data.get('surname')
    name = data.get('name')
    middle_name = data.get('middle_name')
    group_id = data.get('group_id')
    is_nonresident = data.get('is_nonresident', 0)
    
    if not surname or not name or not group_id:
        return jsonify({'error': 'Недостаточно данных'}), 400
    
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование группы
        cursor.execute("SELECT 1 FROM groups WHERE id=?", (group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Группа не найдена'}), 404
        
        cursor.execute("""
            INSERT INTO students 
            (surname, name, middle_name, group_id, is_nonresident)
            VALUES (?, ?, ?, ?, ?)
        """, (surname, name, middle_name, group_id, is_nonresident))
        
        conn.commit()
        student_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'message': 'Студент добавлен',
            'id': student_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование студента
        cursor.execute("SELECT 1 FROM students WHERE id=?", (student_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Студент не найден'}), 404
        
        cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Студент удален'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_student_nonresident', methods=['POST'])
def update_student_nonresident():
    data = request.get_json()
    student_id = data.get('student_id')
    is_nonresident = data.get('is_nonresident')
    
    if student_id is None or is_nonresident is None:
        return jsonify({'error': 'Не указаны обязательные параметры'}), 400
    
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE students 
            SET is_nonresident = ? 
            WHERE id = ?
        """, (is_nonresident, student_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Статус обновлен'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transfer_student', methods=['POST'])
def transfer_student():
    data = request.get_json()
    student_id = data.get('student_id')
    new_group_id = data.get('new_group_id')
    
    if not student_id or not new_group_id:
        return jsonify({'error': 'Не указаны ID студента или группы'}), 400
    
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование студента
        cursor.execute("SELECT 1 FROM students WHERE id=?", (student_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Студент не найден'}), 404
            
        # Проверяем существование новой группы
        cursor.execute("SELECT 1 FROM groups WHERE id=?", (new_group_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Группа не найдена'}), 404
        
        cursor.execute("""
            UPDATE students 
            SET group_id = ? 
            WHERE id = ?
        """, (new_group_id, student_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Студент переведен'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Предметы ---

@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, description FROM subjects")
        subjects = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(subjects)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subjects/add', methods=['POST'])
def add_subject():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': 'Название предмета обязательно'}), 400
    
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM subjects WHERE name=?", (name,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Предмет с таким названием уже существует'}), 400
        
        cursor.execute("""
            INSERT INTO subjects (name, description)
            VALUES (?, ?)
        """, (name, description))
        
        conn.commit()
        subject_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'message': 'Предмет добавлен',
            'id': subject_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subjects/<int:subject_id>', methods=['PUT'])
def update_subject(subject_id):
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '') 
    if not name:
        return jsonify({'error': 'Название предмета обязательно'}), 400 
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        # Проверяем существование предмета
        cursor.execute("SELECT 1 FROM subjects WHERE id=?", (subject_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Предмет не найден'}), 404
        # Проверяем уникальность нового имени
        cursor.execute("""
            SELECT 1 FROM subjects 
            WHERE name = ? AND id != ?
        """, (name, subject_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Предмет с таким названием уже существует'}), 400
        cursor.execute("""
            UPDATE subjects 
            SET name = ?, description = ?
            WHERE id = ?
        """, (name, description, subject_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Предмет обновлен'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/subjects/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование предмета
        cursor.execute("SELECT 1 FROM subjects WHERE id=?", (subject_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Предмет не найден'}), 404
        
        cursor.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Предмет удален'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Посещаемость ---

@app.route('/api/get_attendance', methods=['GET'])
def get_attendance():
    date = request.args.get('date')
    lesson_number = request.args.get('lesson_number')
    group_id = request.args.get('group_id')
    subject_id = request.args.get('subject_id')
    
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        query = """
            SELECT a.student_id, a.status 
            FROM attendance a
            WHERE a.date = ? AND a.lesson_number = ?
        """
        params = [date, lesson_number]
        
        if group_id:
            query += ' AND a.student_id IN (SELECT id FROM students WHERE group_id = ?)'
            params.append(group_id)
        
        if subject_id:
            query += ' AND a.subject_id = ?'
            params.append(subject_id)
        
        cursor.execute(query, params)
        result = {str(row['student_id']): row['status'] for row in cursor.fetchall()}
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_attendance', methods=['POST'])
def save_attendance():
    data = request.get_json()
    student_id = data.get('student_id')
    date = data.get('date')
    lesson_number = data.get('lesson_number')
    status = data.get('status')
    subject_id = data.get('subject_id')
    
    if not all([student_id, date, lesson_number, status]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO attendance 
            (student_id, date, lesson_number, subject_id, status)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, date, lesson_number, subject_id, status))
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'Attendance saved'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_statistics', methods=['GET'])
def get_statistics():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_id = request.args.get('group_id')
    subject_id = request.args.get('subject_id')
    lesson_number = request.args.get('lesson_number')
    try:
        conn = get_db_connection(UNIVERSITY_DB_PATH)
        cursor = conn.cursor()
        query = """
            SELECT 
                s.id,
                s.surname,
                s.name,
                g.name as group_name,
                sub.name as subject_name,
                SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN a.status = 'sick' THEN 1 ELSE 0 END) as sick,
                SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent,
                COUNT(a.id) as total
            FROM students s
            JOIN groups g ON g.id = s.group_id
            LEFT JOIN attendance a ON s.id = a.student_id
                AND a.date BETWEEN ? AND ?
                AND (? IS NULL OR a.lesson_number = ?)
                AND (? IS NULL OR a.subject_id = ?)
            LEFT JOIN subjects sub ON a.subject_id = sub.id
            WHERE (? IS NULL OR s.group_id = ?)
            GROUP BY s.id, s.surname, s.name, g.name, sub.name
            ORDER BY g.name, s.surname, s.name
        """
        cursor.execute(query, (
            start_date, end_date,
            lesson_number, lesson_number,
            subject_id, subject_id,
            group_id, group_id
        ))
        stats = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Пользователи ---

@app.route('/api/get_users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection(USER_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT username, password, role FROM users_data")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    if not username or not password or not role:
        return jsonify({'error': 'Все поля должны быть заполнены'}), 400
    
    try:
        conn = get_db_connection(USER_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM users_data WHERE username=?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Пользователь с таким логином уже существует'}), 400
        
        cursor.execute("""
            INSERT INTO users_data (username, password, role)
            VALUES (?, ?, ?)
        """, (username, password, role))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Пользователь успешно создан'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_user/<string:username>', methods=['DELETE'])
def delete_user(username):
    try:
        conn = get_db_connection(USER_DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем существование пользователя
        cursor.execute("SELECT 1 FROM users_data WHERE username=?", (username,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Пользователь не найден'}), 404
        
        # Проверяем, не пытаемся ли удалить последнего администратора
        cursor.execute("SELECT COUNT(*) FROM users_data WHERE role='admin'")
        admin_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT role FROM users_data WHERE username=?", (username,))
        user_role = cursor.fetchone()[0]
        
        if admin_count == 1 and user_role == 'admin':
            conn.close()
            return jsonify({'error': 'Нельзя удалить последнего администратора'}), 400
        
        cursor.execute("DELETE FROM users_data WHERE username=?", (username,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Пользователь удален'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth', methods=['POST'])
def auth():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Логин и пароль обязательны'}), 400
    
    try:
        conn = get_db_connection(USER_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role FROM users_data 
            WHERE username=? AND password=?
        """, (username, password))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({'role': result['role']})
        else:
            return jsonify({'error': 'Неверный логин или пароль'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
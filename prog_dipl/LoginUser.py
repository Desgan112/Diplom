import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, 
                            QPushButton, QVBoxLayout, QMessageBox, 
                            QHBoxLayout)
from PyQt5.QtGui import QIcon 

from demo_admin_window import AdminScreen
from user_window import UserWindow

class AuthApp(QWidget):
    def __init__(self):
        super().__init__()  
        self.current_user = None
        self.initUI()
        self.init_db()

    def initUI(self):
        self.setWindowTitle('Авторизация (Сетевая версия)')
        self.setWindowIcon(QIcon('icon.png'))
        self.setGeometry(100, 100, 400, 300)

        self.setStyleSheet("""
            QWidget { background-color: #f0f0f0; font-family: Arial; }
            QLabel { font-size: 16px; color: #333333; }
            QLineEdit { font-size: 14px; padding: 5px; border: 1px solid #cccccc; border-radius: 5px; }
            QPushButton { font-size: 16px; padding: 10px; background-color: #4CAF50; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
            QMessageBox { font-size: 14px; }
        """)

        main_layout = QVBoxLayout()
        main_layout.addStretch()

        form_layout = QVBoxLayout()

        self.username_label = QLabel('Логин:')
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText('Введите ваш логин')

        self.password_label = QLabel('Пароль:')
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText('Введите ваш пароль')
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton('Войти', self)
        self.login_button.clicked.connect(self.check_credentials)

        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.login_button)

        h_layout = QHBoxLayout()
        h_layout.addStretch()
        h_layout.addLayout(form_layout)
        h_layout.addStretch()

        main_layout.addLayout(h_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def init_db(self):
        """Инициализация централизованной базы данных"""
        self.conn = sqlite3.connect('//server/share/university_network.db')
        self.cursor = self.conn.cursor()

        # Создаем таблицы, если их нет
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                full_name TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                course INTEGER DEFAULT 1,
                created_by INTEGER,
                FOREIGN KEY(created_by) REFERENCES users(id)
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surname TEXT NOT NULL,
                name TEXT NOT NULL,
                middle_name TEXT,
                group_id INTEGER,
                is_nonresident BOOLEAN DEFAULT 0,
                added_by INTEGER,
                FOREIGN KEY(group_id) REFERENCES groups(id),
                FOREIGN KEY(added_by) REFERENCES users(id)
            )
        ''')
        
        self.conn.commit()

    def check_credentials(self):
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            self.cursor.execute('''
                SELECT id, role, full_name FROM users 
                WHERE username = ? AND password = ?
            ''', (username, password))

            result = self.cursor.fetchone()

            if result:
                user_id, role, full_name = result
                self.current_user = {
                    'id': user_id,
                    'username': username,
                    'role': role,
                    'full_name': full_name
                }
                self.show_role_screen(role)
            else:
                QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', 
                                f'Не удалось подключиться к серверу:\n{str(e)}')

    def show_role_screen(self, role):
        if role == 'Admin':
            self.admin_screen = AdminScreen(self.current_user, self.conn)
            self.admin_screen.show()
        elif role == 'User':
            self.user_screen = UserWindow(self.current_user, self.conn)
            self.user_screen.show()
        self.hide()  # Скрываем окно авторизации

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)  
    auth_app = AuthApp()  
    auth_app.show()  
    sys.exit(app.exec_())
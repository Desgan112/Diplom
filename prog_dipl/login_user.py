import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from user_window import UserWindow
from admin_window import AdminScreen

# URL вашего сервера
SERVER_URL = 'http://127.0.0.1:5000'

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход в систему — Авторизация")
        self.resize(400, 300)
        self.setup_ui()
        self.setup_connection_check()

    def setup_ui(self):
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.setSpacing(15)

        # Заголовок
        title_label = QLabel("Добро пожаловать! Пожалуйста, войдите в систему")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Поле для логина
        login_label = QLabel("Логин:")
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Введите ваш логин")
        main_layout.addWidget(login_label)
        main_layout.addWidget(self.input_username)

        # Поле для пароля
        password_label = QLabel("Пароль:")
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Введите ваш пароль")
        self.input_password.setEchoMode(QLineEdit.Password)
        main_layout.addWidget(password_label)
        main_layout.addWidget(self.input_password)

        # Кнопка входа
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.handle_login)
        main_layout.addWidget(self.login_button)

        # Статус соединения
        self.status_label = QLabel("Проверка соединения с сервером...")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)
        
        # Применение стилей
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f2f5;
                font-family: Arial;
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)

    def setup_connection_check(self):
        """Настройка проверки соединения с сервером"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_server_connection)
        self.timer.start(5000)  # Проверка каждые 5 секунд
        self.check_server_connection()  # Первая проверка сразу

    def check_server_connection(self):
        """Проверка соединения с сервером"""
        try:
            response = requests.get(f"{SERVER_URL}/api/ping", timeout=2)
            if response.status_code == 200:
                self.status_label.setText("✓ Соединение с сервером установлено")
                self.status_label.setStyleSheet("color: green;")
                self.login_button.setEnabled(True)
            else:
                self.status_label.setText("✗ Ошибка соединения с сервером")
                self.status_label.setStyleSheet("color: red;")
                self.login_button.setEnabled(False)
        except requests.RequestException:
            self.status_label.setText("✗ Сервер недоступен")
            self.status_label.setStyleSheet("color: red;")
            self.login_button.setEnabled(False)

    def handle_login(self):
        """Обработка попытки входа"""
        username = self.input_username.text().strip()
        password = self.input_password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите логин и пароль")
            return
        try:
            response = requests.post(
                f"{SERVER_URL}/api/auth",
                json={'username': username, 'password': password},
                timeout=5
            )
            if response.status_code == 200:
                role = response.json().get('role', 'user')
                self.open_role_window(role)
            else:
                error = response.json().get('error', 'Неизвестная ошибка')
                QMessageBox.warning(self, "Ошибка", f"Ошибка авторизации: {error}")
    
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к серверу: {str(e)}")

    def open_role_window(self, role):
        """Открытие окна в зависимости от роли"""
        self.hide()  # Скрываем окно авторизации
        
        if role.lower() == 'admin':
            self.window = AdminScreen()
        else:
            self.window = UserWindow()
            
        self.window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
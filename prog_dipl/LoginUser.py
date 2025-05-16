import sys  
import sqlite3  
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout  
from PyQt5.QtGui import QIcon 

from demo_admin_window import AdminScreen  # Импорт окна администратора
from user_window import UserScreen  # Импорт окна пользователя

class AuthApp(QWidget):
    def __init__(self):
        super().__init__()  
        self.initUI()  

    def initUI(self):
        # Настройка основного окна
        self.setWindowTitle('Авторизация')  # Установка заголовка окна
        self.setWindowIcon(QIcon('icon.png'))  # Установка иконки окна
        self.setGeometry(100, 100, 400, 300)  # Установка размеров и положения окна

        # Внешнее оформление с помощью CSS
        self.setStyleSheet("""
            QWidget { background-color: #f0f0f0; font-family: Arial; }
            QLabel { font-size: 16px; color: #333333; }
            QLineEdit { font-size: 14px; padding: 5px; border: 1px solid #cccccc; border-radius: 5px; }
            QPushButton { font-size: 16px; padding: 10px; background-color: #4CAF50; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
            QMessageBox { font-size: 14px; }
        """)

        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.addStretch()  

        # Вертикальный layout для формы авторизации
        form_layout = QVBoxLayout()

        # Создание и настройка виджетов для ввода логина и пароля
        self.username_label = QLabel('Логин:')  # Надпись для поля логина
        self.username_input = QLineEdit(self)  # Поле для ввода логина
        self.username_input.setPlaceholderText('Введите ваш логин')  # Подсказка в поле логина

        self.password_label = QLabel('Пароль:')  # Надпись для поля пароля
        self.password_input = QLineEdit(self)  # Поле для ввода пароля
        self.password_input.setPlaceholderText('Введите ваш пароль')  # Подсказка в поле пароля
        self.password_input.setEchoMode(QLineEdit.Password)  # Скрытие вводимого пароля

        # Кнопка для входа в систему
        self.login_button = QPushButton('Войти', self)
        self.login_button.clicked.connect(self.check_LogPas)  # Подключение функции проверки логина и пароля

        # Добавление виджетов в форму
        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.login_button)

        # Горизонтальный layout для центрирования формы
        h_layout = QHBoxLayout()
        h_layout.addStretch()  # Добавление растягивающего пространства слева
        h_layout.addLayout(form_layout)  # Добавление формы в центр
        h_layout.addStretch()  # Добавление растягивающего пространства справа

        # Добавление горизонтального layout в основной layout
        main_layout.addLayout(h_layout)
        main_layout.addStretch()  # Добавление растягивающего пространства внизу

        # Установка основного layout для окна
        self.setLayout(main_layout)

    def check_LogPas(self):
        # Получение введенных логина и пароля
        username = self.username_input.text()
        password = self.password_input.text()

        try:
            # Подключение к базе данных и проверка учетных данных
            with sqlite3.connect('user.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT RollesUser FROM polsovatel WHERE username = ? AND password = ?", (username, password))
                result = cursor.fetchone()  # Получение результата запроса

            if result:
                role = result[0]  # Получение роли пользователя
                self.show_role_screen(role) 
            else:
                QMessageBox.warning(self, 'Ошибка', 'Неверный логин или пароль')
        except sqlite3.Error as e:
            # Вывод сообщения об ошибке, если возникла проблема с базой данных
            QMessageBox.critical(self, 'Ошибка базы данных', f'Произошла ошибка при подключении к базе данных: {e}')

    def show_role_screen(self, role):        # Открытие окна в зависимости от роли пользователя
        if role == 'Admin':
            self.admin_screen = AdminScreen()  # Создание окна администратора
            self.admin_screen.show()  # Отображение окна администратора
        elif role == 'User':
            self.user_screen = UserScreen()  # Создание окна пользователя
            self.user_screen.show()  # Отображение окна пользователя
        self.close()  # Закрытие окна авторизации


if __name__ == '__main__':
    app = QApplication(sys.argv)  
    auth_app = AuthApp()  
    auth_app.show()  
    sys.exit(app.exec_()) 
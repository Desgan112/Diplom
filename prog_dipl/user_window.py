from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QFont

class UserScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Окно пользователя')
        self.setGeometry(100, 100, 600, 400)

        label = QLabel('Добро пожаловать, Пользователь!', self)
        label.setFont(QFont('Arial', 16))
        label.move(50, 50)

        # Пример функциональности для пользователя
        self.view_profile_button = QPushButton('Посмотреть профиль', self)
        self.view_profile_button.move(50, 100)
        self.view_profile_button.clicked.connect(self.view_profile)

        self.show()

    def view_profile(self):
        QMessageBox.information(self, 'Профиль', 'Функция просмотра профиля')
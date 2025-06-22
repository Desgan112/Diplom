import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QMessageBox,
    QVBoxLayout, QHBoxLayout, QLineEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QFormLayout, QFrame, QDialog,
    QComboBox, QCheckBox, QSizePolicy, QSpacerItem, QGroupBox
)
from PyQt5.QtGui import QFont, QIntValidator, QFontMetrics, QIcon
from PyQt5.QtCore import Qt

API_URL = 'http://127.0.0.1:5000'


class AdminScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Окно администратора')
        self.setGeometry(100, 100, 1200, 850)
        self.setMinimumSize(1000, 700)

        self.init_ui()
        self.set_style()
        self.load_groups()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("Панель администратора")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Вкладка "Пользователи"
        user_tab = QWidget()
        user_tab_layout = QVBoxLayout(user_tab)
        user_tab_layout.setContentsMargins(10, 10, 10, 10)
        user_tab_layout.setSpacing(15)

        # Группа для формы добавления пользователя
        user_form_group = QGroupBox("Добавить нового пользователя")
        user_form_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        form_layout = QFormLayout(user_form_group)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(10)

        # Поля ввода
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите логин")
        form_layout.addRow("Логин:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Пароль:", self.password_input)

        self.role_input = QComboBox()
        self.role_input.addItems(["admin", "user"])
        form_layout.addRow("Роль:", self.role_input)

        # Кнопка создания пользователя
        self.create_user_button = QPushButton("Создать пользователя")
        self.create_user_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.create_user_button.clicked.connect(self.create_user)  
        # Контейнер для кнопки
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(self.create_user_button)
        button_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.addRow(button_container)
        user_tab_layout.addWidget(user_form_group)
        # Таблица пользователей
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(['Логин', 'Пароль', 'Роль', 'Действия'])
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setAlternatingRowColors(True)
        
        # Стили для таблицы
        self.users_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                gridline-color: #eee;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
            }
        """)
        
        user_tab_layout.addWidget(self.users_table, stretch=1)

        # Вкладка "Группы"
        groups_tab = QWidget()
        groups_layout = QVBoxLayout(groups_tab)
        groups_layout.setContentsMargins(10, 10, 10, 10)
        groups_layout.setSpacing(10)

        # Группа для формы добавления
        add_group_group = QGroupBox("Добавить новую группу")
        add_group_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        add_group_layout = QVBoxLayout(add_group_group)
        add_group_layout.setContentsMargins(15, 15, 15, 10)
        form_layout = QHBoxLayout()
        form_layout.setSpacing(15)

        # Поля ввода
        name_layout = QVBoxLayout()
        name_layout.setSpacing(5)
        name_layout.addWidget(QLabel('Название группы:'))
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText('Например: ИВТ-21')
        name_layout.addWidget(self.group_name_input)

        course_layout = QVBoxLayout()
        course_layout.setSpacing(5)
        course_layout.addWidget(QLabel('Курс (1-4):'))
        self.group_course_input = QLineEdit()
        self.group_course_input.setValidator(QIntValidator(1, 4))
        self.group_course_input.setPlaceholderText('Введите курс (1-4)')
        course_layout.addWidget(self.group_course_input)

        form_layout.addLayout(name_layout)
        form_layout.addLayout(course_layout)

        # Кнопка добавления
        self.add_group_btn = QPushButton('Добавить')
        self.add_group_btn.setFixedWidth(120)
        self.add_group_btn.clicked.connect(self.add_group)
        form_layout.addWidget(self.add_group_btn, alignment=Qt.AlignBottom)
    
        add_group_layout.addLayout(form_layout)
        groups_layout.addWidget(add_group_group)

        # Таблица групп
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(5)
        self.groups_table.setHorizontalHeaderLabels(['ID', 'Название', 'Курс', 'Кол-во студентов', 'Действия'])
        header = self.groups_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  
        header.setSectionResizeMode(1, QHeaderView.Stretch)  
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  
        self.groups_table.verticalHeader().setVisible(False)
        self.groups_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.groups_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.groups_table.setAlternatingRowColors(True)
        self.groups_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        groups_layout.addWidget(self.groups_table, stretch=1)
        button_panel = QHBoxLayout()
        button_panel.setSpacing(10)
        self.delete_group_btn = QPushButton('Удалить выбранную группу')
        self.delete_group_btn.clicked.connect(self.delete_group)
        refresh_btn = QPushButton('Обновить список')
        refresh_btn.clicked.connect(self.load_groups)
        button_panel.addWidget(self.delete_group_btn)
        button_panel.addStretch()
        button_panel.addWidget(refresh_btn)
        groups_layout.addLayout(button_panel)

        # Вкладка "Предметы"
        self.subjects_widget = SubjectsTab()

        # Добавляем вкладки
        self.tabs.addTab(user_tab, "Пользователи")
        self.tabs.addTab(groups_tab, "Группы")
        self.tabs.addTab(self.subjects_widget, "Предметы")

    def load_users(self):
        """Загрузка списка пользователей из API"""
        try:
            response = requests.get(f'{API_URL}/api/get_users')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            
            users = response.json()
            self.users_table.setRowCount(len(users))
            
            for row_idx, user in enumerate(users):
                self.users_table.setItem(row_idx, 0, QTableWidgetItem(user['username']))
                self.users_table.setItem(row_idx, 1, QTableWidgetItem(user['password']))
                self.users_table.setItem(row_idx, 2, QTableWidgetItem(user['role']))
                
                # Кнопка удаления
                delete_btn = QPushButton('Удалить')
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 5px;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #d32f2f;
                    }
                """)
                delete_btn.clicked.connect(lambda _, username=user['username']: self.delete_user(username))
                
                # Контейнер для кнопки
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.addWidget(delete_btn)
                btn_layout.setAlignment(Qt.AlignCenter)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                self.users_table.setCellWidget(row_idx, 3, btn_container)
                
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки пользователей: {str(e)}')

    def delete_user(self, username):
        """Удаление пользователя"""
        reply = QMessageBox.question(
            self, 'Подтверждение',
            f'Вы уверены, что хотите удалить пользователя {username}?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        try:
            response = requests.delete(f'{API_URL}/api/delete_user/{username}')
            
            if response.status_code == 200:
                QMessageBox.information(self, 'Успех', 'Пользователь успешно удален')
                self.load_users()
            else:
                error = response.json().get('error', 'Неизвестная ошибка')
                QMessageBox.warning(self, 'Ошибка', f'Ошибка удаления: {error}')
                
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка соединения: {str(e)}')

    def create_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все обязательные поля")
            return

        try:
            response = requests.post(f'{API_URL}/api/register', json={
                'username': username,
                'password': password,
                'role': role
            }, timeout=5)
            
            if response.status_code == 201:
                QMessageBox.information(self, "Успех", "Пользователь успешно добавлен")
                self.username_input.clear()
                self.password_input.clear()
                self.load_users()
            else:
                error_msg = response.json().get('error', 'Неизвестная ошибка')
                QMessageBox.warning(self, "Ошибка", f"Ошибка: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при подключении: {e}")

    def load_groups(self):
        try:
            response = requests.get(f'{API_URL}/api/get_universities')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            groups = response.json()
            self.groups_table.setRowCount(len(groups))
            
            for row_idx, g in enumerate(groups):
                self.groups_table.setItem(row_idx, 0, QTableWidgetItem(str(g['id'])))
                self.groups_table.setItem(row_idx, 1, QTableWidgetItem(g['name']))
                self.groups_table.setItem(row_idx, 2, QTableWidgetItem(str(g['course'])))
                self.groups_table.setItem(row_idx, 3, QTableWidgetItem(str(g['students_count'])))
                
                # Кнопка открытия
                open_btn = QPushButton('Открыть')
                open_btn.setStyleSheet("""
                    QPushButton {
                        padding: 5px;
                        min-width: 80px;
                    }
                """)
                open_btn.clicked.connect(lambda _, gid=g['id'], gname=g['name']: self.open_student_management(gid, gname))
                
                # Контейнер для кнопки
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.addWidget(open_btn)
                btn_layout.setAlignment(Qt.AlignCenter)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                
                self.groups_table.setCellWidget(row_idx, 4, btn_container)
                
            # Автоматическое растягивание строк
            self.groups_table.resizeRowsToContents()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке групп: {str(e)}')

    def open_student_management(self, group_id, group_name):
        dlg = StudentManagementWindow(group_id, group_name)
        dlg.exec_()
        self.load_groups()

    def add_group(self):
        name = self.group_name_input.text().strip()
        course_text = self.group_course_input.text().strip()
        if not name or not course_text:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return
        try:
            course = int(course_text)
            response = requests.post(f'{API_URL}/api/add_group', json={
                'name': name,
                'course': course
            })
            if response.status_code not in (200, 201):
                raise Exception(response.json().get('error', 'Ошибка'))
            self.group_name_input.clear()
            self.group_course_input.clear()
            self.load_groups()
            QMessageBox.information(self, 'Успех', 'Группа добавлена')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить группу: {str(e)}')

    def delete_group(self):
        selected = self.groups_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, 'Ошибка', 'Выберите группу для удаления')
            return
        row = selected[0].row()
        group_id = int(self.groups_table.item(row, 0).text())
        group_name = self.groups_table.item(row, 1).text()
        try:
            response = requests.get(f'{API_URL}/api/get_students/{group_id}')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            students = response.json()
            student_count = len(students)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка получения студентов: {str(e)}')
            return
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Подтверждение')
        msg_box.setText(f'В группе {group_name} есть {student_count} студентов. Что вы хотите сделать?')
        delete_all_btn = msg_box.addButton('Удалить всех', QMessageBox.YesRole)
        transfer_btn = msg_box.addButton('Перевести', QMessageBox.NoRole)
        cancel_btn = msg_box.addButton('Отмена', QMessageBox.RejectRole)
        msg_box.setDefaultButton(cancel_btn)
        msg_box.exec_()
        if msg_box.clickedButton() == delete_all_btn:
            try:
                response_del = requests.delete(f'{API_URL}/api/delete_group/{group_id}')
                if response_del.status_code != 200:
                    raise Exception(response_del.json().get('error', 'Ошибка'))
                self.load_groups()
                QMessageBox.information(self, 'Успех', 'Группа и все её студенты удалены')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка: {str(e)}')
        elif msg_box.clickedButton() == transfer_btn:
            self.transfer_students_before_delete(group_id, group_name)
        else:
            return

    def transfer_students_before_delete(self, group_id, group_name):
        dlg = QDialog(self)
        dlg.setWindowTitle(f'Перевод студентов из группы {group_name}')
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel('Выберите новую группу:'))

        try:
            response = requests.get(f'{API_URL}/api/get_universities')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            groups = response.json()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки групп: {str(e)}')
            return

        g_list = [g for g in groups if g['id'] != group_id]
        if not g_list:
            QMessageBox.warning(self, 'Ошибка', 'Нет других групп для перевода')
            return

        group_combo = QComboBox()
        for g in g_list:
            group_combo.addItem(g['name'], g['id'])
        layout.addWidget(group_combo)

        btn_box = QHBoxLayout()
        transfer_btn = QPushButton('Перевести и удалить')
        transfer_btn.setFont(QFont('Arial', 13))
        transfer_btn.clicked.connect(lambda _, sid=group_combo.currentData(): self.do_transfer_and_delete(group_id, sid, dlg))
        cancel_btn = QPushButton('Отмена')
        cancel_btn.setFont(QFont('Arial', 13))
        cancel_btn.clicked.connect(dlg.reject)
        btn_box.addWidget(transfer_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)

        if dlg.exec_() == QDialog.Accepted:
            self.load_groups()

    def do_transfer_and_delete(self, old_group_id, new_group_id, dlg):
        try:
            # Перевод студентов
            response = requests.post(f'{API_URL}/api/transfer_group', json={
                'old_group_id': old_group_id,
                'new_group_id': new_group_id
            })
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            # Удаление группы
            del_response = requests.delete(f'{API_URL}/api/delete_group/{old_group_id}')
            if del_response.status_code != 200:
                raise Exception(del_response.json().get('error', 'Ошибка'))
            dlg.accept()
            self.load_groups()
            QMessageBox.information(self, 'Успех', 'Студенты переведены и группа удалена')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {str(e)}')

    def set_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f2f5;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 5px;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-height: 25px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTabWidget::pane {
                border: none;
                margin-top: 10px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
            }
            QCheckBox {
                spacing: 5px;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)

class StudentManagementWindow(QDialog):
    def __init__(self, group_id, group_name):
        super().__init__()
        self.group_id = group_id
        self.group_name = group_name
        self.setWindowTitle(f'Группа: {group_name}')
        self.setMinimumSize(1000, 800)
        self.all_groups = []

        self.init_ui()
        self.load_students()
        self.load_all_groups()
        self.set_style()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title_label = QLabel(f"Управление студентами группы {self.group_name}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Таблица студентов
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(6)
        self.students_table.setHorizontalHeaderLabels(['Фамилия', 'Имя', 'Отчество', 'Группа', 'Приезжий', 'Действия'])
        header = self.students_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.students_table.verticalHeader().setVisible(False)
        self.students_table.setAlternatingRowColors(True)
        self.students_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.students_table)

        # Форма добавления студента
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.StyledPanel)
        form_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)

        form_title = QLabel('Добавить нового студента')
        form_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        form_layout.addRow(form_title)

        self.surname_edit = QLineEdit()
        self.surname_edit.setPlaceholderText('Иванов')
        form_layout.addRow('Фамилия*:', self.surname_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('Иван')
        form_layout.addRow('Имя*:', self.name_edit)

        self.middle_edit = QLineEdit()
        self.middle_edit.setPlaceholderText('Иванович (необязательно)')
        form_layout.addRow('Отчество:', self.middle_edit)

        self.nonresident_checkbox = QCheckBox('Приезжий')
        form_layout.addRow('', self.nonresident_checkbox)

        self.add_student_btn = QPushButton('Добавить студента')
        self.add_student_btn.setFixedWidth(180)
        self.add_student_btn.clicked.connect(self.add_student)
        form_layout.addRow(self.add_student_btn)
        self.add_student_btn.setStyleSheet("background-color: green;")
        layout.addWidget(form_frame)

        close_btn = QPushButton('Закрыть')
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def load_students(self):
        try:
            response = requests.get(f'{API_URL}/api/get_students/{self.group_id}')
            if response.status_code != 200:
                raise Exception(f"Ошибка: {response.json().get('error', 'Неизвестная ошибка')}")
            students = response.json()
            self.students_table.setRowCount(len(students))
            for row_idx, student in enumerate(students):
                self.students_table.setItem(row_idx, 0, QTableWidgetItem(student['surname']))
                self.students_table.setItem(row_idx, 1, QTableWidgetItem(student['name']))
                self.students_table.setItem(row_idx, 2, QTableWidgetItem(student.get('middle_name', '')))
                
                nonresident_check = QCheckBox()
                nonresident_check.setChecked(bool(student['is_nonresident']))
                nonresident_check.stateChanged.connect(
                    lambda state, sid=student['id']: self.update_nonresident_status(sid, state))
                cell_widget = QWidget()
                layout = QHBoxLayout(cell_widget)
                layout.addWidget(nonresident_check)
                layout.setAlignment(Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                self.students_table.setCellWidget(row_idx, 4, cell_widget)

                delete_btn = QPushButton('Исключить')
                delete_btn.clicked.connect(lambda _, sid=student['id']: self.delete_student(sid))
                transfer_btn = QPushButton('Перевести')
                transfer_btn.clicked.connect(lambda _, sid=student['id']: self.transfer_student(sid))
                
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.addWidget(delete_btn)
                btn_layout.addWidget(transfer_btn)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                btn_layout.setSpacing(5)
                self.students_table.setCellWidget(row_idx, 5, btn_container)
                self.students_table.setRowHeight(row_idx, 50)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки студентов: {str(e)}')

    def update_nonresident_status(self, student_id, state):
        is_nonresident = 1 if state == Qt.Checked else 0
        try:
            response = requests.post(f'{API_URL}/api/update_student_nonresident', json={
                'student_id': student_id,
                'is_nonresident': is_nonresident
            })
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось обновить статус: {str(e)}')

    def load_all_groups(self):
        try:
            response = requests.get(f'{API_URL}/api/get_universities')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            self.all_groups = response.json()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки групп: {str(e)}')

    def add_student(self):
        surname = self.surname_edit.text().strip()
        name = self.name_edit.text().strip()
        middle = self.middle_edit.text().strip() or None
        is_nonresident = 1 if self.nonresident_checkbox.isChecked() else 0

        if not surname or not name:
            QMessageBox.warning(self, 'Ошибка', 'Заполните обязательные поля (Фамилия и Имя)')
            return
        try:
            response = requests.post(f'{API_URL}/api/add_student', json={
                'surname': surname,
                'name': name,
                'middle_name': middle,
                'group_id': self.group_id,
                'is_nonresident': is_nonresident
            })
            if response.status_code not in (200, 201):
                raise Exception(response.json().get('error', 'Ошибка'))
            self.surname_edit.clear()
            self.name_edit.clear()
            self.middle_edit.clear()
            self.nonresident_checkbox.setChecked(False)
            self.load_students()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить студента: {str(e)}')

    def delete_student(self, student_id):
        reply = QMessageBox.question(
            self, 'Подтверждение', 
            'Исключить этого студента из группы?', 
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        try:
            response = requests.delete(f'{API_URL}/api/delete_student/{student_id}')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            self.load_students()
            QMessageBox.information(self, 'Успех', 'Студент исключен из группы')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {str(e)}')

    def transfer_student(self, student_id):
        dialog = QDialog(self)
        dialog.setWindowTitle('Перевод студента')
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('Выберите новую группу:'))

        try:
            response = requests.get(f'{API_URL}/api/get_universities')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            groups = response.json()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки групп: {str(e)}')
            return

        g_list = [g for g in groups if g['id'] != self.group_id]
        if not g_list:
            QMessageBox.warning(self, 'Ошибка', 'Нет других групп для перевода')
            return

        group_combo = QComboBox()
        for g in g_list:
            group_combo.addItem(g['name'], g['id'])
        layout.addWidget(group_combo)

        btn_box = QHBoxLayout()
        transfer_btn = QPushButton('Перевести')
        transfer_btn.setFont(self.font())
        transfer_btn.clicked.connect(lambda: self.do_transfer(student_id, group_combo.currentData(), dialog))
        cancel_btn = QPushButton('Отмена')
        cancel_btn.setFont(self.font())
        cancel_btn.clicked.connect(dialog.reject)
        btn_box.addWidget(transfer_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)

        if dialog.exec_() == QDialog.Accepted:
            self.load_students()

    def do_transfer(self, student_id, new_group_id, dialog):
        try:
            response = requests.post(f'{API_URL}/api/transfer_student', json={
                'student_id': student_id,
                'new_group_id': new_group_id
            })
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            QMessageBox.information(self, 'Успех', 'Студент переведен')
            dialog.accept()
            self.load_students()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {str(e)}')


    def set_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f2f5;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 5px;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-height: 25px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
            QTabWidget::pane {
                border: none;
                margin-top: 10px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 8px 12px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
            }
            QCheckBox {
                spacing: 5px;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
            }
        """)


class SubjectsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_subjects()
        self.set_style()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Форма добавления предмета
        form_frame = QFrame()
        form_frame.setStyleSheet("background-color: white; border-radius: 8px; padding: 15px;")
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(10)

        title = QLabel('Добавить новый предмет')
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        form_layout.addRow(title)

        self.subject_name = QLineEdit()
        self.subject_name.setPlaceholderText('Название предмета')
        form_layout.addRow('Название*:', self.subject_name)

        self.subject_desc = QLineEdit()
        self.subject_desc.setPlaceholderText('Описание (необязательно)')
        form_layout.addRow('Описание:', self.subject_desc)

        self.add_subject_btn = QPushButton('Добавить предмет')
        self.add_subject_btn.clicked.connect(self.add_subject)
        self.add_subject_btn.setFixedWidth(180)
        self.add_subject_btn.setStyleSheet("background-color: green;")
        form_layout.addRow(self.add_subject_btn)

        layout.addWidget(form_frame)

        # Таблица предметов
        self.subjects_table = QTableWidget()
        self.subjects_table.setColumnCount(4)
        self.subjects_table.setHorizontalHeaderLabels(['ID', 'Название', 'Описание', ''])
        header = self.subjects_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.subjects_table.verticalHeader().setVisible(False)
        self.subjects_table.setAlternatingRowColors(True)
        self.subjects_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.subjects_table)

    def load_subjects(self):
        try:
            response = requests.get(f'{API_URL}/api/subjects')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            subjects = response.json()
            self.subjects_table.setRowCount(len(subjects))
            for row_idx, subj in enumerate(subjects):
                self.subjects_table.setItem(row_idx, 0, QTableWidgetItem(str(subj['id'])))
                self.subjects_table.setItem(row_idx, 1, QTableWidgetItem(subj['name']))
                self.subjects_table.setItem(row_idx, 2, QTableWidgetItem(subj.get('description', '')))
                # Кнопки "Изменить" и "Удалить"
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                btn_layout.setSpacing(5)
                edit_btn = QPushButton('Изменить')
                edit_btn.setFont(QFont('Arial', 13))
                edit_btn.clicked.connect(lambda _, sid=subj['id']: self.edit_subject(sid))
                delete_btn = QPushButton('Удалить')
                delete_btn.setFont(QFont('Arial', 13))
                delete_btn.clicked.connect(lambda _, sid=subj['id']: self.delete_subject(sid))
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                self.subjects_table.setCellWidget(row_idx, 3, btn_container)
                self.subjects_table.setRowHeight(row_idx, 50)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить предметы: {str(e)}')

    def add_subject(self):
        name = self.subject_name.text().strip()
        description = self.subject_desc.text().strip()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Название предмета обязательно!")
            return

        try:
            response = requests.post(
                f"{API_URL}/api/subjects/add",
                json={"name": name, "description": description},
                timeout=5  # Таймаут 5 секунд
        )

            if response.status_code == 201:
            # Успешно добавлено
                QMessageBox.information(self, "Успех", "Предмет добавлен!")
                self.subject_name.clear()
                self.subject_desc.clear()
                self.load_subjects()  # Обновляем список
            else:
                
                error_msg = response.json().get("error", "Неизвестная ошибка")
                QMessageBox.warning(self, "Ошибка", f"Не удалось добавить предмет: {error_msg}")

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Ошибка сети", f"Не удалось отправить запрос: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неизвестная ошибка: {e}")

    def delete_subject(self, subject_id):
        try:
            response = requests.delete(f'{API_URL}/api/subjects/{subject_id}')
            if response.status_code != 200:
                raise Exception(response.json().get('error', 'Ошибка'))
            self.load_subjects()
            QMessageBox.information(self, 'Успех', 'Предмет удален')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка: {str(e)}')

    def edit_subject(self, subject_id):
        row_idx = None
        for row in range(self.subjects_table.rowCount()):
            item = self.subjects_table.item(row, 0)
            if item and item.text() == str(subject_id):
                row_idx = row
                break
        if row_idx is None:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось найти предмет для редактирования')
            return

        name_item = self.subjects_table.item(row_idx, 1)
        desc_item = self.subjects_table.item(row_idx, 2)
        current_name = name_item.text() if name_item else ''
        current_desc = desc_item.text() if desc_item else ''

        dialog = QDialog(self)
        dialog.setWindowTitle('Редактировать предмет')
        layout = QVBoxLayout(dialog)

        form = QFormLayout()
        name_edit = QLineEdit(current_name)
        desc_edit = QLineEdit(current_desc)

        form.addRow('Название*:', name_edit)
        form.addRow('Описание:', desc_edit)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        save_btn = QPushButton('Сохранить')
        cancel_btn = QPushButton('Отмена')
        save_btn.setFont(QFont('Arial', 13))
        cancel_btn.setFont(QFont('Arial', 13))
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)

        def save_changes():
            new_name = name_edit.text().strip()
            new_desc = desc_edit.text().strip()
            if not new_name:
                QMessageBox.warning(dialog, 'Ошибка', 'Заполните название')
                return
            try:
                response = requests.put(f'{API_URL}/api/subjects/{subject_id}', json={
                    'name': new_name,
                    'description': new_desc
                })
                if response.status_code != 200:
                    raise Exception(response.json().get('error', 'Ошибка'))
                self.load_subjects()
                QMessageBox.information(self, 'Успех', 'Предмет обновлен')
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, 'Ошибка', f'Не удалось обновить предмет: {str(e)}')

        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec_()

    def set_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f2f5;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 5px;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-height: 25px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AdminScreen()
    window.show()
    sys.exit(app.exec_())
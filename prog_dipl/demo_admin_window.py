import sqlite3
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QMessageBox, 
                            QVBoxLayout, QHBoxLayout, QLineEdit,
                            QTableWidget, QTableWidgetItem, QDialog, 
                            QFrame, QSizePolicy, QHeaderView, QFormLayout,
                            QComboBox)
from PyQt5.QtGui import QFont, QIntValidator, QColor
from PyQt5.QtCore import Qt

class StudentManagementWindow(QDialog):
    def __init__(self, group_id, group_name, conn):
        super().__init__()
        self.group_id = group_id
        self.group_name = group_name
        self.conn = conn
        self.cursor = self.conn.cursor()
        
        self.setWindowTitle(f'Группа: {group_name}')
        self.setMinimumSize(850, 650)
        
        self.init_ui()
        self.load_students()
        self.load_all_groups()
        self.set_style()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Таблица студентов
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(5)
        self.students_table.setHorizontalHeaderLabels(['Фамилия', 'Имя', 'Отчество', 'Группа', 'Действия'])
        self.students_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.students_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.students_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.students_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.students_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.students_table.verticalHeader().setVisible(False)
        layout.addWidget(self.students_table)
        
        # Форма добавления студента
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.StyledPanel)
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)
        
        self.surname_edit = QLineEdit()
        self.surname_edit.setPlaceholderText('Иванов')
        form_layout.addRow('Фамилия*:', self.surname_edit)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('Иван')
        form_layout.addRow('Имя*:', self.name_edit)
        
        self.middle_edit = QLineEdit()
        self.middle_edit.setPlaceholderText('Иванович (необязательно)')
        form_layout.addRow('Отчество:', self.middle_edit)
        
        self.add_student_btn = QPushButton('Добавить студента')
        self.add_student_btn.clicked.connect(self.add_student)
        form_layout.addRow(self.add_student_btn)
        
        layout.addWidget(form_frame)
        
        # Кнопка закрытия
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
    
    def load_students(self):
        """Загрузка студентов текущей группы"""
        self.cursor.execute('''
            SELECT s.id, s.surname, s.name, s.middle_name, g.name 
            FROM students s
            LEFT JOIN groups g ON s.group_id = g.id
            WHERE s.group_id = ?
            ORDER BY s.surname, s.name
        ''', (self.group_id,))
        
        students = self.cursor.fetchall()
        self.students_table.setRowCount(len(students))
        
        for row_idx, (student_id, surname, name, middle_name, group_name) in enumerate(students):
            self.students_table.setItem(row_idx, 0, QTableWidgetItem(surname))
            self.students_table.setItem(row_idx, 1, QTableWidgetItem(name))
            self.students_table.setItem(row_idx, 2, QTableWidgetItem(middle_name if middle_name else ''))
            self.students_table.setItem(row_idx, 3, QTableWidgetItem(group_name))
            
            # Кнопка исключения студента
            delete_btn = QPushButton('Исключить')
            delete_btn.clicked.connect(lambda _, sid=student_id: self.delete_student(sid))
            
            # Кнопка перевода в другую группу
            transfer_btn = QPushButton('Перевести')
            transfer_btn.clicked.connect(lambda _, sid=student_id: self.transfer_student(sid))
            
            # Контейнер для кнопок
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.addWidget(delete_btn)
            btn_layout.addWidget(transfer_btn)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            
            self.students_table.setCellWidget(row_idx, 4, btn_container)
    
    def load_all_groups(self):
        """Загрузка всех групп для перевода студентов"""
        self.cursor.execute("SELECT id, name FROM groups WHERE id != ? ORDER BY name", (self.group_id,))
        self.all_groups = self.cursor.fetchall()
    
    def add_student(self):
        """Добавление нового студента в группу"""
        surname = self.surname_edit.text().strip()
        name = self.name_edit.text().strip()
        middle = self.middle_edit.text().strip() or None
        
        if not surname or not name:
            QMessageBox.warning(self, 'Ошибка', 'Заполните обязательные поля (Фамилия и Имя)')
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO students (surname, name, middle_name, group_id) VALUES (?, ?, ?, ?)",
                (surname, name, middle, self.group_id)
            )
            self.conn.commit()
            
            self.surname_edit.clear()
            self.name_edit.clear()
            self.middle_edit.clear()
            self.load_students()
            
            QMessageBox.information(self, 'Успех', 'Студент добавлен в группу')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить студента: {str(e)}')
    
    def delete_student(self, student_id):
        """Исключение студента из группы"""
        self.cursor.execute("SELECT surname, name FROM students WHERE id = ?", (student_id,))
        student = self.cursor.fetchone()
        
        if not student:
            QMessageBox.warning(self, 'Ошибка', 'Студент не найден')
            return
            
        surname, name = student
        
        reply = QMessageBox.question(
            self, 'Подтверждение', 
            f'Исключить студента {surname} {name} из группы?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        
        try:
            self.cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            self.conn.commit()
            self.load_students()
            QMessageBox.information(self, 'Успех', 'Студент исключен из группы')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось исключить студента: {str(e)}')
    
    def transfer_student(self, student_id):
        """Перевод студента в другую группу"""
        self.cursor.execute("SELECT surname, name FROM students WHERE id = ?", (student_id,))
        student = self.cursor.fetchone()
        
        if not student:
            QMessageBox.warning(self, 'Ошибка', 'Студент не найден')
            return
        
        surname, name = student
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f'Перевод студента {surname} {name}')
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel('Выберите новую группу:'))
        
        group_combo = QComboBox()
        for group_id, group_name in self.all_groups:
            group_combo.addItem(group_name, group_id)
        layout.addWidget(group_combo)
        
        btn_box = QHBoxLayout()
        transfer_btn = QPushButton('Перевести')
        transfer_btn.clicked.connect(lambda: self.do_transfer(student_id, group_combo.currentData()))
        transfer_btn.clicked.connect(dialog.accept)
        btn_box.addWidget(transfer_btn)
        
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(dialog.reject)
        btn_box.addWidget(cancel_btn)
        
        layout.addLayout(btn_box)
        
        if dialog.exec_() == QDialog.Accepted:
            self.load_students()  # Обновляем список студентов
    
    def do_transfer(self, student_id, new_group_id):
        """Выполнение перевода студента в другую группу"""
        try:
            self.cursor.execute(
                "UPDATE students SET group_id = ? WHERE id = ?",
                (new_group_id, student_id)
            )
            self.conn.commit()
            QMessageBox.information(self, 'Успех', 'Студент переведен в другую группу')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось перевести студента: {str(e)}')
    
    def set_style(self):
        self.setStyleSheet('''
            QDialog {
                background-color: #f5f5f5;
                font-size: 16px;
            }
            QLabel {
                color: #333333;
                font-size: 16px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 16px;
                min-width: 120px;
                background-color: #2196F3;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a68b4;
            }
            QTableWidget {
                border: 1px solid #dddddd;
                font-size: 16px;
                gridline-color: #dddddd;
                selection-background-color: #2196F3;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 12px;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                padding: 10px;
                border: 1px solid #dddddd;
                border-radius: 5px;
                font-size: 16px;
                min-width: 200px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #2196F3;
            }
        ''')

class AdminScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Университетские группы')
        self.setGeometry(100, 100, 1100, 800)
        self.setMinimumSize(1000, 700)
        
        # Подключение к базе данных
        self.conn = sqlite3.connect('university.db')
        self.cursor = self.conn.cursor()
        self.init_db()
        
        # Основной интерфейс
        self.init_ui()
        self.set_style()
        
    def init_db(self):
        """Инициализация базы данных"""
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course INTEGER NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surname TEXT NOT NULL,
                name TEXT NOT NULL,
                middle_name TEXT,
                group_id INTEGER,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL
            )
        ''')
        self.conn.commit()
    
    def init_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Форма добавления группы
        add_group_frame = QFrame()
        add_group_frame.setFrameShape(QFrame.StyledPanel)
        add_group_layout = QVBoxLayout(add_group_frame)
        add_group_layout.setSpacing(15)
        
        form_title = QLabel('Добавить новую группу')
        form_title.setFont(QFont('Arial', 14, QFont.Bold))
        add_group_layout.addWidget(form_title)
        
        form_layout = QHBoxLayout()
        form_layout.setSpacing(20)
        
        # Поля ввода
        name_layout = QVBoxLayout()
        name_layout.setSpacing(5)
        name_label = QLabel('Название группы:')
        name_layout.addWidget(name_label)
        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText('Например: ИВТ-21')
        name_layout.addWidget(self.group_name_input)
        
        course_layout = QVBoxLayout()
        course_layout.setSpacing(5)
        course_label = QLabel('Курс (1-4):')
        course_layout.addWidget(course_label)
        self.group_course_input = QLineEdit()
        self.group_course_input.setValidator(QIntValidator(1, 4))
        self.group_course_input.setPlaceholderText('Введите курс (1-4)')
        course_layout.addWidget(self.group_course_input)
        
        form_layout.addLayout(name_layout)
        form_layout.addLayout(course_layout)
        
        # Кнопка добавления
        self.add_group_btn = QPushButton('Добавить группу')
        self.add_group_btn.clicked.connect(self.add_group)
        form_layout.addWidget(self.add_group_btn)
        
        add_group_layout.addLayout(form_layout)
        layout.addWidget(add_group_frame)
        
        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Таблица групп
        self.init_groups_table()
        layout.addWidget(self.groups_table)
        
        # Кнопка удаления группы
        self.delete_group_btn = QPushButton('Удалить выбранную группу')
        self.delete_group_btn.clicked.connect(self.delete_group)
        layout.addWidget(self.delete_group_btn, alignment=Qt.AlignRight)
        
        # Загрузка данных
        self.load_groups()
    
    def init_groups_table(self):
        """Инициализация таблицы групп"""
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(5)
        self.groups_table.setHorizontalHeaderLabels(['ID', 'Название', 'Курс', 'Студентов', 'Действия'])
        self.groups_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.groups_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.groups_table.verticalHeader().setVisible(False)
        self.groups_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.groups_table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    def load_groups(self):
        """Загрузка списка групп из базы данных"""
        self.cursor.execute('''
            SELECT g.id, g.name, g.course, COUNT(s.id) 
            FROM groups g
            LEFT JOIN students s ON g.id = s.group_id
            GROUP BY g.id
            ORDER BY g.course, g.name
        ''')
        groups = self.cursor.fetchall()
        
        self.groups_table.setRowCount(len(groups))
        
        for row_idx, (group_id, name, course, student_count) in enumerate(groups):
            self.groups_table.setItem(row_idx, 0, QTableWidgetItem(str(group_id)))
            self.groups_table.setItem(row_idx, 1, QTableWidgetItem(name))
            self.groups_table.setItem(row_idx, 2, QTableWidgetItem(str(course)))
            self.groups_table.setItem(row_idx, 3, QTableWidgetItem(str(student_count)))
            
            # Кнопка открытия управления студентами
            open_btn = QPushButton('Открыть')
            open_btn.clicked.connect(lambda _, gid=group_id, gname=name: self.open_student_management(gid, gname))
            self.groups_table.setCellWidget(row_idx, 4, open_btn)
    
    def open_student_management(self, group_id, group_name):
        """Открытие окна управления студентами группы"""
        dialog = StudentManagementWindow(group_id, group_name, self.conn)
        dialog.exec_()
        self.load_groups()  # Обновляем данные после закрытия диалога
    
    def add_group(self):
        """Добавление новой группы"""
        name = self.group_name_input.text().strip()
        course = self.group_course_input.text().strip()
        
        if not name or not course:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO groups (name, course) VALUES (?, ?)", 
                (name, int(course))
            )
            self.conn.commit()
            
            self.group_name_input.clear()
            self.group_course_input.clear()
            self.load_groups()
            
            QMessageBox.information(self, 'Успех', 'Группа добавлена')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить группу: {str(e)}')
    
    def delete_group(self):
        """Удаление выбранной группы"""
        selected = self.groups_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, 'Ошибка', 'Выберите группу для удаления')
            return
        
        row = selected[0].row()
        group_id = int(self.groups_table.item(row, 0).text())
        group_name = self.groups_table.item(row, 1).text()
        
        # Проверяем, есть ли студенты в группе
        self.cursor.execute("SELECT COUNT(*) FROM students WHERE group_id = ?", (group_id,))
        student_count = self.cursor.fetchone()[0]
        
        if student_count > 0:
            reply = QMessageBox.question(
                self, 'Подтверждение', 
                f'В группе {group_name} есть {student_count} студентов. Удалить группу?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        try:
            self.cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            self.conn.commit()
            self.load_groups()
            QMessageBox.information(self, 'Успех', 'Группа удалена')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить группу: {str(e)}')
    
    def set_style(self):
        self.setStyleSheet('''
            QWidget {
                background-color: #f5f5f5;
                font-size: 16px;
            }
            QLabel {
                color: #333333;
                font-size: 16px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 16px;
                min-width: 120px;
                background-color: #2196F3;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a68b4;
            }
            QTableWidget {
                border: 1px solid #dddddd;
                font-size: 16px;
                gridline-color: #dddddd;
                selection-background-color: #2196F3;
                selection-color: white;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 12px;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                padding: 10px;
                border: 1px solid #dddddd;
                border-radius: 5px;
                font-size: 16px;
                min-width: 200px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #2196F3;
            }
            QFrame {
                border: none;
            }
        ''')
    
    def closeEvent(self, event):
        """Закрытие соединения с БД при выходе"""
        self.conn.close()
        event.accept()

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = AdminScreen()
    window.show()
    sys.exit(app.exec_())
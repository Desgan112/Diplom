import sqlite3
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QMessageBox, 
                            QVBoxLayout, QHBoxLayout, QLineEdit,
                            QTableWidget, QTableWidgetItem, QDialog, 
                            QFrame, QHeaderView, QFormLayout,
                            QComboBox, QCheckBox, QTabWidget)
from PyQt5.QtGui import QFont, QIntValidator
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
        self.students_table.setColumnCount(6)
        self.students_table.setHorizontalHeaderLabels(['Фамилия', 'Имя', 'Отчество', 'Группа', 'Приезжий', 'Действия'])
        self.students_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.students_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.students_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.students_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.students_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.students_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
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
        
        # Чекбокс для отметки "Приезжий"
        self.nonresident_checkbox = QCheckBox('Приезжий')
        form_layout.addRow('', self.nonresident_checkbox)
        font = self.nonresident_checkbox.font()
        font.setPointSize(10)  # Размер шрифта 12
        self.nonresident_checkbox.setFont(font)
        
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
        try:
            self.cursor.execute('''
                SELECT s.id, s.surname, s.name, s.middle_name, g.name, s.is_nonresident 
                FROM students s
                LEFT JOIN groups g ON s.group_id = g.id
                WHERE s.group_id = ?
                ORDER BY s.surname, s.name
            ''', (self.group_id,))
            
            students = self.cursor.fetchall()
            self.students_table.setRowCount(len(students))
            
            for row_idx, (student_id, surname, name, middle_name, group_name, is_nonresident) in enumerate(students):
                self.students_table.setItem(row_idx, 0, QTableWidgetItem(surname))
                self.students_table.setItem(row_idx, 1, QTableWidgetItem(name))
                self.students_table.setItem(row_idx, 2, QTableWidgetItem(middle_name if middle_name else ''))
                self.students_table.setItem(row_idx, 3, QTableWidgetItem(group_name))
                
                # Чекбокс для статуса "Приезжий"
                nonresident_check = QCheckBox()
                nonresident_check.setChecked(bool(is_nonresident))
                nonresident_check.stateChanged.connect(lambda state, sid=student_id: self.update_nonresident_status(sid, state))
                cell_widget = QWidget()
                layout = QHBoxLayout(cell_widget)
                layout.addWidget(nonresident_check)
                layout.setAlignment(Qt.AlignCenter)
                layout.setContentsMargins(0, 0, 0, 0)
                self.students_table.setCellWidget(row_idx, 4, cell_widget)
                
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
                btn_layout.setSpacing(5)
                
                self.students_table.setCellWidget(row_idx, 5, btn_container)
                self.students_table.setRowHeight(row_idx, 50)
        except sqlite3.OperationalError as e:
            if "no such column: s.is_nonresident" in str(e):
                self.cursor.execute("ALTER TABLE students ADD COLUMN is_nonresident BOOLEAN DEFAULT 0")
                self.conn.commit()
                self.load_students()
            else:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка базы данных: {str(e)}')
    
    def update_nonresident_status(self, student_id, state):
        """Обновление статуса 'Приезжий' для студента"""
        is_nonresident = state == Qt.Checked
        try:
            self.cursor.execute(
                "UPDATE students SET is_nonresident = ? WHERE id = ?",
                (is_nonresident, student_id)
            )
            self.conn.commit()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось обновить статус: {str(e)}')
    
    def load_all_groups(self):
        """Загрузка всех групп для перевода студентов"""
        self.cursor.execute("SELECT id, name FROM groups WHERE id != ? ORDER BY name", (self.group_id,))
        self.all_groups = self.cursor.fetchall()
    
    def add_student(self):
        surname = self.surname_edit.text().strip()
        name = self.name_edit.text().strip()
        middle = self.middle_edit.text().strip() or None
        is_nonresident = self.nonresident_checkbox.isChecked()
        
        if not surname or not name:
            QMessageBox.warning(self, 'Ошибка', 'Заполните обязательные поля (Фамилия и Имя)')
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO students (surname, name, middle_name, group_id, is_nonresident) VALUES (?, ?, ?, ?, ?)",
                (surname, name, middle, self.group_id, is_nonresident)
            )
            self.conn.commit()
            self.surname_edit.clear()
            self.name_edit.clear()
            self.middle_edit.clear()
            self.nonresident_checkbox.setChecked(False)
            self.load_students()
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
            self.load_students()
    
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
                padding: 8px 16px;
                border-radius: 2px;
                font-size: 16px;
                min-width: 100px;
                background-color: #2196F3;
                color: white;
                border: 1px solid #0b7dda;
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
                selection-background-color: transparent;
                selection-color: #333333;
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
                border-radius: 2px;
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

class AdminScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Окно администратора')
        self.setGeometry(100, 100, 1100, 800)
        self.setMinimumSize(1000, 700)
        
        self.conn = sqlite3.connect('university.db')
        self.cursor = self.conn.cursor()
        self.init_db()
        
        self.init_ui()
        self.set_style()
        
    def init_db(self):
        self.cursor.execute("PRAGMA foreign_keys = ON")
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                course INTEGER DEFAULT 1
            )
        ''')
        
        self.cursor.execute("PRAGMA table_info(groups)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'course' not in columns:
            try:
                self.cursor.execute("ALTER TABLE groups ADD COLUMN course INTEGER DEFAULT 1")
            except sqlite3.OperationalError:
                pass
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surname TEXT NOT NULL,
                name TEXT NOT NULL,
                middle_name TEXT,
                group_id INTEGER,
                is_nonresident BOOLEAN DEFAULT 0,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL
            )
        ''')
        
        self.cursor.execute("PRAGMA table_info(students)")
        columns = [column[1] for column in self.cursor.fetchall()]
        
        if 'middle_name' not in columns:
            try:
                self.cursor.execute("ALTER TABLE students ADD COLUMN middle_name TEXT")
            except sqlite3.OperationalError:
                pass
        
        if 'is_nonresident' not in columns:
            try:
                self.cursor.execute("ALTER TABLE students ADD COLUMN is_nonresident BOOLEAN DEFAULT 0")
            except sqlite3.OperationalError:
                pass
        
        self.conn.commit()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаем вкладки
        self.tabs = QTabWidget()
        
        # Первая вкладка - Группы
        groups_tab = QWidget()
        groups_layout = QVBoxLayout(groups_tab)
        groups_layout.setContentsMargins(25, 25, 25, 25)
        groups_layout.setSpacing(20)
        
        add_group_frame = QFrame()
        add_group_frame.setFrameShape(QFrame.StyledPanel)
        add_group_layout = QVBoxLayout(add_group_frame)
        add_group_layout.setSpacing(15)
        
        form_title = QLabel('Добавить новую группу')
        form_title.setFont(QFont('Arial', 14, QFont.Bold))
        add_group_layout.addWidget(form_title)
        
        form_layout = QHBoxLayout()
        form_layout.setSpacing(20)
        
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
        
        self.add_group_btn = QPushButton('Добавить группу')
        self.add_group_btn.clicked.connect(self.add_group)
        form_layout.addWidget(self.add_group_btn)
        
        add_group_layout.addLayout(form_layout)
        groups_layout.addWidget(add_group_frame)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        groups_layout.addWidget(separator)
        
        self.init_groups_table()
        groups_layout.addWidget(self.groups_table)
        
        groups_layout.addSpacing(20)
        
        self.delete_group_btn = QPushButton('Удалить выбранную группу')
        self.delete_group_btn.clicked.connect(self.delete_group)
        groups_layout.addWidget(self.delete_group_btn, alignment=Qt.AlignRight)
        
        # Вторая вкладка - Предметы
        subjects_tab = SubjectsTab(self.conn)
        
        # Добавляем вкладки
        self.tabs.addTab(groups_tab, "Группы")
        self.tabs.addTab(subjects_tab, "Предметы")
        
        layout.addWidget(self.tabs)
        
        self.load_groups()
    
    def init_groups_table(self):
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(5)
        self.groups_table.setHorizontalHeaderLabels(['ID', 'Название', 'Курс', 'Кол-во студентов', ' '])
        self.groups_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.groups_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.groups_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.groups_table.verticalHeader().setVisible(False)
        self.groups_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.groups_table.setEditTriggers(QTableWidget.NoEditTriggers)
    
    def load_groups(self):
        try:
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
                open_btn = QPushButton('Открыть')
                open_btn.clicked.connect(lambda _, gid=group_id, gname=name: self.open_student_management(gid, gname))
                self.groups_table.setCellWidget(row_idx, 4, open_btn)
        except sqlite3.OperationalError as e:
            if "no such column: g.course" in str(e):
                self.cursor.execute('''
                    SELECT g.id, g.name, 1 as course, COUNT(s.id) 
                    FROM groups g
                    LEFT JOIN students s ON g.id = s.group_id
                    GROUP BY g.id
                    ORDER BY g.name
                ''')
                groups = self.cursor.fetchall()
                self.groups_table.setRowCount(len(groups))
                for row_idx, (group_id, name, course, student_count) in enumerate(groups):
                    self.groups_table.setItem(row_idx, 0, QTableWidgetItem(str(group_id)))
                    self.groups_table.setItem(row_idx, 1, QTableWidgetItem(name))
                    self.groups_table.setItem(row_idx, 2, QTableWidgetItem(str(course)))
                    self.groups_table.setItem(row_idx, 3, QTableWidgetItem(str(student_count)))
                    open_btn = QPushButton('Открыть')
                    open_btn.clicked.connect(lambda _, gid=group_id, gname=name: self.open_student_management(gid, gname))
                    self.groups_table.setCellWidget(row_idx, 4, open_btn)
            else:
                QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке групп: {str(e)}')
    
    def open_student_management(self, group_id, group_name):
        dialog = StudentManagementWindow(group_id, group_name, self.conn)
        dialog.exec_()
        self.load_groups()
    
    def add_group(self):
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
        selected = self.groups_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, 'Ошибка', 'Выберите группу для удаления')
            return
        row = selected[0].row()
        group_id = int(self.groups_table.item(row, 0).text())
        group_name = self.groups_table.item(row, 1).text()
        self.cursor.execute("SELECT COUNT(*) FROM students WHERE group_id = ?", (group_id,))
        student_count = self.cursor.fetchone()[0]
        if student_count > 0:
            # Создаем кастомный MessageBox с русскими кнопками
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Подтверждение')
            msg_box.setText(f'В группе {group_name} есть {student_count} студентов. Что вы хотите сделать?')
            msg_box.setIcon(QMessageBox.Question)
            delete_all_btn = msg_box.addButton('Удалить всех', QMessageBox.YesRole)
            transfer_btn = msg_box.addButton('Перевести', QMessageBox.NoRole)
            cancel_btn = msg_box.addButton('Отмена', QMessageBox.RejectRole)
            msg_box.setDefaultButton(cancel_btn)
            msg_box.setEscapeButton(cancel_btn)
            msg_box.exec_()
            if msg_box.clickedButton() == delete_all_btn:
                try:
                    self.cursor.execute("DELETE FROM students WHERE group_id = ?", (group_id,))
                    self.cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
                    self.conn.commit()
                    self.load_groups()
                    QMessageBox.information(self, 'Успех', 'Группа и все ее студенты удалены')
                    return
                except Exception as e:
                    self.conn.rollback()
                    QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить группу: {str(e)}')
                    return
            elif msg_box.clickedButton() == transfer_btn:
                self.transfer_students_before_delete(group_id, group_name)
                return
            else:
                return
        # Если студентов нет, просто удаляем группу
        try:
            self.cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            self.conn.commit()
            self.load_groups()
            QMessageBox.information(self, 'Успех', 'Группа удалена')
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить группу: {str(e)}')

    def transfer_students_before_delete(self, group_id, group_name):
        """Перевод студентов в другую группу перед удалением"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f'Перевод студентов из группы {group_name}')
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel('Выберите новую группу для студентов:'))
        self.cursor.execute("SELECT id, name FROM groups WHERE id != ? ORDER BY name", (group_id,))
        groups = self.cursor.fetchall()
        if not groups:
            QMessageBox.warning(self, 'Ошибка', 'Нет других групп для перевода студентов')
            return
        group_combo = QComboBox()
        for g_id, g_name in groups:
            group_combo.addItem(g_name, g_id)
        layout.addWidget(group_combo)
        btn_box = QHBoxLayout()
        transfer_btn = QPushButton('Перевести и удалить')
        transfer_btn.clicked.connect(lambda: self.do_transfer_and_delete(group_id, group_combo.currentData(), dialog))
        transfer_btn.clicked.connect(dialog.accept)
        btn_box.addWidget(transfer_btn)
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(dialog.reject)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)
        dialog.exec_()

    def do_transfer_and_delete(self, old_group_id, new_group_id, dialog):
        """Выполнение перевода студентов и удаления группы"""
        try:
            self.cursor.execute(
                "UPDATE students SET group_id = ? WHERE group_id = ?",
                (new_group_id, old_group_id)
            )
            self.cursor.execute("DELETE FROM groups WHERE id = ?", (old_group_id,))
            self.conn.commit()
            dialog.accept()
            self.load_groups()
            QMessageBox.information(self, 'Успех', 'Студенты переведены и группа удалена')
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Не удалось выполнить операцию: {str(e)}')
    
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
                padding: 8px 16px;
                border-radius: 2px;
                font-size: 16px;
                min-width: 100px;
                background-color: #2196F3;
                color: white;
                border: 1px solid #0b7dda;
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
                selection-background-color: transparent;
                selection-color: #333333;
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
                border-radius: 2px;
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
        self.conn.close()
        event.accept()

class SubjectsTab(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.init_ui()
        self.init_db()
        self.load_subjects()
        self.set_style()
    
    def init_db(self):
        """Инициализация таблицы предметов"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        ''')
        self.conn.commit()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Форма добавления предмета
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.StyledPanel)
        form_layout = QFormLayout(form_frame)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setSpacing(15)
        
        title = QLabel('Добавить новый предмет')
        title.setFont(QFont('Arial', 14, QFont.Bold))
        form_layout.addRow(title)
        
        self.subject_name = QLineEdit()
        self.subject_name.setPlaceholderText('Название предмета')
        form_layout.addRow('Название*:', self.subject_name)
        
        # Убрано поле "Часы"
        # self.subject_hours = QLineEdit()
        # self.subject_hours.setPlaceholderText('Количество часов')
        # self.subject_hours.setValidator(QIntValidator(1, 999))
        # form_layout.addRow('Часы*:', self.subject_hours)
        
        self.subject_desc = QLineEdit()
        self.subject_desc.setPlaceholderText('Описание (необязательно)')
        form_layout.addRow('Описание:', self.subject_desc)
        
        self.add_subject_btn = QPushButton('Добавить предмет')
        self.add_subject_btn.clicked.connect(self.add_subject)
        form_layout.addRow(self.add_subject_btn)
        
        layout.addWidget(form_frame)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Таблица предметов
        self.subjects_table = QTableWidget()
        self.subjects_table.setColumnCount(4)
        self.subjects_table.setHorizontalHeaderLabels(['ID', 'Название', 'Описание', 'Действия'])
        self.subjects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.subjects_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.subjects_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.subjects_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.subjects_table.verticalHeader().setVisible(False)
        layout.addWidget(self.subjects_table)
    
    def load_subjects(self):
        """Загрузка списка предметов из базы данных"""
        try:
            self.cursor.execute('''
                SELECT id, name, description FROM subjects ORDER BY name
            ''')
            subjects = self.cursor.fetchall()
            self.subjects_table.setRowCount(len(subjects))
            for row_idx, (subject_id, name, description) in enumerate(subjects):
                self.subjects_table.setItem(row_idx, 0, QTableWidgetItem(str(subject_id)))
                self.subjects_table.setItem(row_idx, 1, QTableWidgetItem(name))
                self.subjects_table.setItem(row_idx, 2, QTableWidgetItem(description))
                # Кнопки действий
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(0, 0, 0, 0)
                btn_layout.setSpacing(5)
                edit_btn = QPushButton('Изменить')
                edit_btn.clicked.connect(lambda _, sid=subject_id: self.edit_subject(sid))
                delete_btn = QPushButton('Удалить')
                delete_btn.clicked.connect(lambda _, sid=subject_id: self.delete_subject(sid))
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                self.subjects_table.setCellWidget(row_idx, 3, btn_container)
                self.subjects_table.setRowHeight(row_idx, 50)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось загрузить предметы: {str(e)}')
    
    def add_subject(self):
        """Добавление нового предмета"""
        name = self.subject_name.text().strip()
        description = self.subject_desc.text().strip() or None
        if not name:
            QMessageBox.warning(self, 'Ошибка', 'Заполните обязательные поля (Название)')
            return
        try:
            self.cursor.execute(
                "INSERT INTO subjects (name, description) VALUES (?, ?)",
                (name, description)
            )
            self.conn.commit()
            self.subject_name.clear()
            self.subject_desc.clear()
            self.load_subjects()
            QMessageBox.information(self, 'Успех', 'Предмет успешно добавлен')
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, 'Ошибка', 'Предмет с таким названием уже существует')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось добавить предмет: {str(e)}')
    
    def edit_subject(self, subject_id):
        """Редактирование предмета"""
        self.cursor.execute('''
            SELECT name, description FROM subjects WHERE id = ?
        ''', (subject_id,))
        subject = self.cursor.fetchone()
        if not subject:
            QMessageBox.warning(self, 'Ошибка', 'Предмет не найден')
            return
        name, description = subject
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактирование предмета')
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        form_layout = QFormLayout()
        name_edit = QLineEdit(name)
        form_layout.addRow('Название:', name_edit)
        # Убрано поле "Часы"
        # hours_edit = QLineEdit(str(hours))
        # hours_edit.setValidator(QIntValidator(1, 999))
        # form_layout.addRow('Часы:', hours_edit)
        desc_edit = QLineEdit(description if description else '')
        form_layout.addRow('Описание:', desc_edit)
        layout.addLayout(form_layout)
        btn_box = QHBoxLayout()
        save_btn = QPushButton('Сохранить')
        save_btn.clicked.connect(lambda: self.save_subject_changes(
            subject_id, name_edit.text().strip(), 
            desc_edit.text().strip() or None, dialog))
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(dialog.reject)
        btn_box.addWidget(save_btn)
        btn_box.addWidget(cancel_btn)
        layout.addLayout(btn_box)
        dialog.exec_()
    
    def save_subject_changes(self, subject_id, name, description, dialog):
        """Сохранение изменений предмета"""
        if not name:
            QMessageBox.warning(self, 'Ошибка', 'Заполните обязательные поля (Название)')
            return
        try:
            self.cursor.execute('''
                UPDATE subjects SET name = ?, description = ? WHERE id = ?
            ''', (name, description, subject_id))
            self.conn.commit()
            dialog.accept()
            self.load_subjects()
            QMessageBox.information(self, 'Успех', 'Изменения сохранены')
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, 'Ошибка', 'Предмет с таким названием уже существует')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить изменения: {str(e)}')
    
    def delete_subject(self, subject_id):
        """Удаление предмета"""
        self.cursor.execute('SELECT name FROM subjects WHERE id = ?', (subject_id,))
        subject = self.cursor.fetchone()
        if not subject:
            QMessageBox.warning(self, 'Ошибка', 'Предмет не найден')
            return
        reply = QMessageBox.question(
            self, 'Подтверждение', 
            f'Удалить предмет "{subject[0]}"?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        try:
            self.cursor.execute('DELETE FROM subjects WHERE id = ?', (subject_id,))
            self.conn.commit()
            self.load_subjects()
            QMessageBox.information(self, 'Успех', 'Предмет удален')
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить предмет: {str(e)}')
    
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
                padding: 8px 16px;
                border-radius: 2px;
                font-size: 16px;
                min-width: 100px;
                background-color: #2196F3;
                color: white;
                border: 1px solid #0b7dda;
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
                selection-background-color: transparent;
                selection-color: #333333;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 12px;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #dddddd;
                border-radius: 2px;
                font-size: 16px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
            QFrame {
                border: none;
            }
        ''')

# Остальной код остался без изменений
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = AdminScreen()
    window.show()
    sys.exit(app.exec_())
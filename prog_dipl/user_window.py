import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QMessageBox, QTabWidget,
    QVBoxLayout, QTableWidget, QTableWidgetItem,
    QDateEdit, QComboBox, QHBoxLayout, QHeaderView,
    QRadioButton, QButtonGroup, QApplication, QFrame, QSpinBox
)
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QDate

class UserWindow(QWidget):
    def __init__(self, db_path='university.db'):
        super().__init__()
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

        self.setWindowTitle('Система учета посещаемости (многопарная)')
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1400, 800)

        self.init_ui()
        self.set_style()

    def create_tables(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    surname TEXT NOT NULL,
                    name TEXT NOT NULL,
                    group_id INTEGER,
                    is_nonresident BOOLEAN DEFAULT 0,
                    FOREIGN KEY (group_id) REFERENCES groups(id)
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    lesson_number INTEGER NOT NULL,
                    subject_id INTEGER,
                    status TEXT NOT NULL CHECK(status IN ('present', 'late', 'sick', 'absent')),
                    UNIQUE(student_id, date, lesson_number)
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при создании таблиц: {str(e)}')

    def init_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont('Segoe UI', 12))
        
        self.attendance_tab = QWidget()
        self.init_attendance_tab()
        self.stats_tab = QWidget()
        self.init_stats_tab()

        self.tabs.addTab(self.attendance_tab, "Учет посещаемости")
        self.tabs.addTab(self.stats_tab, "Статистика")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.addWidget(self.tabs)

        self.load_groups()
        self.load_subjects()
        self.load_attendance_data()
        self.load_statistics()

    def init_attendance_tab(self):
        layout = QVBoxLayout(self.attendance_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 10)
        title_layout.setSpacing(15)

        self.title = QLabel('Учет посещаемости (по парам)')
        self.title.setFont(QFont('Arial', 16, QFont.Bold))
        title_layout.addWidget(self.title, 1)

        layout.addLayout(title_layout)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)
        separator.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(separator)

        # Панель фильтров
        filter_panel = QFrame()
        filter_panel.setObjectName('filterPanel')
        filter_layout = QHBoxLayout(filter_panel)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(20)

        # Фильтр по дате
        date_filter = QFrame()
        date_filter.setObjectName('dateFilter')
        date_layout = QVBoxLayout(date_filter)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(5)

        date_label = QLabel('Дата:')
        date_label.setFont(QFont('Segoe UI', 11))
        date_layout.addWidget(date_label)

        self.filter_date = QDateEdit()
        self.filter_date.setDate(QDate.currentDate())
        self.filter_date.setCalendarPopup(True)
        self.filter_date.setDisplayFormat("dd.MM.yyyy")
        self.filter_date.setFixedHeight(40)
        self.filter_date.setFixedWidth(150)
        self.filter_date.setFont(QFont('Segoe UI', 11))
        self.filter_date.dateChanged.connect(self.load_attendance_data)
        date_layout.addWidget(self.filter_date)

        filter_layout.addWidget(date_filter)

        # Номер пары
        lesson_filter = QFrame()
        lesson_filter.setObjectName('lessonFilter')
        lesson_layout = QVBoxLayout(lesson_filter)
        lesson_layout.setContentsMargins(0, 0, 0, 0)
        lesson_layout.setSpacing(5)

        lesson_label = QLabel('Номер пары:')
        lesson_label.setFont(QFont('Segoe UI', 11))
        lesson_layout.addWidget(lesson_label)

        self.lesson_number = QSpinBox()
        self.lesson_number.setRange(1, 4)
        self.lesson_number.setValue(1)
        self.lesson_number.setFixedHeight(40)
        self.lesson_number.setFixedWidth(100)
        self.lesson_number.setFont(QFont('Segoe UI', 11))
        self.lesson_number.valueChanged.connect(self.load_attendance_data)
        lesson_layout.addWidget(self.lesson_number)

        filter_layout.addWidget(lesson_filter)

        # Предмет
        subject_filter = QFrame()
        subject_filter.setObjectName('subjectFilter')
        subject_layout = QVBoxLayout(subject_filter)
        subject_layout.setContentsMargins(0, 0, 0, 0)
        subject_layout.setSpacing(5)

        subject_label = QLabel('Предмет:')
        subject_label.setFont(QFont('Segoe UI', 11))
        subject_layout.addWidget(subject_label)

        self.subject_combo = QComboBox()
        self.subject_combo.setFixedHeight(40)
        self.subject_combo.setFixedWidth(200)
        self.subject_combo.setFont(QFont('Segoe UI', 11))
        self.subject_combo.currentIndexChanged.connect(self.load_attendance_data)
        subject_layout.addWidget(self.subject_combo)

        filter_layout.addWidget(subject_filter)

        # Группа
        group_filter = QFrame()
        group_filter.setObjectName('groupFilter')
        group_layout = QVBoxLayout(group_filter)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)

        group_label = QLabel('Группа:')
        group_label.setFont(QFont('Segoe UI', 11))
        group_layout.addWidget(group_label)

        self.filter_group = QComboBox()
        self.filter_group.setFixedHeight(40)
        self.filter_group.setFixedWidth(200)
        self.filter_group.setFont(QFont('Segoe UI', 11))
        self.filter_group.currentIndexChanged.connect(self.load_attendance_data)
        group_layout.addWidget(self.filter_group)

        filter_layout.addWidget(group_filter)

        # Кнопка
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)

        self.save_btn = QPushButton('Сохранить')
        self.save_btn.setIcon(QIcon.fromTheme('document-save'))
        self.save_btn.setFixedHeight(45)
        self.save_btn.setFixedWidth(150)
        self.save_btn.setFont(QFont('Segoe UI', 12))
        self.save_btn.clicked.connect(self.save_attendance)
        button_layout.addWidget(self.save_btn)

        filter_layout.addLayout(button_layout)

        layout.addWidget(filter_panel)

        # Таблица посещаемости
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(6)
        self.attendance_table.setHorizontalHeaderLabels(['ID', 'Фамилия', 'Имя', 'Группа', 'Предмет', 'Статус'])
        self.attendance_table.setColumnHidden(0, True)
        self.attendance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.attendance_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.attendance_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.attendance_table.verticalHeader().setVisible(False)
        self.attendance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.attendance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.attendance_table.setFont(QFont('Segoe UI', 11))
        self.attendance_table.setAlternatingRowColors(True)
        layout.addWidget(self.attendance_table, 1)

        # Статус бар
        self.status_bar = QLabel()
        self.status_bar.setFont(QFont('Segoe UI', 10))
        self.status_bar.setAlignment(Qt.AlignRight)
        layout.addWidget(self.status_bar)

    def init_stats_tab(self):
        layout = QVBoxLayout(self.stats_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel('Статистика посещаемости (по парам)')
        title.setFont(QFont('Segoe UI', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Фильтры
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)

        # Дата начала
        start_date_box = QVBoxLayout()
        start_date_label = QLabel('Дата начала:')
        start_date_label.setFont(QFont('Segoe UI', 10))
        start_date_box.addWidget(start_date_label)
        self.stats_start_date = QDateEdit()
        self.stats_start_date.setDate(QDate.currentDate().addDays(-7))
        self.stats_start_date.setCalendarPopup(True)
        self.stats_start_date.setDisplayFormat("dd.MM.yyyy")
        self.stats_start_date.setFixedHeight(40)
        self.stats_start_date.setFixedWidth(150)
        self.stats_start_date.setFont(QFont('Segoe UI', 10))
        self.stats_start_date.dateChanged.connect(self.load_statistics)
        start_date_box.addWidget(self.stats_start_date)
        filter_layout.addLayout(start_date_box)

        # Дата конца
        end_date_box = QVBoxLayout()
        end_date_label = QLabel('Дата окончания:')
        end_date_label.setFont(QFont('Segoe UI', 10))
        end_date_box.addWidget(end_date_label)
        self.stats_end_date = QDateEdit()
        self.stats_end_date.setDate(QDate.currentDate())
        self.stats_end_date.setCalendarPopup(True)
        self.stats_end_date.setDisplayFormat("dd.MM.yyyy")
        self.stats_end_date.setFixedHeight(40)
        self.stats_end_date.setFixedWidth(150)
        self.stats_end_date.setFont(QFont('Segoe UI', 10))
        self.stats_end_date.dateChanged.connect(self.load_statistics)
        end_date_box.addWidget(self.stats_end_date)
        filter_layout.addLayout(end_date_box)

        # Предмет
        subject_box = QVBoxLayout()
        subject_label = QLabel('Предмет:')
        subject_label.setFont(QFont('Segoe UI', 10))
        subject_box.addWidget(subject_label)
        self.stats_subject_filter = QComboBox()
        self.stats_subject_filter.setFixedHeight(40)
        self.stats_subject_filter.setFixedWidth(180)
        self.stats_subject_filter.setFont(QFont('Segoe UI', 10))
        self.stats_subject_filter.currentIndexChanged.connect(self.load_statistics)
        subject_box.addWidget(self.stats_subject_filter)
        filter_layout.addLayout(subject_box)

        # Группа
        group_box = QVBoxLayout()
        group_label = QLabel('Группа:')
        group_label.setFont(QFont('Segoe UI', 10))
        group_box.addWidget(group_label)
        self.stats_group_filter = QComboBox()
        self.stats_group_filter.setFixedHeight(40)
        self.stats_group_filter.setFixedWidth(180)
        self.stats_group_filter.setFont(QFont('Segoe UI', 10))
        self.stats_group_filter.currentIndexChanged.connect(self.load_statistics)
        group_box.addWidget(self.stats_group_filter)
        filter_layout.addLayout(group_box)

        # Пара
        lesson_box = QVBoxLayout()
        lesson_label = QLabel('Пара:')
        lesson_label.setFont(QFont('Segoe UI', 10))
        lesson_box.addWidget(lesson_label)
        self.stats_lesson_filter = QComboBox()
        self.stats_lesson_filter.setFixedHeight(40)
        self.stats_lesson_filter.setFixedWidth(120)
        self.stats_lesson_filter.setFont(QFont('Segoe UI', 10))
        self.stats_lesson_filter.addItem("Все пары", None)
        for i in range(1, 5):
            self.stats_lesson_filter.addItem(f"Пара {i}", i)
        self.stats_lesson_filter.currentIndexChanged.connect(self.load_statistics)
        lesson_box.addWidget(self.stats_lesson_filter)
        filter_layout.addLayout(lesson_box)

        layout.addLayout(filter_layout)

        # Таблица
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(9)
        self.stats_table.setHorizontalHeaderLabels([
            'Фамилия', 'Имя', 'Группа', 'Предмет',
            'Присутствовал', 'Опоздал', 'Болел',
            'Отсутствовал', 'Посещаемость (%)'
        ])
        for i in range(9):
            self.stats_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setFont(QFont('Segoe UI', 10))
        self.stats_table.setAlternatingRowColors(True)
        layout.addWidget(self.stats_table, 1)

        # Итоговая сводка
        self.stats_summary = QLabel()
        self.stats_summary.setFont(QFont('Segoe UI', 10))
        self.stats_summary.setAlignment(Qt.AlignRight)
        layout.addWidget(self.stats_summary)

    def load_groups(self):
        try:
            self.cursor.execute("SELECT name FROM groups ORDER BY name")
            groups = self.cursor.fetchall()
            self.filter_group.clear()
            for group in groups:
                self.filter_group.addItem(group[0], group[0])
            self.stats_group_filter.clear()
            for group in groups:
                self.stats_group_filter.addItem(group[0], group[0])
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке групп: {str(e)}')

    def load_subjects(self):
        try:
            self.cursor.execute("SELECT name FROM subjects ORDER BY name")
            subjects = self.cursor.fetchall()
            self.subject_combo.clear()
            self.stats_subject_filter.clear()
            for subject in subjects:
                self.subject_combo.addItem(subject[0], subject[0])
                self.stats_subject_filter.addItem(subject[0], subject[0])
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке предметов: {str(e)}')

    def get_students(self, group_name=None):
        try:
            if group_name:
                query = '''
                    SELECT s.id, s.surname, s.name, g.name, s.is_nonresident
                    FROM students s
                    JOIN groups g ON s.group_id = g.id
                    WHERE g.name = ?
                    ORDER BY s.surname, s.name
                '''
                params = (group_name,)
            else:
                query = '''
                    SELECT s.id, s.surname, s.name, g.name, s.is_nonresident
                    FROM students s
                    JOIN groups g ON s.group_id = g.id
                    ORDER BY g.name, s.surname, s.name
                '''
                params = ()
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке студентов: {str(e)}')
            return []

    def load_attendance_data(self):
        try:
            date = self.filter_date.date().toString('yyyy-MM-dd')
            lesson_num = self.lesson_number.value()
            group_name = self.filter_group.currentData()
            subject_name = self.subject_combo.currentData()

            # Получаем предмет
            subject_id = None
            subject_display = ""
            if subject_name:
                self.cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                subject_id = self.cursor.fetchone()[0]

            # Запрос
            query = '''
                SELECT a.student_id, a.status 
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN groups g ON s.group_id = g.id
                WHERE a.date = ? AND a.lesson_number = ?
                AND (? IS NULL OR g.name = ?)
                AND (? IS NULL OR a.subject_id = ?)
            '''
            self.cursor.execute(query, (date, lesson_num, group_name, group_name, subject_id, subject_id))
            attendance_records = {row[0]: row[1] for row in self.cursor.fetchall()}

            students = self.get_students(group_name)

            self.attendance_table.setRowCount(len(students))
            for row, (student_id, surname, name, group, is_nonresident) in enumerate(students):
                status = attendance_records.get(student_id, 'present')
                self.attendance_table.setItem(row, 0, QTableWidgetItem(str(student_id)))

                surname_item = QTableWidgetItem(surname)
                if is_nonresident:
                    surname_item.setData(Qt.UserRole, 'nonresident')
                self.attendance_table.setItem(row, 1, surname_item)

                self.attendance_table.setItem(row, 2, QTableWidgetItem(name))
                self.attendance_table.setItem(row, 3, QTableWidgetItem(group))
                self.attendance_table.setItem(row, 4, QTableWidgetItem(subject_display))

                # Статус радиокнопки
                status_widget = QWidget()
                status_layout = QHBoxLayout(status_widget)
                status_layout.setContentsMargins(5, 0, 5, 0)
                status_layout.setSpacing(8)

                button_group = QButtonGroup(status_widget)
                buttons = [
                    QRadioButton("Присут.", objectName='present'),
                    QRadioButton("Опоздал", objectName='late'),
                    QRadioButton("Болел", objectName='sick'),
                    QRadioButton("Отсут.", objectName='absent')
                ]
                for btn in buttons:
                    btn.setProperty('status', btn.objectName())
                    button_group.addButton(btn)
                    status_layout.addWidget(btn)
                    if btn.property('status') == status:
                        btn.setChecked(True)
                status_widget.button_group = button_group
                self.attendance_table.setCellWidget(row, 5, status_widget)
                self.attendance_table.setRowHeight(row, 50)
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке данных: {str(e)}')

    def load_statistics(self):
        try:
            start_date = self.stats_start_date.date().toString('yyyy-MM-dd')
            end_date = self.stats_end_date.date().toString('yyyy-MM-dd')
            group_name = self.stats_group_filter.currentData()
            subject_name = self.stats_subject_filter.currentData()
            lesson_num = self.stats_lesson_filter.currentData()

            # Получаем предмет
            subject_id = None
            if subject_name:
                self.cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                subject_id = self.cursor.fetchone()[0]

            # Статистика
            query = '''
                SELECT 
                    s.id,
                    s.surname,
                    s.name,
                    g.name,
                    sub.name,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN a.status = 'sick' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END),
                    COUNT(a.id)
                FROM students s
                JOIN groups g ON g.id = s.group_id
                LEFT JOIN attendance a ON s.id = a.student_id
                    AND a.date BETWEEN ? AND ?
                    AND (? IS NULL OR a.lesson_number = ?)
                    AND (? IS NULL OR a.subject_id = ?)
                LEFT JOIN subjects sub ON a.subject_id = sub.id
                WHERE (? IS NULL OR g.name = ?)
                GROUP BY s.id, s.surname, s.name, g.name, sub.name
                ORDER BY g.name, s.surname, s.name
            '''
            self.cursor.execute(query, (
                start_date, end_date,
                lesson_num, lesson_num,
                subject_id, subject_id,
                group_name, group_name
            ))
            data = self.cursor.fetchall()

            # Таблица
            self.stats_table.setRowCount(len(data) + 1)
            total_present = total_late = total_sick = total_absent = total_lessons = 0

            for row_idx, row_data in enumerate(data):
                (sid, surname, name, grp, subj, present, late, sick, absent, lessons) = row_data
                self.stats_table.setItem(row_idx, 0, QTableWidgetItem(surname))
                self.stats_table.setItem(row_idx, 1, QTableWidgetItem(name))
                self.stats_table.setItem(row_idx, 2, QTableWidgetItem(grp))
                self.stats_table.setItem(row_idx, 3, QTableWidgetItem(subj))
                self.stats_table.setItem(row_idx, 4, QTableWidgetItem(str(present)))
                self.stats_table.setItem(row_idx, 5, QTableWidgetItem(str(late)))
                self.stats_table.setItem(row_idx, 6, QTableWidgetItem(str(sick)))
                self.stats_table.setItem(row_idx, 7, QTableWidgetItem(str(absent)))

                total_attended = present + late
                attendance_percent = 0
                if lessons > 0:
                    attendance_percent = round((total_attended / lessons) * 100, 1)
                percent_item = QTableWidgetItem(f"{attendance_percent}%")
                if attendance_percent < 70:
                    percent_item.setForeground(QColor('#d9534f'))  # красный
                elif attendance_percent < 90:
                    percent_item.setForeground(QColor('#f0ad4e'))  # оранжевый
                else:
                    percent_item.setForeground(QColor('#5cb85c'))  # зеленый
                self.stats_table.setItem(row_idx, 8, percent_item)

                # Суммируем
                total_present += present
                total_late += late
                total_sick += sick
                total_absent += absent
                total_lessons += lessons

            # Итоговая строка
            total_row = len(data)
            self.stats_table.setItem(total_row, 0, QTableWidgetItem("ИТОГО"))
            self.stats_table.setItem(total_row, 1, QTableWidgetItem(""))
            self.stats_table.setItem(total_row, 2, QTableWidgetItem(""))
            self.stats_table.setItem(total_row, 3, QTableWidgetItem(""))

            self.stats_table.setItem(total_row, 4, QTableWidgetItem(str(total_present)))
            self.stats_table.setItem(total_row, 5, QTableWidgetItem(str(total_late)))
            self.stats_table.setItem(total_row, 6, QTableWidgetItem(str(total_sick)))
            self.stats_table.setItem(total_row, 7, QTableWidgetItem(str(total_absent)))

            total_attended = total_present + total_late
            total_records = total_attended + total_sick + total_absent
            total_percent = 0
            if total_records > 0:
                total_percent = round((total_attended / total_records) * 100, 1)

            total_percent_item = QTableWidgetItem(f"{total_percent}%")
            if total_percent < 70:
                total_percent_item.setForeground(QColor('#d9534f'))
            elif total_percent < 90:
                total_percent_item.setForeground(QColor('#f0ad4e'))
            else:
                total_percent_item.setForeground(QColor('#5cb85c'))
            self.stats_table.setItem(total_row, 8, total_percent_item)

            # Выделяем итоги
            for col in range(9):
                item = self.stats_table.item(total_row, col)
                if item:
                    item.setBackground(QColor('#f0f0f0'))
                    item.setFont(QFont('Segoe UI', 11, QFont.Bold))

            # Общая сводка
            period_text = f"Период: {start_date} - {end_date}"
            group_text = f"Группа: {group_name if group_name else 'Все'}"
            subject_text = f"Предмет: {subject_name if subject_name else 'Все'}"
            lesson_text = f"Пара: {f'№{lesson_num}' if lesson_num else 'Все'}"
            total_text = f"Всего пар: {total_lessons} | Посещаемость: {total_percent}%"

            self.stats_summary.setText(
                f"{period_text} | {group_text} | {subject_text} | {lesson_text}\n"
                f"{total_text}"
            )
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке статистики: {str(e)}')

    def save_attendance(self):
        try:
            date = self.filter_date.date().toString('yyyy-MM-dd')
            lesson_num = self.lesson_number.value()
            subject_name = self.subject_combo.currentData()
            total = self.attendance_table.rowCount()
            saved = 0
            subject_id = None
            
            if subject_name:
                self.cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                subject_id = self.cursor.fetchone()[0]
                
            for row in range(total):
                student_id = int(self.attendance_table.item(row, 0).text())
                radio_widget = self.attendance_table.cellWidget(row, 5)
                status = 'present'
                for btn in radio_widget.button_group.buttons():
                    if btn.isChecked():
                        status = btn.property('status')
                        break
                
                self.cursor.execute('''
                    INSERT OR REPLACE INTO attendance 
                    (student_id, date, lesson_number, subject_id, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, date, lesson_num, subject_id, status))
                saved += 1
            
            self.conn.commit()
            self.load_statistics()

            # Обновляем стиль статус бара без перезаписи свойств
            self.status_bar.setText(f"Сохранено: {saved} записей")
            self.status_bar.setStyleSheet("color: #4CAF50; font-weight: bold;")  # зеленый
        except sqlite3.Error as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при сохранении: {str(e)}')

class UserWindow(QWidget):
    def __init__(self, db_path='university.db'):
        super().__init__()
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

        self.setWindowTitle('Система учета посещаемости (многопарная)')
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1400, 800)

        self.init_ui()
        self.set_style()

    def create_tables(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    surname TEXT NOT NULL,
                    name TEXT NOT NULL,
                    group_id INTEGER,
                    is_nonresident BOOLEAN DEFAULT 0,
                    FOREIGN KEY (group_id) REFERENCES groups(id)
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    lesson_number INTEGER NOT NULL,
                    subject_id INTEGER,
                    status TEXT NOT NULL CHECK(status IN ('present', 'late', 'sick', 'absent')),
                    UNIQUE(student_id, date, lesson_number)
                )
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при создании таблиц: {str(e)}')

    def init_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont('Segoe UI', 12))
        
        self.attendance_tab = QWidget()
        self.init_attendance_tab()
        self.stats_tab = QWidget()
        self.init_stats_tab()

        self.tabs.addTab(self.attendance_tab, "Учет посещаемости")
        self.tabs.addTab(self.stats_tab, "Статистика")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.addWidget(self.tabs)

        self.load_groups()
        self.load_subjects()
        self.load_attendance_data()
        self.load_statistics()

    def init_attendance_tab(self):
        layout = QVBoxLayout(self.attendance_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 10)
        title_layout.setSpacing(15)

        self.title = QLabel('Учет посещаемости (по парам)')
        self.title.setFont(QFont('Arial', 16, QFont.Bold))
        title_layout.addWidget(self.title, 1)

        layout.addLayout(title_layout)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(1)
        separator.setStyleSheet("color: #d0d0d0;")
        layout.addWidget(separator)

        # Панель фильтров
        filter_panel = QFrame()
        filter_panel.setObjectName('filterPanel')
        filter_layout = QHBoxLayout(filter_panel)
        filter_layout.setContentsMargins(15, 15, 15, 15)
        filter_layout.setSpacing(20)

        # Фильтр по дате
        date_filter = QFrame()
        date_filter.setObjectName('dateFilter')
        date_layout = QVBoxLayout(date_filter)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(5)

        date_label = QLabel('Дата:')
        date_label.setFont(QFont('Segoe UI', 11))
        date_layout.addWidget(date_label)

        self.filter_date = QDateEdit()
        self.filter_date.setDate(QDate.currentDate())
        self.filter_date.setCalendarPopup(True)
        self.filter_date.setDisplayFormat("dd.MM.yyyy")
        self.filter_date.setFixedHeight(40)
        self.filter_date.setFixedWidth(150)
        self.filter_date.setFont(QFont('Segoe UI', 11))
        self.filter_date.dateChanged.connect(self.load_attendance_data)
        date_layout.addWidget(self.filter_date)

        filter_layout.addWidget(date_filter)

        # Номер пары
        lesson_filter = QFrame()
        lesson_filter.setObjectName('lessonFilter')
        lesson_layout = QVBoxLayout(lesson_filter)
        lesson_layout.setContentsMargins(0, 0, 0, 0)
        lesson_layout.setSpacing(5)

        lesson_label = QLabel('Номер пары:')
        lesson_label.setFont(QFont('Segoe UI', 11))
        lesson_layout.addWidget(lesson_label)

        self.lesson_number = QSpinBox()
        self.lesson_number.setRange(1, 4)
        self.lesson_number.setValue(1)
        self.lesson_number.setFixedHeight(40)
        self.lesson_number.setFixedWidth(100)
        self.lesson_number.setFont(QFont('Segoe UI', 11))
        self.lesson_number.valueChanged.connect(self.load_attendance_data)
        lesson_layout.addWidget(self.lesson_number)

        filter_layout.addWidget(lesson_filter)

        # Предмет
        subject_filter = QFrame()
        subject_filter.setObjectName('subjectFilter')
        subject_layout = QVBoxLayout(subject_filter)
        subject_layout.setContentsMargins(0, 0, 0, 0)
        subject_layout.setSpacing(5)

        subject_label = QLabel('Предмет:')
        subject_label.setFont(QFont('Segoe UI', 11))
        subject_layout.addWidget(subject_label)

        self.subject_combo = QComboBox()
        self.subject_combo.setFixedHeight(40)
        self.subject_combo.setFixedWidth(200)
        self.subject_combo.setFont(QFont('Segoe UI', 11))
        self.subject_combo.currentIndexChanged.connect(self.load_attendance_data)
        subject_layout.addWidget(self.subject_combo)

        filter_layout.addWidget(subject_filter)

        # Группа
        group_filter = QFrame()
        group_filter.setObjectName('groupFilter')
        group_layout = QVBoxLayout(group_filter)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(5)

        group_label = QLabel('Группа:')
        group_label.setFont(QFont('Segoe UI', 11))
        group_layout.addWidget(group_label)

        self.filter_group = QComboBox()
        self.filter_group.setFixedHeight(40)
        self.filter_group.setFixedWidth(200)
        self.filter_group.setFont(QFont('Segoe UI', 11))
        self.filter_group.currentIndexChanged.connect(self.load_attendance_data)
        group_layout.addWidget(self.filter_group)

        filter_layout.addWidget(group_filter)

        # Кнопка
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)

        self.save_btn = QPushButton('Сохранить')
        self.save_btn.setIcon(QIcon.fromTheme('document-save'))
        self.save_btn.setFixedHeight(45)
        self.save_btn.setFixedWidth(150)
        self.save_btn.setFont(QFont('Segoe UI', 12))
        self.save_btn.clicked.connect(self.save_attendance)
        button_layout.addWidget(self.save_btn)

        filter_layout.addLayout(button_layout)

        layout.addWidget(filter_panel)

        # Таблица посещаемости
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(6)
        self.attendance_table.setHorizontalHeaderLabels(['ID', 'Фамилия', 'Имя', 'Группа', 'Предмет', 'Статус'])
        self.attendance_table.setColumnHidden(0, True)
        self.attendance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.attendance_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.attendance_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.attendance_table.verticalHeader().setVisible(False)
        self.attendance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.attendance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.attendance_table.setFont(QFont('Segoe UI', 11))
        self.attendance_table.setAlternatingRowColors(True)
        layout.addWidget(self.attendance_table, 1)

        # Статус бар
        self.status_bar = QLabel()
        self.status_bar.setFont(QFont('Segoe UI', 10))
        self.status_bar.setAlignment(Qt.AlignRight)
        layout.addWidget(self.status_bar)

    def init_stats_tab(self):
        layout = QVBoxLayout(self.stats_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel('Статистика посещаемости (по парам)')
        title.setFont(QFont('Segoe UI', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Фильтры
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)

        # Дата начала
        start_date_box = QVBoxLayout()
        start_date_label = QLabel('Дата начала:')
        start_date_label.setFont(QFont('Segoe UI', 10))
        start_date_box.addWidget(start_date_label)
        self.stats_start_date = QDateEdit()
        self.stats_start_date.setDate(QDate.currentDate().addDays(-7))
        self.stats_start_date.setCalendarPopup(True)
        self.stats_start_date.setDisplayFormat("dd.MM.yyyy")
        self.stats_start_date.setFixedHeight(40)
        self.stats_start_date.setFixedWidth(150)
        self.stats_start_date.setFont(QFont('Segoe UI', 10))
        self.stats_start_date.dateChanged.connect(self.load_statistics)
        start_date_box.addWidget(self.stats_start_date)
        filter_layout.addLayout(start_date_box)

        # Дата конца
        end_date_box = QVBoxLayout()
        end_date_label = QLabel('Дата окончания:')
        end_date_label.setFont(QFont('Segoe UI', 10))
        end_date_box.addWidget(end_date_label)
        self.stats_end_date = QDateEdit()
        self.stats_end_date.setDate(QDate.currentDate())
        self.stats_end_date.setCalendarPopup(True)
        self.stats_end_date.setDisplayFormat("dd.MM.yyyy")
        self.stats_end_date.setFixedHeight(40)
        self.stats_end_date.setFixedWidth(150)
        self.stats_end_date.setFont(QFont('Segoe UI', 10))
        self.stats_end_date.dateChanged.connect(self.load_statistics)
        end_date_box.addWidget(self.stats_end_date)
        filter_layout.addLayout(end_date_box)

        # Предмет
        subject_box = QVBoxLayout()
        subject_label = QLabel('Предмет:')
        subject_label.setFont(QFont('Segoe UI', 10))
        subject_box.addWidget(subject_label)
        self.stats_subject_filter = QComboBox()
        self.stats_subject_filter.setFixedHeight(40)
        self.stats_subject_filter.setFixedWidth(180)
        self.stats_subject_filter.setFont(QFont('Segoe UI', 10))
        self.stats_subject_filter.currentIndexChanged.connect(self.load_statistics)
        subject_box.addWidget(self.stats_subject_filter)
        filter_layout.addLayout(subject_box)

        # Группа
        group_box = QVBoxLayout()
        group_label = QLabel('Группа:')
        group_label.setFont(QFont('Segoe UI', 10))
        group_box.addWidget(group_label)
        self.stats_group_filter = QComboBox()
        self.stats_group_filter.setFixedHeight(40)
        self.stats_group_filter.setFixedWidth(180)
        self.stats_group_filter.setFont(QFont('Segoe UI', 10))
        self.stats_group_filter.currentIndexChanged.connect(self.load_statistics)
        group_box.addWidget(self.stats_group_filter)
        filter_layout.addLayout(group_box)

        # Пара
        lesson_box = QVBoxLayout()
        lesson_label = QLabel('Пара:')
        lesson_label.setFont(QFont('Segoe UI', 10))
        lesson_box.addWidget(lesson_label)
        self.stats_lesson_filter = QComboBox()
        self.stats_lesson_filter.setFixedHeight(40)
        self.stats_lesson_filter.setFixedWidth(120)
        self.stats_lesson_filter.setFont(QFont('Segoe UI', 10))
        self.stats_lesson_filter.addItem("Все пары", None)
        for i in range(1, 5):
            self.stats_lesson_filter.addItem(f"Пара {i}", i)
        self.stats_lesson_filter.currentIndexChanged.connect(self.load_statistics)
        lesson_box.addWidget(self.stats_lesson_filter)
        filter_layout.addLayout(lesson_box)

        layout.addLayout(filter_layout)

        # Таблица
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(9)
        self.stats_table.setHorizontalHeaderLabels([
            'Фамилия', 'Имя', 'Группа', 'Предмет',
            'Присутствовал', 'Опоздал', 'Болел',
            'Отсутствовал', 'Посещаемость (%)'
        ])
        for i in range(9):
            self.stats_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setFont(QFont('Segoe UI', 10))
        self.stats_table.setAlternatingRowColors(True)
        layout.addWidget(self.stats_table, 1)

        # Итоговая сводка
        self.stats_summary = QLabel()
        self.stats_summary.setFont(QFont('Segoe UI', 10))
        self.stats_summary.setAlignment(Qt.AlignRight)
        layout.addWidget(self.stats_summary)

    def load_groups(self):
        try:
            self.cursor.execute("SELECT name FROM groups ORDER BY name")
            groups = self.cursor.fetchall()
            self.filter_group.clear()
            for group in groups:
                self.filter_group.addItem(group[0], group[0])
            self.stats_group_filter.clear()
            for group in groups:
                self.stats_group_filter.addItem(group[0], group[0])
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке групп: {str(e)}')

    def load_subjects(self):
        try:
            self.cursor.execute("SELECT name FROM subjects ORDER BY name")
            subjects = self.cursor.fetchall()
            self.subject_combo.clear()
            self.stats_subject_filter.clear()
            for subject in subjects:
                self.subject_combo.addItem(subject[0], subject[0])
                self.stats_subject_filter.addItem(subject[0], subject[0])
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке предметов: {str(e)}')

    def get_students(self, group_name=None):
        try:
            if group_name:
                query = '''
                    SELECT s.id, s.surname, s.name, g.name, s.is_nonresident
                    FROM students s
                    JOIN groups g ON s.group_id = g.id
                    WHERE g.name = ?
                    ORDER BY s.surname, s.name
                '''
                params = (group_name,)
            else:
                query = '''
                    SELECT s.id, s.surname, s.name, g.name, s.is_nonresident
                    FROM students s
                    JOIN groups g ON s.group_id = g.id
                    ORDER BY g.name, s.surname, s.name
                '''
                params = ()
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке студентов: {str(e)}')
            return []

    def load_attendance_data(self):
        try:
            date = self.filter_date.date().toString('yyyy-MM-dd')
            lesson_num = self.lesson_number.value()
            group_name = self.filter_group.currentData()
            subject_name = self.subject_combo.currentData()

            # Получаем предмет
            subject_id = None
            subject_display = ""
            if subject_name:
                self.cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                subject_id = self.cursor.fetchone()[0]

            # Запрос
            query = '''
                SELECT a.student_id, a.status 
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                JOIN groups g ON s.group_id = g.id
                WHERE a.date = ? AND a.lesson_number = ?
                AND (? IS NULL OR g.name = ?)
                AND (? IS NULL OR a.subject_id = ?)
            '''
            self.cursor.execute(query, (date, lesson_num, group_name, group_name, subject_id, subject_id))
            attendance_records = {row[0]: row[1] for row in self.cursor.fetchall()}

            students = self.get_students(group_name)

            self.attendance_table.setRowCount(len(students))
            for row, (student_id, surname, name, group, is_nonresident) in enumerate(students):
                status = attendance_records.get(student_id, 'present')
                self.attendance_table.setItem(row, 0, QTableWidgetItem(str(student_id)))

                surname_item = QTableWidgetItem(surname)
                if is_nonresident:
                    surname_item.setData(Qt.UserRole, 'nonresident')
                self.attendance_table.setItem(row, 1, surname_item)

                self.attendance_table.setItem(row, 2, QTableWidgetItem(name))
                self.attendance_table.setItem(row, 3, QTableWidgetItem(group))
                self.attendance_table.setItem(row, 4, QTableWidgetItem(subject_display))

                # Статус радиокнопки
                status_widget = QWidget()
                status_layout = QHBoxLayout(status_widget)
                status_layout.setContentsMargins(5, 0, 5, 0)
                status_layout.setSpacing(8)

                button_group = QButtonGroup(status_widget)
                buttons = [
                    QRadioButton("Присут.", objectName='present'),
                    QRadioButton("Опоздал", objectName='late'),
                    QRadioButton("Болел", objectName='sick'),
                    QRadioButton("Отсут.", objectName='absent')
                ]
                for btn in buttons:
                    btn.setProperty('status', btn.objectName())
                    button_group.addButton(btn)
                    status_layout.addWidget(btn)
                    if btn.property('status') == status:
                        btn.setChecked(True)
                status_widget.button_group = button_group
                self.attendance_table.setCellWidget(row, 5, status_widget)
                self.attendance_table.setRowHeight(row, 50)
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке данных: {str(e)}')

    def load_statistics(self):
        try:
            start_date = self.stats_start_date.date().toString('yyyy-MM-dd')
            end_date = self.stats_end_date.date().toString('yyyy-MM-dd')
            group_name = self.stats_group_filter.currentData()
            subject_name = self.stats_subject_filter.currentData()
            lesson_num = self.stats_lesson_filter.currentData()

            # Получаем предмет
            subject_id = None
            if subject_name:
                self.cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                subject_id = self.cursor.fetchone()[0]

            # Статистика
            query = '''
                SELECT 
                    s.id,
                    s.surname,
                    s.name,
                    g.name,
                    sub.name,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN a.status = 'sick' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END),
                    COUNT(a.id)
                FROM students s
                JOIN groups g ON g.id = s.group_id
                LEFT JOIN attendance a ON s.id = a.student_id
                    AND a.date BETWEEN ? AND ?
                    AND (? IS NULL OR a.lesson_number = ?)
                    AND (? IS NULL OR a.subject_id = ?)
                LEFT JOIN subjects sub ON a.subject_id = sub.id
                WHERE (? IS NULL OR g.name = ?)
                GROUP BY s.id, s.surname, s.name, g.name, sub.name
                ORDER BY g.name, s.surname, s.name
            '''
            self.cursor.execute(query, (
                start_date, end_date,
                lesson_num, lesson_num,
                subject_id, subject_id,
                group_name, group_name
            ))
            data = self.cursor.fetchall()

            # Таблица
            self.stats_table.setRowCount(len(data) + 1)
            total_present = total_late = total_sick = total_absent = total_lessons = 0

            for row_idx, row_data in enumerate(data):
                (sid, surname, name, grp, subj, present, late, sick, absent, lessons) = row_data
                self.stats_table.setItem(row_idx, 0, QTableWidgetItem(surname))
                self.stats_table.setItem(row_idx, 1, QTableWidgetItem(name))
                self.stats_table.setItem(row_idx, 2, QTableWidgetItem(grp))
                self.stats_table.setItem(row_idx, 3, QTableWidgetItem(subj))
                self.stats_table.setItem(row_idx, 4, QTableWidgetItem(str(present)))
                self.stats_table.setItem(row_idx, 5, QTableWidgetItem(str(late)))
                self.stats_table.setItem(row_idx, 6, QTableWidgetItem(str(sick)))
                self.stats_table.setItem(row_idx, 7, QTableWidgetItem(str(absent)))

                total_attended = present + late
                attendance_percent = 0
                if lessons > 0:
                    attendance_percent = round((total_attended / lessons) * 100, 1)
                percent_item = QTableWidgetItem(f"{attendance_percent}%")
                if attendance_percent < 70:
                    percent_item.setForeground(QColor('#d9534f'))  # красный
                elif attendance_percent < 90:
                    percent_item.setForeground(QColor('#f0ad4e'))  # оранжевый
                else:
                    percent_item.setForeground(QColor('#5cb85c'))  # зеленый
                self.stats_table.setItem(row_idx, 8, percent_item)

                # Суммируем
                total_present += present
                total_late += late
                total_sick += sick
                total_absent += absent
                total_lessons += lessons

            # Итоговая строка
            total_row = len(data)
            self.stats_table.setItem(total_row, 0, QTableWidgetItem("ИТОГО"))
            self.stats_table.setItem(total_row, 1, QTableWidgetItem(""))
            self.stats_table.setItem(total_row, 2, QTableWidgetItem(""))
            self.stats_table.setItem(total_row, 3, QTableWidgetItem(""))

            self.stats_table.setItem(total_row, 4, QTableWidgetItem(str(total_present)))
            self.stats_table.setItem(total_row, 5, QTableWidgetItem(str(total_late)))
            self.stats_table.setItem(total_row, 6, QTableWidgetItem(str(total_sick)))
            self.stats_table.setItem(total_row, 7, QTableWidgetItem(str(total_absent)))

            total_attended = total_present + total_late
            total_records = total_attended + total_sick + total_absent
            total_percent = 0
            if total_records > 0:
                total_percent = round((total_attended / total_records) * 100, 1)

            total_percent_item = QTableWidgetItem(f"{total_percent}%")
            if total_percent < 70:
                total_percent_item.setForeground(QColor('#d9534f'))
            elif total_percent < 90:
                total_percent_item.setForeground(QColor('#f0ad4e'))
            else:
                total_percent_item.setForeground(QColor('#5cb85c'))
            self.stats_table.setItem(total_row, 8, total_percent_item)

            # Выделяем итоги
            for col in range(9):
                item = self.stats_table.item(total_row, col)
                if item:
                    item.setBackground(QColor('#f0f0f0'))
                    item.setFont(QFont('Segoe UI', 11, QFont.Bold))

            # Общая сводка
            period_text = f"Период: {start_date} - {end_date}"
            group_text = f"Группа: {group_name if group_name else 'Все'}"
            subject_text = f"Предмет: {subject_name if subject_name else 'Все'}"
            lesson_text = f"Пара: {f'№{lesson_num}' if lesson_num else 'Все'}"
            total_text = f"Всего пар: {total_lessons} | Посещаемость: {total_percent}%"

            self.stats_summary.setText(
                f"{period_text} | {group_text} | {subject_text} | {lesson_text}\n"
                f"{total_text}"
            )
        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при загрузке статистики: {str(e)}')

    def save_attendance(self):
        try:
            date = self.filter_date.date().toString('yyyy-MM-dd')
            lesson_num = self.lesson_number.value()
            subject_name = self.subject_combo.currentData()
            total = self.attendance_table.rowCount()
            saved = 0
            subject_id = None
            
            if subject_name:
                self.cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                subject_id = self.cursor.fetchone()[0]
                
            for row in range(total):
                student_id = int(self.attendance_table.item(row, 0).text())
                radio_widget = self.attendance_table.cellWidget(row, 5)
                status = 'present'
                for btn in radio_widget.button_group.buttons():
                    if btn.isChecked():
                        status = btn.property('status')
                        break
                
                self.cursor.execute('''
                    INSERT OR REPLACE INTO attendance 
                    (student_id, date, lesson_number, subject_id, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, date, lesson_num, subject_id, status))
                saved += 1
            
            self.conn.commit()
            self.load_statistics()

            # Обновляем стиль статус бара без перезаписи свойств
            self.status_bar.setText(f"Сохранено: {saved} записей")
            self.status_bar.setStyleSheet("color: #4CAF50; font-weight: bold;")  # зеленый
        except sqlite3.Error as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Ошибка базы данных', f'Ошибка при сохранении: {str(e)}')

    def set_style(self):
        self.setStyleSheet('''
            QWidget {
                background-color: #ffffff;
                color: #333;
                font-family: "Segoe UI", Arial;
            }
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                color: #555;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #333;
                border-bottom: 2px solid #2196F3;
                font-weight: bold;
            }
            QLabel {
                color: #444;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QComboBox, QDateEdit, QSpinBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 30px;
                background: #fff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #ccc;
            }
            QTableWidget {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background: #fff;
                gridline-color: #eee;
                selection-background-color: #e3f2fd;
                selection-color: #000;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QRadioButton {
                spacing: 5px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            #filterPanel, #dateFilter, #lessonFilter, #subjectFilter, #groupFilter {
                background: #fff;
                border-radius: 4px;
                border: 1px solid #d0d0d0;
            }
            ''')


    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Закрытие приложения',
            'Вы уверены, что хотите закрыть приложение?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.conn.close()
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = UserWindow()
    window.show()
    sys.exit(app.exec_())
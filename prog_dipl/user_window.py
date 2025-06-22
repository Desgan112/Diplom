import requests
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QMessageBox, QTabWidget,
                            QVBoxLayout, QTableWidget, QTableWidgetItem, QDateEdit,
                            QComboBox, QHBoxLayout, QHeaderView, QFrame, QSpinBox,
                            QFileDialog,QButtonGroup,QRadioButton,QApplication)
from PyQt5.QtGui import QFont, QIcon, QColor
from PyQt5.QtCore import Qt, QDate,QSizeF
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument
import xlsxwriter
class ServerAPI:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
    
    def _make_request(self, method, endpoint, data=None):
        try:
            url = f"{self.base_url}{endpoint}"
            if method == "GET":
                response = requests.get(url, params=data)
            elif method == "POST":
                response = requests.post(url, json=data)
            elif method == "PUT":
                response = requests.put(url, json=data)
            elif method == "DELETE":
                response = requests.delete(url)
            
            if response.status_code >= 400:
                error_msg = response.json().get('error', 'Unknown error')
                raise Exception(f"Server error: {error_msg}")
            
            return response.json()
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(None, 'Connection Error', f'Failed to connect to server: {str(e)}')
            raise
    
    def get_groups(self):
        return self._make_request("GET", "/api/get_universities")
    
    def get_subjects(self):
        return self._make_request("GET", "/api/subjects")
    
    def get_students(self, group_id=None):
        params = {}
        if group_id:
            params['group_id'] = group_id
        return self._make_request("GET", "/api/get_students", params)
    
    def get_attendance(self, date, lesson_number, group_id=None, subject_id=None):
        params = {
            'date': date,
            'lesson_number': lesson_number
        }
        if group_id:
            params['group_id'] = group_id
        if subject_id:
            params['subject_id'] = subject_id
        return self._make_request("GET", "/api/get_attendance", params)
    
    def save_attendance(self, student_id, date, lesson_number, status, subject_id=None):
        data = {
            'student_id': student_id,
            'date': date,
            'lesson_number': lesson_number,
            'status': status
        }
        if subject_id:
            data['subject_id'] = subject_id
        return self._make_request("POST", "/api/save_attendance", data)
    
    def get_statistics(self, start_date, end_date, group_id=None, subject_id=None, lesson_number=None):
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        if group_id:
            params['group_id'] = group_id
        if subject_id:
            params['subject_id'] = subject_id
        if lesson_number:
            params['lesson_number'] = lesson_number
        return self._make_request("GET", "/api/get_statistics", params)

class UserWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.api = ServerAPI()
        
        self.setWindowTitle('Система учета посещаемости')
        self.setGeometry(100, 100, 1600, 1000)
        self.setMinimumSize(1400, 800)

        self.init_ui()
        self.set_style()
        self.load_initial_data()

    def load_initial_data(self):
        self.load_groups()
        self.load_subjects()
        self.load_attendance_data()
        self.load_statistics()

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

    def init_attendance_tab(self):
        layout = QVBoxLayout(self.attendance_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 10)
        title_layout.setSpacing(15)

        self.title = QLabel('Учет посещаемости')
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

        # Панель полей выбора
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
        self.attendance_table.setColumnCount(5)
        self.attendance_table.setHorizontalHeaderLabels(['ID', 'Фамилия', 'Имя', 'Группа', 'Статус'])
        self.attendance_table.setColumnHidden(0, True)
        self.attendance_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.attendance_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.attendance_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
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
        title = QLabel('Статистика посещаемости')
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
        export_buttons = QHBoxLayout()
        
        self.export_pdf_btn = QPushButton('Экспорт в PDF')
        self.export_pdf_btn.setIcon(QIcon.fromTheme('document-export'))
        self.export_pdf_btn.setFixedHeight(40)
        self.export_pdf_btn.setFont(QFont('Segoe UI', 10))
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        export_buttons.addWidget(self.export_pdf_btn)
        
        self.export_excel_btn = QPushButton('Экспорт в Excel')
        self.export_excel_btn.setIcon(QIcon.fromTheme('document-export'))
        self.export_excel_btn.setFixedHeight(40)
        self.export_excel_btn.setFont(QFont('Segoe UI', 10))
        self.export_excel_btn.clicked.connect(self.export_to_excel)
        export_buttons.addWidget(self.export_excel_btn)
        
        layout.addLayout(export_buttons)

    def load_groups(self):
        try:
            groups = self.api.get_groups()
            self.filter_group.clear()
            self.stats_group_filter.clear()
            
            for group in groups:
                self.filter_group.addItem(group['name'], group['id'])
                self.stats_group_filter.addItem(group['name'], group['id'])
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке групп: {str(e)}')

    def load_subjects(self):
        try:
            subjects = self.api.get_subjects()
            self.subject_combo.clear()
            self.stats_subject_filter.clear()
            
            for subject in subjects:
                self.subject_combo.addItem(subject['name'], subject['id'])
                self.stats_subject_filter.addItem(subject['name'], subject['id'])
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке предметов: {str(e)}')

    def load_attendance_data(self):
        try:
            date = self.filter_date.date().toString('yyyy-MM-dd')
            lesson_num = self.lesson_number.value()
            group_id = self.filter_group.currentData()
            subject_id = self.subject_combo.currentData()
        
        # Получаем данные о посещаемости
            attendance_data = self.api.get_attendance(
                date=date,
                lesson_number=lesson_num,
                group_id=group_id,
                subject_id=subject_id
            ) or {}  # На случай если сервер вернет None
        
        # Получаем список студентов
            students = self.api.get_students(group_id=group_id)
            if not students:
                raise Exception("Не удалось загрузить список студентов")
        
            self.attendance_table.setRowCount(len(students))
            for row, student in enumerate(students):
                student_id = str(student['id'])
                status = attendance_data.get(student_id, 'present')
            
                self.attendance_table.setItem(row, 0, QTableWidgetItem(student_id))
                self.attendance_table.setItem(row, 1, QTableWidgetItem(student['surname']))
                self.attendance_table.setItem(row, 2, QTableWidgetItem(student['name']))
                self.attendance_table.setItem(row, 3, QTableWidgetItem(student['group_name']))
            

                status_widget = QWidget()
                status_layout = QHBoxLayout(status_widget)
                button_group = QButtonGroup(status_widget)
            
                status_types = [
                    ('present', 'Присут.'),
                    ('late', 'Опоздал'),
                 ('sick', 'Болел'),
                    ('absent', 'Отсут.')
                ]
            
                for status_type, label in status_types:
                    btn = QRadioButton(label)
                    btn.setProperty('status', status_type)
                    button_group.addButton(btn)
                    status_layout.addWidget(btn)
                    if status_type == status:
                        btn.setChecked(True)
            
                self.attendance_table.setCellWidget(row, 4, status_widget)
                self.attendance_table.setRowHeight(row, 50)
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке данных: {str(e)}')

    def save_attendance(self):
        try:
            date = self.filter_date.date().toString('yyyy-MM-dd')
            lesson_num = self.lesson_number.value()
            subject_id = self.subject_combo.currentData()
            saved = 0
            
            for row in range(self.attendance_table.rowCount()):
                student_id = int(self.attendance_table.item(row, 0).text())
                radio_widget = self.attendance_table.cellWidget(row, 4)
                
                status = None
                for btn in radio_widget.findChildren(QRadioButton):
                    if btn.isChecked():
                        status = btn.property('status')
                        break
                
                if status:
                    self.api.save_attendance(
                        student_id=student_id,
                        date=date,
                        lesson_number=lesson_num,
                        status=status,
                        subject_id=subject_id
                    )
                    saved += 1
            
            self.status_bar.setText(f"Сохранено: {saved} записей")
            self.status_bar.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            # Обновляем статистику после сохранения
            self.load_statistics()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при сохранении: {str(e)}')

    def load_statistics(self):
        try:
            start_date = self.stats_start_date.date().toString('yyyy-MM-dd')
            end_date = self.stats_end_date.date().toString('yyyy-MM-dd')
            group_id = self.stats_group_filter.currentData()
            subject_id = self.stats_subject_filter.currentData()
            lesson_num = self.stats_lesson_filter.currentData()
            
            stats = self.api.get_statistics(
                start_date=start_date,
                end_date=end_date,
                group_id=group_id,
                subject_id=subject_id,
                lesson_number=lesson_num
            )
            
            self.update_stats_table(stats)
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке статистики: {str(e)}')

    def update_stats_table(self, stats):
        self.stats_table.setRowCount(len(stats) + 1)
        total_present = total_late = total_sick = total_absent = total_lessons = 0

        for row_idx, row_data in enumerate(stats):
            self.stats_table.setItem(row_idx, 0, QTableWidgetItem(row_data['surname']))
            self.stats_table.setItem(row_idx, 1, QTableWidgetItem(row_data['name']))
            self.stats_table.setItem(row_idx, 2, QTableWidgetItem(row_data['group_name']))
            self.stats_table.setItem(row_idx, 3, QTableWidgetItem(row_data.get('subject_name', '')))
            
            present = row_data.get('present', 0)
            late = row_data.get('late', 0)
            sick = row_data.get('sick', 0)
            absent = row_data.get('absent', 0)
            total = row_data.get('total', 0)
            
            self.stats_table.setItem(row_idx, 4, QTableWidgetItem(str(present)))
            self.stats_table.setItem(row_idx, 5, QTableWidgetItem(str(late)))
            self.stats_table.setItem(row_idx, 6, QTableWidgetItem(str(sick)))
            self.stats_table.setItem(row_idx, 7, QTableWidgetItem(str(absent)))

            total_attended = present + late
            attendance_percent = 0
            if total > 0:
                attendance_percent = round((total_attended / total) * 100, 1)
            
            percent_item = QTableWidgetItem(f"{attendance_percent}%")
            if attendance_percent < 70:
                percent_item.setForeground(QColor('#d9534f'))  # красный
            elif attendance_percent < 90:
                percent_item.setForeground(QColor('#f0ad4e'))  # оранжевый
            else:
                percent_item.setForeground(QColor('#5cb85c'))  # зеленый
            self.stats_table.setItem(row_idx, 8, percent_item)

            total_present += present
            total_late += late
            total_sick += sick
            total_absent += absent
            total_lessons += total

        # Итоговая строка
        total_row = len(stats)
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
        period_text = f"Период: {self.stats_start_date.date().toString('dd.MM.yyyy')} - {self.stats_end_date.date().toString('dd.MM.yyyy')}"
        group_text = f"Группа: {self.stats_group_filter.currentText() if self.stats_group_filter.currentData() else 'Все'}"
        subject_text = f"Предмет: {self.stats_subject_filter.currentText() if self.stats_subject_filter.currentData() else 'Все'}"
        lesson_text = f"Пара: {self.stats_lesson_filter.currentText()}"
        total_text = f"Всего пар: {total_lessons} | Посещаемость: {total_percent}%"

        self.stats_summary.setText(
            f"{period_text} | {group_text} | {subject_text} | {lesson_text}\n"
            f"{total_text}"
        )

    def export_to_pdf(self):
        try:
            # Создаем документ
            doc = QTextDocument()
            doc.setDocumentMargin(0)  # Убираем стандартные отступы
            
            # Рассчитываем масштаб 
            table_width = sum(self.stats_table.columnWidth(col) for col in range(self.stats_table.columnCount()))
            scale_factor = min(5.0, 2500 / table_width)  
            
            # Формируем HTML с разными коэффициентами увеличения
            html = [
                "<html><head><style>",
                "body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; height: 100vh;",
                "display: flex; flex-direction: column; justify-content: center; align-items: center; }",
                "h1 { text-align: center; font-size: 72pt; margin: 0 0 40px 0; font-weight: bold; }",  # В 3 раза больше
                "h2 { text-align: center; font-size: 36pt; margin: 0 0 60px 0; }",  # В 3 раза больше
                "table { border-collapse: collapse; margin: 0 auto 50px auto; }",  # Таблица в 5 раз больше
                "th, td { border: 3px solid #555; padding: 25px; font-size: 25pt; text-align: center; }",  # В 5 раз больше
                "th { background-color: #f2f2f2; font-weight: bold; }",
                ".good { background-color: #d4edda !important; }",
                ".medium { background-color: #fff3cd !important; }",
                ".bad { background-color: #ffdddd !important; }",
                ".summary { font-size: 36pt; text-align: center; margin-top: 60px; line-height: 1.8; }",  # В 3 раза больше
                "</style></head><body>"
            ]
            
            # Заголовок 
            html.append("<h1>СТАТИСТИКА ПОСЕЩАЕМОСТИ</h1>")
            
            # Таблица 
            html.append(f'<table style="font-size: {25*scale_factor}pt">')
            html.append("<colgroup>")
            
            # Ширины столбцов 
            for col in range(self.stats_table.columnCount()):
                width = self.stats_table.columnWidth(col) * scale_factor * 5.0
                html.append(f'<col width="{width}px">')
            
            # Заголовки таблицы
            html.append("<thead><tr>")
            for col in range(self.stats_table.columnCount()):
                header = self.stats_table.horizontalHeaderItem(col).text()
                html.append(f"<th>{header}</th>")
            html.append("</tr></thead><tbody>")
            
            # Данные таблицы
            for row in range(self.stats_table.rowCount()):
                html.append("<tr style='height: 60px;'>")
                for col in range(self.stats_table.columnCount()):
                    item = self.stats_table.item(row, col)
                    text = item.text() if item else ''
                    
                    # Обработка цветов
                    cell_class = ""
                    if col == self.stats_table.columnCount() - 1 and '%' in text:
                        try:
                            percent = float(text.replace('%', '').strip())
                            cell_class = "bad" if percent < 70 else "medium" if percent < 90 else "good"
                        except ValueError:
                            pass
                    
                    html.append(f'<td class="{cell_class}">{text}</td>')
                html.append("</tr>")
            
            html.append("</tbody></table>")
            
            # Статистика 
            summary = self.stats_summary.text().split('\n')
            html.append('<div class="summary">')
            html.extend(f'<div>{line}</div>' for line in summary)
            html.append('</div></body></html>')
            
            doc.setHtml('\n'.join(html))
            
            # Настройка принтера
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setResolution(600)
            printer.setPageSize(QPrinter.A4)
            printer.setFullPage(True)
            printer.setOrientation(QPrinter.Landscape)
            
            # Сохранение файла
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как PDF", "", "PDF Files (*.pdf)")
            
            if file_path:
                if not file_path.endswith('.pdf'):
                    file_path += '.pdf'
                
                printer.setOutputFileName(file_path)
                doc.setPageSize(QSizeF(printer.pageRect().size()))
                doc.print_(printer)
                
                QMessageBox.information(self, "Готово", "PDF создан !")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")

    def export_to_excel(self):
        try:
            # Получаем данные из таблицы
            headers = []
            for col in range(self.stats_table.columnCount()):
                headers.append(self.stats_table.horizontalHeaderItem(col).text())
            
            data = []
            for row in range(self.stats_table.rowCount()):
                row_data = []
                for col in range(self.stats_table.columnCount()):
                    item = self.stats_table.item(row, col)
                    row_data.append(item.text() if item else '')
                data.append(row_data)
            
            # Сохраняем файл
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как Excel", "", "Excel Files (*.xlsx)")
            
            if file_path:
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                
                # Создаем новый Excel файл
                workbook = xlsxwriter.Workbook(file_path)
                worksheet = workbook.add_worksheet('Статистика')
                
                # Форматы
                header_format = workbook.add_format({
                    'bold': True,
                    'border': 1,
                    'bg_color': '#D7E4BC',
                    'align': 'center',
                    'valign': 'vcenter'
                })
                
                # Записываем заголовки
                for col, header in enumerate(headers):
                    worksheet.write(0, col, header, header_format)
                
                # Записываем данные
                for row_num, row_data in enumerate(data, start=1):
                    for col_num, cell_data in enumerate(row_data):
                        worksheet.write(row_num, col_num, cell_data)
                
                # Автонастройка ширины столбцов
                for col, header in enumerate(headers):
                    max_len = len(header)
                    for row in data:
                        if len(str(row[col])) > max_len:
                            max_len = len(str(row[col]))
                    worksheet.set_column(col, col, max_len + 2)
                
                # Добавляем информацию о периоде
                summary = self.stats_summary.text().split('\n')
                worksheet.write(len(data)+1, 0, summary[0])
                worksheet.write(len(data)+2, 0, summary[1])
                
                workbook.close()
                QMessageBox.information(self, "Успех", "Файл успешно сохранен!")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать в Excel: {str(e)}")
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
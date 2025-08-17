from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox, 
                           QGridLayout, QTextEdit, QProgressBar, QMessageBox, QHBoxLayout, 
                           QRadioButton, QButtonGroup, QTabWidget, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QDate, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
import qdarkstyle
import sys
from version import VERSION, AUTHOR, GITHUB_URL
import os

class SRTReservationWorker(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, login_info, train_info, personal_info, settings):
        super().__init__()
        self.login_info = login_info
        self.train_info = train_info
        self.personal_info = personal_info
        self.settings = settings
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = True
        self._stop_requested = False
    
    def stop(self):
        """안전하게 작업 중단"""
        self._stop_requested = True
        self.is_running = False
        
        # 브라우저와 playwright를 즉시 종료
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except:
            pass
        
    def run(self):
        try:
            if self._stop_requested:
                return
                
            from srt_automation import setup_driver, start_reservation
            
            try:
                self.playwright, self.browser, self.context, self.page = setup_driver()
            except Exception as e:
                if "Executable doesn't exist" in str(e) or "Playwright" in str(e):
                    self.progress_signal.emit("⚠️ 브라우저가 설치되지 않았습니다.")
                    self.progress_signal.emit("터미널에서 다음 명령을 실행해주세요:")
                    self.progress_signal.emit("playwright install chromium")
                    self.finished_signal.emit(False)
                    return
                else:
                    raise
            
            if self._stop_requested:
                return
                
            # start_reservation_with_worker 대신 기존 함수 사용
            success = start_reservation(
                self.playwright,
                self.browser,
                self.context,
                self.page,
                self.login_info,
                self.train_info,
                self.personal_info,
                self.settings,
                self.progress_signal
            )
            
            if not self._stop_requested:
                self.finished_signal.emit(success)
        except Exception as e:
            if not self._stop_requested:
                self.progress_signal.emit(f"❌ 오류 발생: {str(e)}")
                self.finished_signal.emit(False)
        finally:
            # 정리 작업
            try:
                if self.page:
                    self.page.close()
            except:
                pass
            try:
                if self.context:
                    self.context.close()
            except:
                pass
            try:
                if self.browser:
                    self.browser.close()
            except:
                pass
            try:
                if self.playwright:
                    self.playwright.stop()
            except:
                pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"🚄 SRT Hunter v{VERSION}")
        self.setGeometry(100, 100, 1100, 750)
        self.setMinimumSize(1000, 700)
        
        # 다크 스타일 적용
        app = QApplication.instance()
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        
        # 메인 위젯
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 메인 레이아웃 - 세로
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_widget.setLayout(main_layout)
        
        # 헤더 추가
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        title_label = QLabel("🚄 SRT 자동 예매 시스템")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
        """)
        
        status_label = QLabel("⚫ 대기")
        status_label.setObjectName("statusLabel")
        status_label.setStyleSheet("""
            font-size: 14px;
            padding: 5px 10px;
            background-color: #2b2b2b;
            border-radius: 10px;
        """)
        self.status_label = status_label
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(status_label)
        main_layout.addLayout(header_layout)
        
        # 탭 위젯 추가
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background-color: #2b2b2b;
                border-radius: 5px;
            }
            QTabBar::tab {
                padding: 6px 16px;
                margin-right: 3px;
            }
            QTabBar::tab:selected {
                background-color: #3c3c3c;
                border-bottom: 2px solid #4CAF50;
            }
        """)
        
        # 예매 탭
        reservation_tab = QWidget()
        self.setup_reservation_tab(reservation_tab)
        self.tab_widget.addTab(reservation_tab, "예매")
        
        # 설정 탭
        settings_tab = QWidget()
        self.setup_settings_tab(settings_tab)
        self.tab_widget.addTab(settings_tab, "설정")
        
        main_layout.addWidget(self.tab_widget)
        
        # 진행 상태 섹션
        status_group = QGroupBox("진행 상태")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        status_layout = QVBoxLayout()
        
        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                text-align: center;
                height: 22px;
                background-color: #1e1e1e;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #3d8b40, stop: 1 #4CAF50);
                border-radius: 3px;
            }
        """)
        self.progress_bar.hide()
        status_layout.addWidget(self.progress_bar)
        
        # 로그 텍스트
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
        """)
        self.log_text.setPlaceholderText("예매 진행 상황이 여기에 표시됩니다...")
        status_layout.addWidget(self.log_text)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # 하단 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 시작 버튼
        self.start_button = QPushButton("예매 시작")
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                padding: 10px 25px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
            QPushButton:disabled {
                background: #555555;
                color: #999999;
            }
        """)
        self.start_button.clicked.connect(self.start_reservation)
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 중단 버튼
        self.reset_button = QPushButton("중단")
        self.reset_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f44336, stop: 1 #da190b);
                color: white;
                border: none;
                padding: 10px 25px;
                font-size: 15px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #da190b, stop: 1 #c41e08);
            }
            QPushButton:pressed {
                background: #c41e08;
            }
        """)
        self.reset_button.clicked.connect(self.reset_program)
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 버전 정보
        version_label = QLabel(f"v{VERSION} | Developed by {AUTHOR}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #666666; font-size: 11px;")
        main_layout.addWidget(version_label)
        
        # 초기 설정
        self.update_time_options()
        self.load_login_info()
        
    def setup_reservation_tab(self, parent):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 로그인 정보와 개인정보를 한 줄에 배치
        top_layout = QHBoxLayout()
        
        # 로그인 정보
        login_group = QGroupBox("로그인 정보")
        login_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        login_layout = QGridLayout()
        login_layout.setSpacing(8)
        
        self.id_input = QLineEdit()
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.id_input.setPlaceholderText("SRT 회원번호")
        self.pw_input.setPlaceholderText("비밀번호")
        
        # 스타일 적용
        input_style = """
            QLineEdit {
                padding: 8px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """
        self.id_input.setStyleSheet(input_style)
        self.pw_input.setStyleSheet(input_style)
        
        login_layout.addWidget(QLabel("회원번호:"), 0, 0)
        login_layout.addWidget(self.id_input, 0, 1)
        login_layout.addWidget(QLabel("비밀번호:"), 1, 0)
        login_layout.addWidget(self.pw_input, 1, 1)
        
        login_group.setLayout(login_layout)
        
        # 개인정보
        personal_group = QGroupBox("결제 정보")
        personal_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        personal_layout = QGridLayout()
        personal_layout.setSpacing(8)
        
        self.phone_input = QLineEdit()
        self.birth_input = QLineEdit()
        self.phone_input.setPlaceholderText("01012345678")
        self.birth_input.setPlaceholderText("990101 (6자리)")
        
        self.phone_input.setStyleSheet(input_style)
        self.birth_input.setStyleSheet(input_style)
        
        personal_layout.addWidget(QLabel("전화번호:"), 0, 0)
        personal_layout.addWidget(self.phone_input, 0, 1)
        personal_layout.addWidget(QLabel("생년월일:"), 1, 0)
        personal_layout.addWidget(self.birth_input, 1, 1)
        
        personal_group.setLayout(personal_layout)
        
        top_layout.addWidget(login_group)
        top_layout.addWidget(personal_group)
        layout.addLayout(top_layout)
        
        # 예매 정보
        reservation_group = QGroupBox("예매 정보")
        reservation_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        reservation_layout = QGridLayout()
        reservation_layout.setSpacing(8)
        
        # 역 목록
        stations = [
            "수서", "동탄", "평택지제", "천안아산", "대전", "공주", 
            "익산", "정읍", "광주송정", "나주", "목포",
            "김천구미", "서대구", "동대구", "경주", "울산(통도사)", 
            "부산", "마산", "창원", "진영", "진주"
        ]
        
        # 출발역/도착역
        self.dep_stn = QComboBox()
        self.arr_stn = QComboBox()
        self.dep_stn.addItems(stations)
        self.arr_stn.addItems(stations)
        self.dep_stn.setCurrentText("수서")
        self.arr_stn.setCurrentText("부산")
        
        combo_style = """
            QComboBox {
                padding: 8px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 1px solid #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
            }
        """
        self.dep_stn.setStyleSheet(combo_style)
        self.arr_stn.setStyleSheet(combo_style)
        
        # 날짜 선택
        current_date = QDate.currentDate()
        dates = []
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        for i in range(30):
            date = current_date.addDays(i)
            formatted_date = f"{date.toString('yyyy/MM/dd')}({weekdays[date.dayOfWeek() - 1]})"
            dates.append(formatted_date)
        self.date_select = QComboBox()
        self.date_select.addItems(dates)
        self.date_select.setStyleSheet(combo_style)
        self.date_select.setMaxVisibleItems(10)  # 드롭다운 최대 항목 수 제한
        
        # 시간 선택
        self.time_select = QComboBox()
        self.time_select.setStyleSheet(combo_style)
        
        # 좌석 유형
        seat_layout = QHBoxLayout()
        self.seat_type_group = QButtonGroup(self)
        self.special_seat = QRadioButton("특실")
        self.general_seat = QRadioButton("일반실")
        self.seat_type_group.addButton(self.special_seat)
        self.seat_type_group.addButton(self.general_seat)
        self.general_seat.setChecked(True)
        
        seat_layout.addWidget(self.special_seat)
        seat_layout.addWidget(self.general_seat)
        seat_layout.addStretch()
        
        # 레이아웃 구성
        reservation_layout.addWidget(QLabel("출발역:"), 0, 0)
        reservation_layout.addWidget(self.dep_stn, 0, 1)
        reservation_layout.addWidget(QLabel("도착역:"), 0, 2)
        reservation_layout.addWidget(self.arr_stn, 0, 3)
        
        reservation_layout.addWidget(QLabel("날짜:"), 1, 0)
        reservation_layout.addWidget(self.date_select, 1, 1)
        reservation_layout.addWidget(QLabel("시간:"), 1, 2)
        reservation_layout.addWidget(self.time_select, 1, 3)
        
        reservation_layout.addWidget(QLabel("좌석:"), 2, 0)
        reservation_layout.addLayout(seat_layout, 2, 1, 1, 3)
        
        reservation_group.setLayout(reservation_layout)
        layout.addWidget(reservation_group)
        
        # 날짜 변경 시 시간 업데이트
        self.date_select.currentIndexChanged.connect(self.update_time_options)
        
        layout.addStretch()
        parent.setLayout(layout)
    
    def setup_settings_tab(self, parent):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 검색 설정
        search_group = QGroupBox("검색 설정")
        search_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        search_layout = QGridLayout()
        search_layout.setSpacing(8)
        
        self.time_tolerance_input = QLineEdit()
        self.time_tolerance_input.setPlaceholderText("30")
        self.time_tolerance_input.setText("30")
        
        self.refresh_interval_input = QLineEdit()
        self.refresh_interval_input.setPlaceholderText("0.05")
        self.refresh_interval_input.setText("0.05")
        
        input_style = """
            QLineEdit {
                padding: 8px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #4CAF50;
            }
        """
        self.time_tolerance_input.setStyleSheet(input_style)
        self.refresh_interval_input.setStyleSheet(input_style)
        
        search_layout.addWidget(QLabel("허용 시간 범위:"), 0, 0)
        search_layout.addWidget(self.time_tolerance_input, 0, 1)
        time_help = QLabel("분 (예: 60 = 선택 시간부터 60분 이내)")
        time_help.setStyleSheet("color: #888888; font-size: 11px; font-weight: normal;")
        search_layout.addWidget(time_help, 0, 2)
        
        search_layout.addWidget(QLabel("새로고침 간격:"), 1, 0)
        search_layout.addWidget(self.refresh_interval_input, 1, 1)
        refresh_help = QLabel("초 (권장: 0.1초 이상)")
        refresh_help.setStyleSheet("color: #888888; font-size: 11px; font-weight: normal;")
        search_layout.addWidget(refresh_help, 1, 2)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # 자동화 정보
        info_group = QGroupBox("자동화 정보")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        info_layout = QVBoxLayout()
        
        info_text = QLabel("""
        • 엔진: Playwright (고성능 웹 자동화)
        • 브라우저: Chromium
        • 모드: 헤드리스 OFF (화면 표시)
        • 결제: 카카오페이 자동 연동
        """)
        info_text.setStyleSheet("""
            font-size: 12px;
            font-weight: normal;
            color: #e0e0e0;
            padding: 10px;
            background-color: #1e1e1e;
            border-radius: 3px;
        """)
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 저장된 정보
        saved_group = QGroupBox("저장된 정보")
        saved_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        saved_layout = QHBoxLayout()
        
        self.save_button = QPushButton("로그인 정보 저장")
        self.load_button = QPushButton("로그인 정보 불러오기")
        
        button_style = """
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
        """
        self.save_button.setStyleSheet(button_style)
        self.load_button.setStyleSheet(button_style)
        
        self.save_button.clicked.connect(self.save_login_info)
        self.load_button.clicked.connect(self.load_login_info)
        
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        saved_layout.addWidget(self.save_button)
        saved_layout.addWidget(self.load_button)
        saved_layout.addStretch()
        
        saved_group.setLayout(saved_layout)
        layout.addWidget(saved_group)
        
        layout.addStretch()
        parent.setLayout(layout)
    
    def update_time_options(self):
        """시간 선택 콤보박스의 옵션을 업데이트하는 함수"""
        from datetime import datetime
        
        # 현재 선택된 날짜
        selected_date_str = self.date_select.currentText().split('(')[0]
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y/%m/%d").date()
        except:
            # 날짜 파싱 실패 시 기본값 사용
            self.time_select.clear()
            for hour in range(0, 24, 2):
                self.time_select.addItem(f"{hour:02d}:00")
            return
        
        # 현재 시간
        current_time = datetime.now()
        current_date = current_time.date()
        
        # 시간 옵션 생성
        self.time_select.clear()
        
        if selected_date == current_date:
            # 오늘 날짜인 경우 현재 시간 이후만 표시
            current_hour = current_time.hour
            for hour in range(0, 24, 2):
                if hour >= current_hour:
                    self.time_select.addItem(f"{hour:02d}:00")
        else:
            # 다른 날짜는 모든 시간대 표시
            for hour in range(0, 24, 2):
                self.time_select.addItem(f"{hour:02d}:00")
        
        # 선택 가능한 시간이 없는 경우
        if self.time_select.count() == 0:
            self.time_select.addItem("선택 가능한 시간 없음")
            self.start_button.setEnabled(False)
        else:
            if hasattr(self, 'start_button'):
                self.start_button.setEnabled(True)
    
    def save_login_info(self):
        try:
            with open("login_info.txt", "w") as f:
                f.write(self.id_input.text())
            QMessageBox.information(self, "저장 완료", "로그인 정보가 저장되었습니다.")
        except Exception as e:
            QMessageBox.warning(self, "저장 실패", f"저장 중 오류 발생: {str(e)}")
    
    def load_login_info(self):
        try:
            if os.path.exists("login_info.txt"):
                with open("login_info.txt", "r") as f:
                    self.id_input.setText(f.read().strip())
                self.log_text.append("✅ 저장된 로그인 정보를 불러왔습니다.")
        except:
            pass
    
    def validate_inputs(self):
        if not self.id_input.text() or not self.phone_input.text() or not self.birth_input.text():
            QMessageBox.warning(self, "입력 오류", "모든 필수 정보를 입력해주세요.")
            return False
        
        if self.dep_stn.currentText() == self.arr_stn.currentText():
            QMessageBox.warning(self, "입력 오류", "출발역과 도착역이 동일합니다.")
            return False
        
        return True
    
    def start_reservation(self):
        if not self.validate_inputs():
            return
        
        login_info = {
            'id': self.id_input.text(),
            'password': self.pw_input.text(),
            'phone': self.phone_input.text(),
            'birth': self.birth_input.text()
        }
        
        personal_info = {
            'phone': self.phone_input.text(),
            'birth': self.birth_input.text()
        }
        
        train_info = {
            'departure': self.dep_stn.currentText(),
            'arrival': self.arr_stn.currentText(),
            'date': self.date_select.currentText(),  # 전체 문자열 전달 (요일 포함)
            'target_time': self.time_select.currentText().split(':')[0].zfill(2),  # 2자리로 패딩
            'time_tolerance': self.time_tolerance_input.text() or "30",  # 레거시와 동일하게 30
            'seat_types': {
                'special': self.special_seat.isChecked(),
                'general': self.general_seat.isChecked()
            },
            'passenger_count': 1,  # 1인 예매 고정
            'passenger_names': []  # 빈 리스트
        }
        
        settings = {
            'refresh_interval': self.refresh_interval_input.text() or "0.05"  # 레거시와 동일하게 0.05
        }
        
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        
        self.worker = SRTReservationWorker(login_info, train_info, personal_info, settings)
        self.worker.progress_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.reservation_finished)
        self.worker.start()
        
        self.start_button.setEnabled(False)
        self.reset_button.setEnabled(True)
        self.status_label.setText("🟢 실행중")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            padding: 5px 10px;
            background-color: #2b4c2b;
            border-radius: 10px;
            color: #4CAF50;
        """)
        self.log_text.clear()
        self.log_text.append("🚀 예매를 시작합니다...")
    
    def update_log(self, message):
        self.log_text.append(message)
        # 자동 스크롤
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def reservation_finished(self, success):
        self.progress_bar.hide()
        self.start_button.setEnabled(True)
        self.reset_button.setEnabled(False)
        
        if success:
            self.status_label.setText("✅ 완료")
            self.status_label.setStyleSheet("""
                font-size: 14px;
                padding: 5px 10px;
                background-color: #2b4c2b;
                border-radius: 10px;
                color: #4CAF50;
            """)
            QMessageBox.information(self, "예매 완료", "🎉 예매가 성공적으로 완료되었습니다!")
        else:
            self.status_label.setText("❌ 실패")
            self.status_label.setStyleSheet("""
                font-size: 14px;
                padding: 5px 10px;
                background-color: #4c2b2b;
                border-radius: 10px;
                color: #f44336;
            """)
            QMessageBox.warning(self, "예매 실패", "❌ 예매에 실패했습니다.")
    
    def reset_program(self):
        """프로그램 중단 - 비동기 처리로 UI 블로킹 방지"""
        self.log_text.append("⏹️ 중단 요청을 처리하는 중...")
        self.reset_button.setEnabled(False)  # 중복 클릭 방지
        
        # QTimer를 사용해 비동기로 처리
        QTimer.singleShot(0, self._do_reset)
    
    def _do_reset(self):
        """실제 중단 작업 수행"""
        try:
            if hasattr(self, 'worker') and self.worker.isRunning():
                # 워커에 중단 신호 보내기
                self.worker.stop()
                
                # 워커가 종료될 때까지 최대 0.5초 대기
                if not self.worker.wait(500):
                    # 강제 종료
                    self.worker.terminate()
                    self.worker.wait(100)
        except Exception as e:
            self.log_text.append(f"중단 중 오류: {str(e)}")
        finally:
            # UI 상태 업데이트
            self.progress_bar.hide()
            self.start_button.setEnabled(True)
            self.reset_button.setEnabled(False)
            self.status_label.setText("⚫ 중단됨")
            self.status_label.setStyleSheet("""
                font-size: 14px;
                padding: 5px 10px;
                background-color: #3c3c3c;
                border-radius: 10px;
                color: #999999;
            """)
            self.log_text.append("⏹️ 프로그램이 중단되었습니다.")
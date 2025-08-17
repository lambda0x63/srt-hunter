from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox, 
                           QGridLayout, QTextEdit, QProgressBar, QMessageBox, QHBoxLayout, QCheckBox, QRadioButton, QButtonGroup)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QDate
from PyQt6.QtGui import QFont
import qdarkstyle
import sys
from version import VERSION, AUTHOR, GITHUB_URL
import os

class SRTReservationWorker(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, login_info, train_info, personal_info, settings, use_playwright=False):
        super().__init__()
        self.login_info = login_info
        self.train_info = train_info
        self.personal_info = personal_info
        self.settings = settings
        self.use_playwright = use_playwright
        self.driver = None
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    def run(self):
        try:
            if self.use_playwright:
                # Playwright 버전 사용
                from srt_automation_v2 import setup_driver, start_reservation
                self.playwright, self.browser, self.context, self.page = setup_driver()
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
            else:
                # Selenium 버전 사용
                from srt_automation import setup_driver, start_reservation
                self.driver, wait = setup_driver()
                success = start_reservation(
                    self.driver, 
                    wait, 
                    self.login_info,
                    self.train_info,
                    self.personal_info,
                    self.settings,
                    self.progress_signal
                )
            self.finished_signal.emit(success)
        except Exception as e:
            self.progress_signal.emit(f"오류 발생: {str(e)}")
            self.finished_signal.emit(False)
        finally:
            if self.use_playwright:
                if self.browser:
                    try:
                        self.browser.close()
                    except:
                        pass
                if self.playwright:
                    try:
                        self.playwright.stop()
                    except:
                        pass
            else:
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT Ticket Hunter")
        self.setGeometry(100, 100, 1300, 850)
        
        # 다크 스타일 적용
        app = QApplication.instance()
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        
        # 메인 위젯 설정
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 메인 그리드 레이아웃으로 변경
        main_layout = QGridLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_widget.setLayout(main_layout)
        
        # 왼쪽 컬럼 레이아웃
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        
        # 오른쪽 컬럼 레이아웃
        right_column = QVBoxLayout()
        right_column.setSpacing(20)
        
        # 왼쪽 컬럼용 위젯
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        
        # 오른쪽 컬럼용 위젯
        right_widget = QWidget()
        right_widget.setLayout(right_column)
        
        # UI 구성요소 초기화 (2열 구조)
        self.init_ui(left_column, right_column)
        
        # 메인 그리드에 왼쪽/오른쪽 컬럼 추가
        main_layout.addWidget(left_widget, 0, 0)
        main_layout.addWidget(right_widget, 0, 1)
        
        # 초기 시간 옵션 설정
        self.update_time_options()
        
        # 저장된 로그인 정보 불러오기
        self.load_login_info()

    def setup_style(self):
        # 폰트 설정
        app = QApplication.instance()
        app.setFont(QFont('Pretendard', 10))
        
        # QDarkStyle 적용
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        
    def init_ui(self, left_column, right_column):
        # 로그인 그룹 (왼쪽 컬럼)
        login_group = QGroupBox("로그인 정보")
        login_layout = QGridLayout()
        login_layout.setSpacing(15)
        
        self.id_input = QLineEdit()
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.id_input.setPlaceholderText("SRT 회원번호를 입력하세요")
        self.pw_input.setPlaceholderText("SRT 비밀번호를 입력하세요")
        
        login_layout.addWidget(QLabel("회원번호"), 0, 0)
        login_layout.addWidget(self.id_input, 0, 1)
        login_layout.addWidget(QLabel("비밀번호"), 1, 0)
        login_layout.addWidget(self.pw_input, 1, 1)
        
        # 저장/불러오기 버튼 추가
        save_load_layout = QHBoxLayout()
        self.save_button = QPushButton("정보 저장")
        self.load_button = QPushButton("정보 불러오기")
        self.save_button.clicked.connect(self.save_login_info)
        self.load_button.clicked.connect(self.load_login_info)
        save_load_layout.addWidget(self.save_button)
        save_load_layout.addWidget(self.load_button)
        login_layout.addLayout(save_load_layout, 2, 0, 1, 2)
        
        login_group.setLayout(login_layout)
        left_column.addWidget(login_group)
        
        # 개인정보 그룹 (왼쪽 컬럼)
        personal_group = QGroupBox("결제 개인정보")
        personal_layout = QGridLayout()
        personal_layout.setSpacing(10)
        
        self.phone_input = QLineEdit()
        self.birth_input = QLineEdit()
        self.phone_input.setPlaceholderText("01012345678")
        self.birth_input.setPlaceholderText("990110")
        
        personal_layout.addWidget(QLabel("전화번호:"), 0, 0)
        personal_layout.addWidget(self.phone_input, 0, 1)
        personal_layout.addWidget(QLabel("생년월일:"), 1, 0)
        personal_layout.addWidget(self.birth_input, 1, 1)
        
        personal_group.setLayout(personal_layout)
        left_column.addWidget(personal_group)
        
        # 예매 정보 그룹 (오른쪽 컬럼)
        reservation_group = QGroupBox("예매 정보")
        reservation_layout = QGridLayout()
        reservation_layout.setSpacing(10)
        
        # 역 목록
        stations = [
            "수서", "동탄", "평택지제", "경주", "곡성", "공주", "광주송정", 
            "구례구", "김천구미", "나주", "남원", "대전", "동대구", "마산", 
            "목포", "밀양", "부산", "서대구", "순천", "여수EXPO", "여천", 
            "오송", "울산(통도사)", "익산", "전주", "정읍", "진영", "진주", 
            "창원", "창원중앙", "천안아산", "포항"
        ]
        
        # 출발역/도착역 콤보박스
        self.dep_stn = QComboBox()
        self.arr_stn = QComboBox()
        self.dep_stn.addItems(stations)
        self.arr_stn.addItems(stations)
        
        dep_label = QLabel("출발역:")
        arr_label = QLabel("도착역:")
        
        reservation_layout.addWidget(dep_label, 0, 0)
        reservation_layout.addWidget(self.dep_stn, 0, 1)
        reservation_layout.addWidget(arr_label, 1, 0)
        reservation_layout.addWidget(self.arr_stn, 1, 1)
        
        # 날짜 옵션 생성 (현재일부터 27일)
        current_date = QDate.currentDate()
        dates = []
        weekdays = ['월', '화', '수', '목', '금', '토', '일']
        for i in range(27):
            date = current_date.addDays(i)
            formatted_date = f"{date.toString('yyyy/MM/dd')}({weekdays[date.dayOfWeek() - 1]})"
            dates.append(formatted_date)
        self.date_select = QComboBox()
        self.date_select.addItems(dates)
        
        date_label = QLabel("날짜:")
        reservation_layout.addWidget(date_label, 2, 0)
        reservation_layout.addWidget(self.date_select, 2, 1)
        
        # 시간 선택
        self.time_select = QComboBox()
        time_label = QLabel("출발 시간:")
        reservation_layout.addWidget(time_label, 3, 0)
        reservation_layout.addWidget(self.time_select, 3, 1)
        
        # 날짜 선택 시 시간 옵션 업데이트
        self.date_select.currentIndexChanged.connect(self.update_time_options)
        
        reservation_group.setLayout(reservation_layout)
        right_column.addWidget(reservation_group)
        
        # 설정 그룹 (오른쪽 컬럼)
        settings_group = QGroupBox("상세 설정")
        settings_layout = QGridLayout()
        settings_layout.setSpacing(10)
        
        # 좌석 유형 선택 옵션 추가
        seat_type_label = QLabel("좌석 유형:")

        # 특실/일반실 선택을 위한 라디오 버튼 그룹
        self.seat_type_group = QButtonGroup(self)
        self.special_seat = QRadioButton("특실")
        self.general_seat = QRadioButton("일반실")
        self.seat_type_group.addButton(self.special_seat)
        self.seat_type_group.addButton(self.general_seat)

        # 일반실을 기본값으로 설정
        self.general_seat.setChecked(True)

        seat_type_layout = QHBoxLayout()
        seat_type_layout.addWidget(self.special_seat)
        seat_type_layout.addWidget(self.general_seat)
        
        settings_layout.addWidget(seat_type_label, 0, 0)
        settings_layout.addLayout(seat_type_layout, 0, 1)
        
        self.time_tolerance_input = QLineEdit()
        self.refresh_interval_input = QLineEdit()
        self.time_tolerance_input.setPlaceholderText("30")
        self.refresh_interval_input.setPlaceholderText("0.05")
        
        settings_layout.addWidget(QLabel("허용 시간 범위(분):"), 1, 0)
        settings_layout.addWidget(self.time_tolerance_input, 1, 1)
        settings_layout.addWidget(QLabel("새로고침 간격(초):"), 2, 0)
        settings_layout.addWidget(self.refresh_interval_input, 2, 1)
        
        # 인원수 선택 추가
        passenger_layout = QHBoxLayout()
        passenger_label = QLabel("인원수:")
        self.passenger_count = QComboBox()
        self.passenger_count.addItems([str(i) for i in range(1, 5)])  # 1-4명으로 제한
        passenger_layout.addWidget(passenger_label)
        passenger_layout.addWidget(self.passenger_count)
        settings_layout.addLayout(passenger_layout, 3, 0, 1, 2)
        
        # 동승자 정보 입력 필드 추가
        passenger_info_layout = QVBoxLayout()
        self.passenger_info_group = QGroupBox("동승자 정보")
        self.passenger_info_group.setVisible(False)  # 기본적으로 숨김 상태
        passenger_info_inner_layout = QGridLayout()

        self.passenger_names = []
        for i in range(3):  # 최대 3명의 동승자 (총 4명)
            name_label = QLabel(f"동승자 {i+1} 이름:")
            name_input = QLineEdit()
            name_input.setPlaceholderText("이름을 입력하세요")
            self.passenger_names.append(name_input)
            passenger_info_inner_layout.addWidget(name_label, i, 0)
            passenger_info_inner_layout.addWidget(name_input, i, 1)
            name_input.setVisible(False)  # 초기에는 모두 숨김

        self.passenger_info_group.setLayout(passenger_info_inner_layout)
        passenger_info_layout.addWidget(self.passenger_info_group)
        settings_layout.addLayout(passenger_info_layout, 7, 0, 1, 2)

        # 인원수 변경 시 동승자 정보 필드 표시/숨김 처리
        self.passenger_count.currentIndexChanged.connect(self.update_passenger_info_fields)
        
        # Playwright 사용 옵션 추가
        self.use_playwright_checkbox = QCheckBox("Playwright 엔진 사용 (V2)")
        self.use_playwright_checkbox.setToolTip("더 안정적인 Playwright 엔진을 사용합니다")
        settings_layout.addWidget(self.use_playwright_checkbox, 8, 0, 1, 2)
        
        # 도움말 텍스트 추가 - 위치 조정
        help_text = QLabel("* 허용 시간 범위: 선택한 시간부터 해당 시간만큼 이후까지 예매를 시도 (예: 14시 선택, 30분 설정시 14:00~14:30)")
        help_text.setWordWrap(True)  # 긴 텍스트 자동 줄바꿈
        settings_layout.addWidget(help_text, 4, 0, 1, 2)
        
        refresh_help = QLabel("* 새로고침 간격: 0.05 ~ 0.1초 권장")
        refresh_help.setWordWrap(True)
        settings_layout.addWidget(refresh_help, 5, 0, 1, 2)
        
        # 다인 예매 도움말 추가
        multi_help = QLabel("* 다인 예매: SRT 시스템이 자동으로 최적 좌석 배정 (2-4인)")
        multi_help.setWordWrap(True)
        settings_layout.addWidget(multi_help, 6, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        right_column.addWidget(settings_group)
        
        # 진행 상태 표시 (오른쪽 컬럼)
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        right_column.addWidget(self.progress_bar)
        
        # 실행 버튼 (오른쪽 컬럼)
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("예매 시작")
        self.start_button.clicked.connect(self.start_reservation)
        button_layout.addWidget(self.start_button)
        
        # 중단 및 초기화 버튼 추가
        self.reset_button = QPushButton("중단 및 초기화")
        self.reset_button.setStyleSheet("background-color: #d9534f; color: white;")  # 빨간색 스타일
        self.reset_button.clicked.connect(self.reset_program)
        button_layout.addWidget(self.reset_button)
        
        right_column.addLayout(button_layout)
        
        # 로그 표시 영역 (왼쪽 컬럼)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        left_column.addWidget(self.log_text)
        
        # 버전 정보 표시 - version.py에서 정보 가져오기
        dev_info = QLabel(f"SRT Hunter v{VERSION} | Developed by {AUTHOR} | GitHub: {GITHUB_URL}")
        dev_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_info.setStyleSheet("color: gray;")
        left_column.addWidget(dev_info)

    def update_time_options(self):
        """시간 선택 콤보박스의 옵션을 업데이트하는 함수"""
        from datetime import datetime, timedelta
        
        # 현재 선택된 날짜
        selected_date_str = self.date_select.currentText().split('(')[0]
        selected_date = datetime.strptime(selected_date_str, "%Y/%m/%d").date()
        
        # 현재 시간
        current_time = datetime.now()
        current_date = current_time.date()
        
        # 시간 옵션 생성 (0시부터 22시까지 2시간 간격)
        self.time_select.clear()
        
        if selected_date == current_date:
            # 현재 시간대부터 표시
            current_hour = current_time.hour
            
            for hour in range(0, 23, 2):
                self.time_select.addItem(f"{hour:02d}:00")
        else:
            # 다른 날짜는 모든 시간대 표시
            for hour in range(0, 23, 2):
                self.time_select.addItem(f"{hour:02d}:00")
        
        # 선택 가능한 시간이 없는 경우
        if self.time_select.count() == 0:
            self.time_select.addItem("선택 가능한 시간 없음")
            self.start_button.setEnabled(False)
        else:
            self.start_button.setEnabled(True)

    def update_passenger_info_fields(self):
        """인원수에 따라 동승자 정보 입력 필드를 표시/숨김"""
        count = int(self.passenger_count.currentText())
        
        # 2명 이상일 때만 동승자 정보 그룹 표시
        self.passenger_info_group.setVisible(count > 1)
        
        # 필요한 수의 동승자 필드만 표시
        for i, name_input in enumerate(self.passenger_names):
            name_input.setVisible(i < count - 1)
            if i < count - 1:
                name_input.setPlaceholderText(f"동승자 {i+1} 이름")
            else:
                name_input.clear()  # 숨겨진 필드는 내용 삭제

    def start_reservation(self):
        if not self.validate_inputs():
            return
            
        # 날짜 문자열 그대로 사용 (예: "2024/01/01(월)")
        date_str = self.date_select.currentText()
        
        # 시간 값을 2자리 숫자로 변환 (예: "8:00" -> "08")
        time_str = self.time_select.currentText().split(':')[0].zfill(2)
        
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
        
        # 동승자 정보 추가
        passenger_names = []
        count = int(self.passenger_count.currentText())
        if count > 1:
            for i in range(count - 1):
                if i < len(self.passenger_names):
                    passenger_names.append(self.passenger_names[i].text())
        
        train_info = {
            'departure': self.dep_stn.currentText(),
            'arrival': self.arr_stn.currentText(),
            'date': date_str,
            'target_time': time_str,
            'time_tolerance': self.time_tolerance_input.text() or "30",
            'seat_types': {
                'special': self.special_seat.isChecked(),
                'general': self.general_seat.isChecked()
            },
            'passenger_count': count,
            'passenger_names': passenger_names
        }
        
        settings = {
            'refresh_interval': self.refresh_interval_input.text() or "0.05"
        }
        
        # 진행 상태 표시 초기화
        self.progress_bar.setRange(0, 0)  # 불확정 프로그레스 바
        self.progress_bar.show()
        
        # 워커 스레드 시작 (Playwright 옵션 포함)
        use_playwright = self.use_playwright_checkbox.isChecked()
        self.worker = SRTReservationWorker(login_info, train_info, personal_info, settings, use_playwright)
        self.worker.progress_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.reservation_finished)
        self.worker.start()
        
        # UI 상태 변경
        self.start_button.setEnabled(False)

    def validate_inputs(self):
        if not self.id_input.text() or not self.phone_input.text() or not self.birth_input.text():
            QMessageBox.warning(self, "입력 오류", "아이디와 전화번호, 생년월일을 입력해주세요.")
            return False
        if self.dep_stn.currentText() == self.arr_stn.currentText():
            QMessageBox.warning(self, "입력 오류", "출발역과 도착역이 동일합니다.")
            return False
        
        # 좌석 유형 검증
        if not (self.special_seat.isChecked() or self.general_seat.isChecked()):
            QMessageBox.warning(self, "입력 오류", "좌석 유형(특실/일반실)을 선택해주세요.")
            return False
            
        # 전화번호 형식 검사
        phone = self.phone_input.text()
        if not phone.isdigit() or len(phone) != 11:
            QMessageBox.warning(self, "입력 오류", "전화번호는 11자리 숫자로 입력해주세요.")
            return False
            
        # 생년월일 형식 검사
        birth = self.birth_input.text()
        if not birth.isdigit() or len(birth) != 6:
            QMessageBox.warning(self, "입력 오류", "생년월일은 6자리 숫자로 입력해주세요.")
            return False
            
        # 허용 시간 범위 검사
        try:
            time_tolerance = float(self.time_tolerance_input.text() or "30")
            if time_tolerance <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "허용 시간 범위는 양수여야 합니다.")
            return False
            
        # 새로고침 간격 검사
        try:
            refresh_interval = float(self.refresh_interval_input.text() or "0.05")
            if refresh_interval <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "새로고침 간격은 양수여야 합니다.")
            return False

        # 인원수가 2명 이상일 때 동승자 이름 검증
        passenger_count = int(self.passenger_count.currentText())
        if passenger_count > 1:
            for i in range(passenger_count - 1):
                if not self.passenger_names[i].text().strip():
                    QMessageBox.warning(self, "입력 오류", f"동승자 {i+1}의 이름을 입력해주세요.")
                    return False
        
        # 날짜와 시간 검증
        from datetime import datetime, timedelta
        current_time = datetime.now()
        
        # 선택된 날짜 파싱 (예: "2024/12/28(토)" -> datetime)
        selected_date_str = self.date_select.currentText().split('(')[0]  # "2024/12/28" 추출
        selected_time_str = self.time_select.currentText()  # "HH:00" 형식
        
        selected_datetime = datetime.strptime(
            f"{selected_date_str} {selected_time_str}",
            "%Y/%m/%d %H:%M"
        )

        if selected_datetime.date() == current_time.date():
            current_hour_block = (current_time.hour // 2) * 2
            selected_hour = selected_datetime.hour
            
            if selected_hour < current_hour_block - 2:
                QMessageBox.warning(
                    self,
                    "입력 오류",
                    "선택한 시간대가 너무 이전입니다.\n현재 시간 근처의 시간대를 선택해주세요."
                )
                return False
            
        return True

    def update_log(self, message):
        self.log_text.append(message)

    def reservation_finished(self, success):
        self.start_button.setEnabled(True)
        self.progress_bar.hide()
        
        if success:
            QMessageBox.information(self, "예매 완료", "예매가 성공적으로 완료되었습니다!")
            self.update_log("예매가 완료되었습니다!")
        else:
            QMessageBox.warning(self, "예매 실패", "예매에 실패했습니다. 로그를 확인해주세요.")
            self.update_log("예매에 실패했습니다.")

    def save_login_info(self):
        try:
            # 비밀번호를 제외한 정보만 저장
            info = {
                'id': self.id_input.text(),
                'phone': self.phone_input.text(),
                'birth': self.birth_input.text()
            }
            
            # 스크립트 실행 디렉토리를 기준으로 절대 경로 사용
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login_info.txt')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{info['id']}\n")
                f.write(f"{info['phone']}\n")
                f.write(f"{info['birth']}\n")
            
            QMessageBox.information(self, "저장 완료", "로그인 정보가 저장되었습니다. (비밀번호 제외)")
            self.update_log(f"로그인 정보가 저장되었습니다: {file_path}")
        except Exception as e:
            QMessageBox.warning(self, "저장 오류", f"정보 저장 중 오류 발생: {str(e)}")
            self.update_log(f"정보 저장 중 오류 발생: {str(e)}")

    def load_login_info(self):
        try:
            # 스크립트 실행 디렉토리를 기준으로 절대 경로 사용
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'login_info.txt')
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) >= 3:  # 최소 3줄 (ID, 전화번호, 생년월일)
                        self.id_input.setText(lines[0].strip())
                        self.phone_input.setText(lines[1].strip())
                        self.birth_input.setText(lines[2].strip())
                        self.update_log("저장된 로그인 정보를 불러왔습니다. (비밀번호는 직접 입력해주세요)")
                        return
                self.update_log("저장된 로그인 정보가 불충분합니다.")
            else:
                self.update_log("저장된 로그인 정보 파일이 없습니다.")
        except Exception as e:
            QMessageBox.warning(self, "불러오기 오류", f"저장된 정보를 불러오는 중 오류 발생: {str(e)}")
            self.update_log(f"저장된 정보를 불러오는 중 오류 발생: {str(e)}")

    def reset_program(self):
        # 사용자에게 확인 메시지
        reply = QMessageBox.question(self, '초기화', 
                                     '진행 중인 모든 작업을 중단하고 초기화하시겠습니까?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.No:
            return
            
        # 진행 중인 작업이 있는지 확인
        if hasattr(self, 'worker') and self.worker.isRunning():
            try:
                # 드라이버 종료 시도
                if hasattr(self.worker, 'driver') and self.worker.driver:
                    try:
                        self.worker.driver.quit()
                    except:
                        pass
                
                # 쓰레드 종료
                self.worker.terminate()
                self.worker.wait(1000)  # 최대 1초 대기
                
                # 강제 종료가 필요한 경우
                if self.worker.isRunning():
                    self.worker.quit()
                    
                self.update_log("작업이 강제 중단되었습니다.")
            except Exception as e:
                self.update_log(f"작업 중단 중 오류 발생: {str(e)}")
                
        # UI 초기화
        self.progress_bar.hide()
        self.start_button.setEnabled(True)
        
        # 로그 초기화
        self.log_text.clear()
        self.update_log("프로그램이 초기화되었습니다.")
        
        # 시간 옵션 초기화
        self.update_time_options() 
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QLabel, QLineEdit, QComboBox, QPushButton, QGroupBox, 
                           QGridLayout, QTextEdit, QProgressBar, QMessageBox, QHBoxLayout, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QDate
from PyQt6.QtGui import QFont
import qdarkstyle
import sys
from srt_automation import *

class SRTReservationWorker(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, login_info, train_info, personal_info, settings):
        super().__init__()
        self.login_info = login_info
        self.train_info = train_info
        self.personal_info = personal_info
        self.settings = settings
        self.driver = None
        
    def run(self):
        try:
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
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRT Ticket Hunter")
        self.setGeometry(100, 100, 1300, 700)
        
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
        self.special_seat = QCheckBox("특실")
        self.general_seat = QCheckBox("일반실")
        self.standing_seat = QCheckBox("입석+좌석")
        
        seat_type_layout = QHBoxLayout()
        seat_type_layout.addWidget(self.special_seat)
        seat_type_layout.addWidget(self.general_seat)
        seat_type_layout.addWidget(self.standing_seat)
        
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
        
        # 도움말 텍스트 추가
        help_text = QLabel("* 허용 시간 범위: 선택한 시간부터 해당 시간만큼 이후까지 예매를 시도 (예: 14시 선택, 30분 설정시 14:00~14:30)")
        help_text.setWordWrap(True)  # 긴 텍스트 자동 줄바꿈
        settings_layout.addWidget(help_text, 3, 0, 1, 2)
        
        refresh_help = QLabel("* 새로고침 간격: 0.05 ~ 0.1초 권장")
        refresh_help.setWordWrap(True)
        settings_layout.addWidget(refresh_help, 4, 0, 1, 2)
        
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
        right_column.addLayout(button_layout)
        
        # 로그 표시 영역 (왼쪽 컬럼)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        left_column.addWidget(self.log_text)
        
        dev_info = QLabel("SRT Hunter v1.1.0 | Developed by faith6 | GitHub: https://github.com/root39293/srt-hunter")
        dev_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_info.setStyleSheet("color: gray;")
        left_column.addWidget(dev_info)
        
        # 초기 시간 옵션 설정
        self.update_time_options()

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

    def start_reservation(self):
        if not self.validate_inputs():
            return
            
        # 날짜 문자열 그대로 사용 (예: "2024/01/01(월)")
        date_str = self.date_select.currentText()
        
        # 시간 값을 2자리 숫자로 변환 (예: "8:00" -> "08")
        time_str = self.time_select.currentText().split(':')[0].zfill(2)
        
        login_info = {
            'id': self.id_input.text(),
            'password': self.pw_input.text()
        }
        
        personal_info = {
            'phone': self.phone_input.text(),
            'birth': self.birth_input.text()
        }
        
        train_info = {
            'departure': self.dep_stn.currentText(),
            'arrival': self.arr_stn.currentText(),
            'date': date_str,
            'target_time': time_str,
            'time_tolerance': self.time_tolerance_input.text() or "30",
            'seat_types': {
                'special': self.special_seat.isChecked(),
                'general': self.general_seat.isChecked(),
                'standing': self.standing_seat.isChecked()
            }
        }
        
        settings = {
            'refresh_interval': self.refresh_interval_input.text() or "0.05"
        }
        
        # 진행 상태 표시 초기화
        self.progress_bar.setRange(0, 0)  # 불확정 프로그레스 바
        self.progress_bar.show()
        
        # 워커 스레드 시작
        self.worker = SRTReservationWorker(login_info, train_info, personal_info, settings)
        self.worker.progress_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.reservation_finished)
        self.worker.start()
        
        # UI 상태 변경
        self.start_button.setEnabled(False)

    def validate_inputs(self):
        if not self.id_input.text() or not self.pw_input.text():
            QMessageBox.warning(self, "입력 오류", "아이디와 비밀번호를 입력해주세요.")
            return False
        if not self.phone_input.text() or not self.birth_input.text():
            QMessageBox.warning(self, "입력 오류", "전화번호와 생년월일을 입력해주세요.")
            return False
        if self.dep_stn.currentText() == self.arr_stn.currentText():
            QMessageBox.warning(self, "입력 오류", "출발역과 도착역이 동일합니다.")
            return False
        
        # 좌석 유형 검증
        if not (self.special_seat.isChecked() or self.general_seat.isChecked() or self.standing_seat.isChecked()):
            QMessageBox.warning(self, "입력 오류", "최소한 하나의 좌석 유형을 선택해주세요.")
            return False
            
        # 일반실이 선택되지 않았는데 입석+좌석이 선택된 경우
        if not self.general_seat.isChecked() and self.standing_seat.isChecked():
            QMessageBox.warning(self, "입력 오류", "입석+좌석은 일반실이 선택된 경우에만 선택할 수 있습니다.")
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
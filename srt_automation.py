from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
import time
import os

def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    return driver, wait

def parse_train_info(row):
    """
    열차 정보를 파싱하는 함수
    """
    try:
        cols = row.find_elements(By.TAG_NAME, "td")
        train_type = cols[1].text.split('\n')[0]  # SRT (첫 줄만)
        train_number = cols[2].text.strip()  # 열차번호
        dep_time = cols[3].find_element(By.CLASS_NAME, "time").text  # 출발시간
        arr_time = cols[4].find_element(By.CLASS_NAME, "time").text  # 도착시간
        
        # 특실 예약 버튼 찾기
        special_button = None
        special_spans = cols[5].find_elements(By.CSS_SELECTOR, "a[href='#none'] span")
        if special_spans and special_spans[0].text == "예약하기":
            special_button = special_spans[0].find_element(By.XPATH, "./..")
        
        # 일반실 예약 버튼 찾기
        general_button = None
        standing_button = None
        general_spans = cols[6].find_elements(By.CSS_SELECTOR, "a[href='#none'] span")
        for span in general_spans:
            if span.text == "예약하기":
                general_button = span.find_element(By.XPATH, "./..")
            elif span.text == "입석+좌석":
                standing_button = span.find_element(By.XPATH, "./..")
        
        return {
            'type': train_type,
            'number': train_number,
            'dep_time': dep_time,
            'arr_time': arr_time,
            'special_button': special_button,
            'general_button': general_button,
            'standing_button': standing_button
        }
    except Exception as e:
        print(f"열차 정보 파싱 중 오류: {str(e)}")
        return None

def time_diff_minutes(time1, time2):
    """
    두 시간의 차이를 분으로 계산 (time1, time2는 "HH:MM" 형식)
    """
    h1, m1 = map(int, time1.split(':'))
    h2, m2 = map(int, time2.split(':'))
    return abs((h1 * 60 + m1) - (h2 * 60 + m2))

def find_available_train(driver, wait, target_time, time_tolerance, seat_types):
    """
    허용 시간 내의 예약 가능한 열차를 찾는 함수
    """
    try:
        # 조회 결과 테이블 찾기
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody")))
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        available_trains = []
        target_time_str = f"{target_time}:00"  # "08:00" 형식으로 변환
        
        for row in rows:
            train_info = parse_train_info(row)
            if not train_info:
                continue
                
            # SRT만 선택
            if train_info['type'] != 'SRT':
                continue
                
            # 허용 시간 범위 내에 있는지 확인
            time_difference = time_diff_minutes(target_time_str, train_info['dep_time'])
            if time_difference > time_tolerance:
                continue
                
            # 선택된 좌석 유형에 따라 예약 가능 여부 확인
            available_buttons = []
            
            if seat_types['special'] and train_info['special_button']:
                available_buttons.append(('특실', train_info['special_button']))
                
            if seat_types['general'] and train_info['general_button']:
                available_buttons.append(('일반실', train_info['general_button']))
                
            if seat_types['standing'] and train_info['standing_button']:
                available_buttons.append(('입석+좌석', train_info['standing_button']))
                
            if available_buttons:
                train_info['time_diff'] = time_difference
                train_info['available_buttons'] = available_buttons
                available_trains.append(train_info)
        
        # 시간 차이가 가장 적은 열차 선택
        if available_trains:
            best_train = min(available_trains, key=lambda x: x['time_diff'])
            # 선택된 좌석 유형 중 가장 우선순위가 높은 것 선택 (특실 > 일반실 > 입석+좌석)
            best_train['reserve_button'] = best_train['available_buttons'][0][1]
            return best_train
        
        return None
        
    except Exception as e:
        print(f"열차 검색 중 오류: {str(e)}")
        return None

def search_and_reserve(driver, wait, login_info, train_info, settings, personal_info, progress_signal=None):
    def log(message):
        if progress_signal:
            progress_signal.emit(message)
        print(message)
        
    while True:
        try:
            # 조회하기 버튼 클릭
            log("\n새로운 검색 시도...")
            search_button = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[2]/input")))
            
            # JavaScript로 클릭 실행
            driver.execute_script("arguments[0].click();", search_button)
            log("조회하기 버튼 클릭 완료")
            
            time.sleep(1)  # 검색 결과 로딩 대기
            
            # 허용 시간 내의 예약 가능한 열차 찾기
            target_time = train_info['target_time']
            time_tolerance = int(train_info['time_tolerance'])
            seat_types = train_info['seat_types']
            available_train = find_available_train(driver, wait, target_time, time_tolerance, seat_types)
            
            if available_train:
                log(f"\n예약 가능한 열차를 찾았습니다!")
                log(f"열차번호: {available_train['number']}")
                log(f"출발시간: {available_train['dep_time']}")
                log(f"도착시간: {available_train['arr_time']}")
                
                # 예약하기 버튼 클릭
                available_train['reserve_button'].click()
                log("예약하기 버튼 클릭 완료")
                
                # 입석+좌석 선택 시 발생하는 alert 처리
                try:
                    alert = driver.switch_to.alert
                    alert_text = alert.text
                    if "입석+좌석 승차권은 '스마트폰 발권'이 불가합니다" in alert_text:
                        alert.accept()
                        log("입석+좌석 안내 확인")
                except:
                    pass  # alert가 없는 경우 무시
                
                # 결제하기 버튼 클릭
                quick_wait = WebDriverWait(driver, 5)
                payment_button = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div/div[4]/div/div[2]/form/fieldset/div[11]/a[1]")))
                payment_button.click()
                log("결제하기 버튼 클릭 완료")

                # 간편결제 탭 클릭
                easy_payment_tab = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[2]/ul/li[2]/a")))
                easy_payment_tab.click()
                log("간편결제 탭 클릭 완료")

                # 카카오페이 버튼 클릭
                kakao_pay_button = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[6]/div[1]/table/tbody/tr/td/div/input[3]")))
                kakao_pay_button.click()
                log("카카오페이 선택 완료")

                # 스마트폰 발권 옵션 클릭
                smartphone_ticket = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[11]/div[2]/ul/li[2]/a")))
                smartphone_ticket.click()
                log("스마트폰 발권 옵션 선택 완료")

                # alert 창 처리
                time.sleep(1)  # alert 창이 나타날 때까지 잠시 대기
                alert = driver.switch_to.alert
                alert.accept()
                log("알림창 확인 클릭 완료")

                # 결제 및 발권 버튼 클릭
                final_payment_button = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[11]/div[11]/input[2]")))
                final_payment_button.click()
                log("결제 및 발권 버튼 클릭 완료")

                # 새 창으로 전환
                time.sleep(2)  # 새 창이 열릴 때까지 대기
                windows = driver.window_handles
                driver.switch_to.window(windows[-1])  # 마지막으로 열린 창으로 전환
                log("카카오페이 결제창으로 전환 완료")

                # 카톡결제 버튼 클릭
                kakao_talk_pay = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div/main/div/div[1]/div[4]/span")))
                kakao_talk_pay.click()
                log("카톡결제 버튼 클릭 완료")

                # 휴대폰 번호 입력
                phone_input = quick_wait.until(EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[1]/main/div/div[2]/div/div[2]/form/div[1]/div/div/span/input")))
                phone_input.clear()
                phone_input.send_keys(personal_info['phone'])
                log("휴대폰 번호 입력 완료")

                # 생년월일 입력
                birth_input = quick_wait.until(EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[1]/main/div/div[2]/div/div[2]/form/div[2]/div/div/span/input")))
                birth_input.clear()
                birth_input.send_keys(personal_info['birth'])
                log("생년월일 입력 완료")

                # 최종 결제요청 버튼 클릭
                final_request_button = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/main/div/div[2]/div/div[2]/form/button")))
                final_request_button.click()
                log("최종 결제요청 완료")

                # 결제 완료될 때까지 대기 (최대 600초 = 10분)
                payment_wait = WebDriverWait(driver, 600)
                try:
                    # 휴대폰 결제 확인 화면이 나타날 때까지 대기
                    payment_wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(text(), '휴대폰에서 카카오페이 결제후,')]")))
                    log("휴대폰에서 카카오페이 결제를 진행해주세요. (제한시간: 10분)")
                    
                    # 결제가 완료될 때까지 계속 대기
                    while True:
                        try:
                            # 현재 URL이 SRT 도메인으로 변경되었는지 확인
                            current_url = driver.current_url
                            if "srail.kr" in current_url:
                                log("결제가 완료되었습니다!")
                                break
                            time.sleep(1)
                        except:
                            time.sleep(1)
                except TimeoutException:
                    log("결제 시간이 초과되었습니다. (10분 경과)")
                    # 계속 대기
                    while True:
                        try:
                            current_url = driver.current_url
                            if "srail.kr" in current_url:
                                log("결제가 완료되었습니다!")
                                break
                            time.sleep(1)
                        except:
                            time.sleep(1)

                return True
            
            log("예약 가능한 열차가 없습니다. 잠시 후 다시 시도합니다...")
            time.sleep(float(settings['refresh_interval']))
                
        except Exception as e:
            log(f"검색 중 오류 발생: {str(e)}")
            if "Connection aborted" in str(e) or "Failed to establish" in str(e):
                log("브라우저 연결이 종료되었습니다.")
                return False
            time.sleep(float(settings['refresh_interval']))

def start_reservation(driver, wait, login_info, train_info, personal_info, settings, progress_signal=None):
    def log(message):
        if progress_signal:
            progress_signal.emit(message)
        print(message)
        
    try:
        # 1. 로그인 페이지로 이동
        log("로그인 페이지로 이동 중...")
        driver.get("https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000")
        time.sleep(0.5)
        
        # 2. 로그인 정보 입력
        member_id = login_info['id']
        member_pw = login_info['password']
        
        log("로그인 시도 중...")
        id_input = wait.until(EC.presence_of_element_located((By.ID, "srchDvNm01")))
        id_input.clear()
        id_input.send_keys(member_id)
        
        pw_input = driver.find_element(By.ID, "hmpgPwdCphd01")
        pw_input.clear()
        pw_input.send_keys(member_pw)
        
        # 3. 로그인 버튼 클릭
        submit_button = driver.find_element(
            By.CSS_SELECTOR, "input.submit.btn_pastel2.loginSubmit[type='submit']")
        submit_button.click()
        
        # 4. 로그인 성공 확인
        try:
            wait.until(EC.url_changes("https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000"))
            log("로그인 성공!")
            
            # 메인 창을 제외한 다른 탭 닫기
            main_window = driver.current_window_handle
            for handle in driver.window_handles:
                if handle != main_window:
                    driver.switch_to.window(handle)
                    driver.close()
            driver.switch_to.window(main_window)
            log("추가 탭 정리 완료")
            
            # 5. 일반승차권 조회 페이지로 이동
            log("일반승차권 조회 페이지로 이동 중...")
            driver.get("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000")
            time.sleep(0.5)
            
            # 6. 출발역 입력
            dep_stn = train_info['departure']
            log(f"출발역 입력 시도: {dep_stn}")
            dep_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[1]/div/div/div[1]/input")))
            dep_input.clear()
            dep_input.send_keys(dep_stn)
            log("출발역 입력 완료")
            
            time.sleep(0.3)
            
            # 7. 도착역 입력
            arr_stn = train_info['arrival']
            log(f"도착역 입력 시도: {arr_stn}")
            arr_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[1]/div/div/div[2]/input")))
            arr_input.clear()
            arr_input.send_keys(arr_stn)
            log("도착역 입력 완료")
            
            time.sleep(0.3)
            
            # 8. 날짜 선택
            date = train_info['date']
            log(f"날짜 선택 시도: {date}")
            
            # 날짜 드롭다운 클릭
            date_select = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "select[name='dptDt']")))  # name 속성으로 선택
            date_select.click()
            time.sleep(0.3)
            
            # 날짜 옵션 선택 - Select 클래스 사용
            date_selector = Select(date_select)
            date_selector.select_by_visible_text(date)
            log("날짜 선택 완료")
            
            time.sleep(0.3)
            
            # 9. 시간 선택
            target_time = train_info['target_time']
            log(f"시간 선택 시도: {target_time}시")
            
            # 시간 드롭다운 클릭
            time_select = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "select[name='dptTm']")))
            time_select.click()
            time.sleep(0.3)
            
            # 시간 옵션 선택 - Select 클래스 사용
            time_selector = Select(time_select)
            time_selector.select_by_value(f"{target_time}0000")  # 시간값에 0000 추가 (예: 080000)
            log("시간 선택 완료")
            
            time.sleep(0.3)
            
            # 10. 조회 및 예약 시도
            return search_and_reserve(driver, wait, login_info, train_info, settings, personal_info, progress_signal)
            
        except TimeoutException:
            log("로그인 실패: 아이디나 비밀번호를 확인해주세요.")
            return False
            
    except Exception as e:
        log(f"오류 발생: {str(e)}")
        import traceback
        log(f"상세 오류 정보:\n{traceback.format_exc()}")
        return False

def main():
    try:
        print("이 스크립트는 직접 실행하지 않고 GUI를 통해 실행해주세요.")
        print("python main.py를 실행하여 GUI를 시작하세요.")
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 
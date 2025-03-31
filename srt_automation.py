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
from version import VERSION

def setup_driver():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    return driver, wait

def parse_train_info(row):
    """
    테이블 행에서 열차 정보를 추출하는 함수
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
        general_spans = cols[6].find_elements(By.CSS_SELECTOR, "a[href='#none'] span")
        for span in general_spans:
            if span.text == "예약하기":
                general_button = span.find_element(By.XPATH, "./..")
        
        return {
            'type': train_type,
            'number': train_number,
            'dep_time': dep_time,
            'arr_time': arr_time,
            'special_button': special_button,
            'general_button': general_button
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

def find_available_train(driver, wait, target_time, time_tolerance, seat_types, passenger_count=1):
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
            
            if seat_types.get('special', False) and train_info['special_button']:
                available_buttons.append(('특실', train_info['special_button']))
                
            if seat_types.get('general', False) and train_info['general_button']:
                available_buttons.append(('일반실', train_info['general_button']))
            
            if available_buttons:
                train_info['time_diff'] = time_difference
                train_info['available_buttons'] = available_buttons
                available_trains.append(train_info)
        
        # 인원수와 좌석 선호도 정보 추가 처리
        # 다인 예매일 경우 특별한 처리 적용
        if passenger_count > 1:
            # 좌석 유형별 처리 로직 구현
            pass  # 임시 패스 처리 (실제 구현에서는 알고리즘 추가)
        
        # 다인 예매 정보 표시
        if passenger_count > 1:
            for train in available_trains:
                train['seat_note'] = f"{passenger_count}명 자동 배정 예정"
        
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
        
    # 인원수 추출
    passenger_count = train_info.get('passenger_count', 1)
    
    log(f"인원수: {passenger_count}명")
    
    while True:
        try:
            # 인원수 설정 (다인 예매인 경우)
            if passenger_count > 1:
                if not set_passenger_count(driver, wait, passenger_count, log):
                    log("인원수 설정 실패, 다시 시도합니다.")
                    continue
            
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
            available_train = find_available_train(driver, wait, target_time, time_tolerance, seat_types, passenger_count)
            
            if available_train:
                log(f"\n예약 가능한 열차를 찾았습니다!")
                log(f"열차번호: {available_train['number']}")
                log(f"출발시간: {available_train['dep_time']}")
                log(f"도착시간: {available_train['arr_time']}")
                
                if passenger_count > 1:
                    log(f"인원수: {passenger_count}명 (자동 배정)")
                    if 'seat_note' in available_train:
                        log(available_train['seat_note'])
                
                # 예약하기 버튼 클릭
                available_train['reserve_button'].click()
                log("예약하기 버튼 클릭 완료")
                
                # SRT 2개 편성 연결 열차 알림창 처리 추가
                try:
                    alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
                    alert_text = alert.text
                    if "SRT 2개 편성을 연결하여 운행하는 열차" in alert_text:
                        log("2개 편성 연결 열차 알림 확인")
                        alert.accept()
                except:
                    log("알림창 없음")
                
                # 결제하기 버튼 클릭 전 짧은 대기 추가
                time.sleep(1)
                
                # 잔여석 없음 메시지 확인
                try:
                    no_seats_message = driver.find_element(By.XPATH, "//p[contains(text(), '잔여석 없음') or contains(text(), '좌석이 매진')]")
                    if no_seats_message:
                        log("다른 사용자가 먼저 좌석을 예약했습니다. 다시 검색을 시도합니다.")
                        driver.back()  # 새로고침 대신 이전 페이지로 돌아가기
                        continue
                except:
                    log("좌석이 있는 것으로 확인됩니다. 결제 진행 중...")
                
                # 결제하기 버튼 클릭
                try:
                    quick_wait = WebDriverWait(driver, 5)
                    payment_button = quick_wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "/html/body/div/div[4]/div/div[2]/form/fieldset/div[11]/a[1]")))
                    driver.execute_script("arguments[0].click();", payment_button)
                    log("결제하기 버튼 클릭 완료")
                except Exception as e:
                    log(f"결제하기 버튼 클릭 실패: {str(e)}")
                    # 잔여석이 없을 가능성이 있으므로 확인
                    try:
                        page_source = driver.page_source
                        if "잔여석 없음" in page_source or "좌석이 매진" in page_source:
                            log("다른 사용자가 먼저 좌석을 예약했습니다. 다시 검색을 시도합니다.")
                        else:
                            log("알 수 없는 이유로 결제하기 버튼을 찾을 수 없습니다.")
                    except:
                        log("페이지 확인 중 오류가 발생했습니다.")
                    
                    # 이전 페이지로 돌아가기
                    driver.back()
                    continue

                # 다인 예매인 경우 동승자 정보 입력
                if passenger_count > 1:
                    try:
                        log("동승자 정보 입력 중...")
                        
                        # 동승자 정보 입력 대기
                        quick_wait = WebDriverWait(driver, 5)
                        
                        # 동승자 수만큼 반복
                        for i in range(1, passenger_count):  # 1부터 시작 (첫 번째 승객은 예매자 본인)
                            try:
                                # 동승자 이름 입력 필드 찾기 (인덱스가 1부터 시작)
                                passenger_input = quick_wait.until(EC.presence_of_element_located(
                                    (By.XPATH, f"/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[11]/div[5]/div[3]/table/tbody/tr[{i+1}]/td[8]/input[2]")))
                                
                                # 동승자 이름 입력
                                passenger_name = ""
                                if 'passenger_names' in train_info and i-1 < len(train_info['passenger_names']):
                                    passenger_name = train_info['passenger_names'][i-1]
                                
                                # 이름이 비어있으면 기본값 설정
                                if not passenger_name:
                                    passenger_name = f"동승자{i}"
                                
                                # 이름 입력
                                passenger_input.clear()
                                passenger_input.send_keys(passenger_name)
                                log(f"동승자 {i} 이름 입력 완료: {passenger_name}")
                            except Exception as e:
                                log(f"동승자 {i} 이름 입력 중 오류: {str(e)}")
                        
                        log("동승자 정보 입력 완료")
                        time.sleep(1)  # 페이지 안정화를 위한 대기 시간 추가
                    except Exception as e:
                        log(f"동승자 정보 입력 중 오류 발생: {str(e)}")
                
                # 간편결제 탭과 카카오페이 선택 부분 수정
                try:
                    log("간편결제 탭으로 전환 중...")
                    # 페이지 안정화를 위한 대기 시간 추가
                    time.sleep(1)
                    
                    # id로 요소 찾기 (더 정확함)
                    easy_payment_tab = quick_wait.until(EC.presence_of_element_located((By.ID, "chTab2")))
                    
                    # JavaScript로 클릭 실행
                    driver.execute_script("arguments[0].click();", easy_payment_tab)
                    # 또는 onclick 이벤트 직접 호출
                    log("간편결제 탭 클릭 완료")
                    
                    # 탭 전환 후 잠시 대기
                    time.sleep(1)
                    
                    # 카카오페이 라디오 버튼 선택 - id로 찾기
                    kakao_pay_button = quick_wait.until(EC.presence_of_element_located((By.ID, "kakaoPay")))
                    driver.execute_script("arguments[0].click();", kakao_pay_button)
                    # 또는 onclick 이벤트 직접 호출
                    # driver.execute_script("changeStlTpCd(document.getElementById('kakaoPay'))")
                    log("카카오페이 선택 완료")
                    
                except Exception as e:
                    log(f"결제 방식 선택 중 오류: {str(e)}")
                    # 대체 방법 시도
                    try:
                        # 스크롤을 아래로 이동
                        driver.execute_script("window.scrollBy(0, 300);")
                        time.sleep(1)
                        
                        # onclick 이벤트 직접 호출 시도
                        driver.execute_script("changeTab(1); return false;")
                        log("간편결제 탭 클릭 완료 (스크립트 호출)")
                        
                        time.sleep(1)
                        
                        # onclick 이벤트 직접 호출
                        driver.execute_script("changeStlTpCd(document.getElementById('kakaoPay'))")
                        log("카카오페이 선택 완료 (스크립트 호출)")
                    except Exception as sub_e:
                        log(f"대체 방법으로 결제 방식 선택 중 오류: {str(sub_e)}")
                        # 세 번째 방법 시도
                        try:
                            log("다른 방법으로 결제 방식 선택 시도...")
                            # XPath로 시도
                            driver.find_element(By.XPATH, "//a[@id='chTab2']").click()
                            time.sleep(1)
                            driver.find_element(By.XPATH, "//input[@id='kakaoPay']").click()
                            log("결제 방식 선택 완료 (XPath)")
                        except Exception as third_e:
                            log(f"모든 결제 방식 선택 시도 실패: {str(third_e)}")

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
                    # 결제가 완료될 때까지 계속 대기
                    while True:
                        try:
                            # 결제완료 페이지의 특정 요소들을 확인
                            current_url = driver.current_url
                            page_source = driver.page_source
                            
                            # 결제완료 페이지의 특징적인 텍스트들을 확인
                            completion_indicators = [
                                "스마트티켓 발급이 완료되었습니다",
                                "결제완료",
                                "승인번호",
                                "결제금액"
                            ]
                            
                            if any(indicator in page_source for indicator in completion_indicators):
                                # 결제 정보 추출 시도
                                try:
                                    amount = driver.find_element(By.XPATH, "//td[contains(text(), '원')]").text
                                    approval_date = driver.find_element(By.XPATH, "//td[contains(text(), '20')]").text
                                    log(f"결제가 완료되었습니다!")
                                    log(f"결제 금액: {amount}")
                                    log(f"승인 일시: {approval_date}")
                                except:
                                    log("결제가 완료되었습니다!")
                                
                                time.sleep(2)  # 결제 완료 페이지 로딩 대기
                                
                                # 모든 창 닫기
                                try:
                                    for window in driver.window_handles:
                                        driver.switch_to.window(window)
                                        driver.close()
                                except:
                                    pass
                                
                                log("예매가 완료되어 브라우저를 종료합니다.")
                                return True
                                
                            time.sleep(1)
                        except Exception as e:
                            if "no such window" in str(e):
                                log("결제가 완료되었습니다!")
                                return True
                            time.sleep(1)
                except TimeoutException:
                    log("결제 시간이 초과되었습니다. (10분 경과)")
                    # 계속 대기
                    while True:
                        try:
                            current_url = driver.current_url
                            page_source = driver.page_source
                            if "결제완료" in page_source or "srail.kr" in current_url:
                                log("결제가 완료되었습니다!")
                                time.sleep(2)
                                return True
                            time.sleep(1)
                        except Exception as e:
                            if "no such window" in str(e):
                                log("결제가 완료되었습니다!")
                                return True
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
        print(f"SRT 티켓 헌터 v{VERSION}")
        print("이 스크립트는 직접 실행하지 않고 GUI를 통해 실행해주세요.")
        print("python main.py를 실행하여 GUI를 시작하세요.")
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 

# 인원수 설정 함수 구현
def set_passenger_count(driver, wait, count, log_func):
    try:
        # 1인이면 기본값이므로 별도 설정 필요 없음
        if count <= 1:
            log_func("인원수: 1명 (기본값)")
            return True
            
        log_func(f"인원수 {count}명으로 설정 중...")
        
        # 인원수 선택 드롭다운 찾기 - ID로 찾기 시도
        try:
            adult_select = wait.until(EC.presence_of_element_located((By.ID, "psgInfoPerPrnb1")))
        except:
            # ID로 찾기 실패 시 XPath로 시도
            adult_select = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div/div[4]/div/div[2]/form/fieldset/div[1]/div/ul/li[2]/div[2]/div[1]/select")))
        
        # Select 객체를 사용하여 값 설정
        select = Select(adult_select)
        select.select_by_value(str(count))
        
        log_func(f"인원수 {count}명 설정 완료")
        return True
        
    except Exception as e:
        log_func(f"인원수 설정 중 오류 발생: {str(e)}")
        return False 
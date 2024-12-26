from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
import time
import configparser
import os

def setup_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 10)
    return driver, wait

def load_config():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if not os.path.exists(config_path):
        raise FileNotFoundError("config.ini 파일을 찾을 수 없습니다.")
    config.read(config_path, encoding='utf-8')
    return config

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
        
        # 일반실 예약 버튼 찾기
        reserve_button = None
        general_button = cols[6].find_elements(By.CSS_SELECTOR, "a[href='#none'] span")
        if general_button and general_button[0].text == "예약하기":
            reserve_button = general_button[0].find_element(By.XPATH, "./..")  # 부모 a 태그
        
        # 일반실이 없으면 특실 예약 버튼 찾기
        if not reserve_button:
            special_button = cols[5].find_elements(By.CSS_SELECTOR, "a[href='#none'] span")
            if special_button and special_button[0].text == "예약하기":
                reserve_button = special_button[0].find_element(By.XPATH, "./..")  # 부모 a 태그
        
        return {
            'type': train_type,
            'number': train_number,
            'dep_time': dep_time,
            'arr_time': arr_time,
            'has_reserve_button': reserve_button is not None,
            'reserve_button': reserve_button
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

def find_available_train(driver, wait, target_time, time_tolerance):
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
                
            # 예약 가능한지 확인
            if train_info['has_reserve_button']:
                train_info['time_diff'] = time_difference
                available_trains.append(train_info)
        
        # 시간 차이가 가장 적은 열차 선택
        if available_trains:
            return min(available_trains, key=lambda x: x['time_diff'])
        
        return None
        
    except Exception as e:
        print(f"열차 검색 중 오류: {str(e)}")
        return None

def search_and_reserve(driver, wait, config):
    """
    열차 검색 및 예약 시도 함수
    """
    while True:
        try:
            # 조회하기 버튼 클릭
            print("\n새로운 검색 시도...")
            search_button = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[2]/input")))
            
            # JavaScript로 클릭 실행
            driver.execute_script("arguments[0].click();", search_button)
            print("조회하기 버튼 클릭 완료")
            
            time.sleep(1)  # 검색 결과 로딩 대기
            
            # 허용 시간 내의 예약 가능한 열차 찾기
            target_time = config['TRAIN']['target_time']
            time_tolerance = int(config['TRAIN']['time_tolerance'])
            available_train = find_available_train(driver, wait, target_time, time_tolerance)
            
            if available_train:
                print(f"\n예약 가능한 열차를 찾았습니다!")
                print(f"열차번호: {available_train['number']}")
                print(f"출발시간: {available_train['dep_time']}")
                print(f"도착시간: {available_train['arr_time']}")
                
                # 예약하기 버튼 클릭
                available_train['reserve_button'].click()
                print("예약하기 버튼 클릭 완료")
                
                # 결제하기 버튼 클릭
                quick_wait = WebDriverWait(driver, 5)
                payment_button = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div/div[4]/div/div[2]/form/fieldset/div[11]/a[1]")))
                payment_button.click()
                print("결제하기 버튼 클릭 완료")

                # 간편결제 탭 클릭
                easy_payment_tab = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[2]/ul/li[2]/a")))
                easy_payment_tab.click()
                print("간편결제 탭 클릭 완료")

                # 카카오페이 버튼 클릭
                kakao_pay_button = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[6]/div[1]/table/tbody/tr/td/div/input[3]")))
                kakao_pay_button.click()
                print("카카오페이 선택 완료")

                # 스마트폰 발권 옵션 클릭
                smartphone_ticket = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[11]/div[2]/ul/li[2]/a")))
                smartphone_ticket.click()
                print("스마트폰 발권 옵션 선택 완료")

                # alert 창 처리
                time.sleep(1)  # alert 창이 나타날 때까지 잠시 대기
                alert = driver.switch_to.alert
                alert.accept()
                print("알림창 확인 클릭 완료")

                # 결제 및 발권 버튼 클릭
                final_payment_button = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[11]/div[11]/input[2]")))
                final_payment_button.click()
                print("결제 및 발권 버튼 클릭 완료")

                # 새 창으로 전환
                time.sleep(2)  # 새 창이 열릴 때까지 대기
                windows = driver.window_handles
                driver.switch_to.window(windows[-1])  # 마지막으로 열린 창으로 전환
                print("카카오페이 결제창으로 전환 완료")

                # 카톡결제 버튼 클릭
                kakao_talk_pay = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div/main/div/div[1]/div[4]/span")))
                kakao_talk_pay.click()
                print("카톡결제 버튼 클릭 완료")

                # 휴대폰 번호 입력
                phone_input = quick_wait.until(EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[1]/main/div/div[2]/div/div[2]/form/div[1]/div/div/span/input")))
                phone_input.send_keys(config['PERSONAL']['phone'])
                print("휴대폰 번호 입력 완료")

                # 생년월일 입력
                birth_input = quick_wait.until(EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[1]/main/div/div[2]/div/div[2]/form/div[2]/div/div/span/input")))
                birth_input.send_keys(config['PERSONAL']['birth'])
                print("생년월일 입력 완료")

                # 최종 결제요청 버튼 클릭
                final_request_button = quick_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "/html/body/div[1]/main/div/div[2]/div/div[2]/form/button")))
                final_request_button.click()
                print("최종 결제요청 완료")

                return True
            
            print("예약 가능한 열차가 없습니다. 잠시 후 다시 시도합니다...")
            time.sleep(float(config['SETTINGS']['refresh_interval']))
            
        except Exception as e:
            print(f"검색 중 오류 발생: {str(e)}")
            time.sleep(float(config['SETTINGS']['refresh_interval']))

def test_login_and_search(driver, wait, config):
    try:
        # 1. 로그인 페이지로 이동
        print("로그인 페이지로 이동 중...")
        driver.get("https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000")
        time.sleep(0.5)
        
        # 2. 로그인 정보 입력
        member_id = config['LOGIN']['id']
        member_pw = config['LOGIN']['password']
        
        print("로그인 시도 중...")
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
            print("로그인 성공!")
            
            # 메인 창을 제외한 다른 탭 닫기
            main_window = driver.current_window_handle
            for handle in driver.window_handles:
                if handle != main_window:
                    driver.switch_to.window(handle)
                    driver.close()
            driver.switch_to.window(main_window)
            print("추가 탭 정리 완료")
            
            # 5. 일반승차권 조회 페이지로 이동
            print("일반승차권 조회 페이지로 이동 중...")
            driver.get("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000")
            time.sleep(0.5)
            
            # 6. 출발역 입력
            dep_stn = config['TRAIN']['departure']
            print(f"출발역 입력 시도: {dep_stn}")
            dep_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[1]/div/div/div[1]/input")))
            dep_input.clear()
            dep_input.send_keys(dep_stn)
            print("출발역 입력 완료")
            
            time.sleep(0.3)
            
            # 7. 도착역 입력
            arr_stn = config['TRAIN']['arrival']
            print(f"도착역 입력 시도: {arr_stn}")
            arr_input = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[1]/div/div/div[2]/input")))
            arr_input.clear()
            arr_input.send_keys(arr_stn)
            print("도착역 입력 완료")
            
            time.sleep(0.3)
            
            # 8. 날짜 선택
            date = config['TRAIN']['date']
            print(f"날짜 선택 시도: {date}")
            
            # 날짜 드롭다운 클릭
            date_select = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "select[name='dptDt']")))  # name 속성으로 선택
            date_select.click()
            time.sleep(0.3)
            
            # 날짜 옵션 선택 - Select 클래스 사용
            date_selector = Select(date_select)
            date_selector.select_by_visible_text(date)
            print("날짜 선택 완료")
            
            time.sleep(0.3)
            
            # 9. 시간 선택
            target_time = config['TRAIN']['target_time']
            print(f"시간 선택 시도: {target_time}시")
            
            # 시간 드롭다운 클릭
            time_select = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "select[name='dptTm']")))
            time_select.click()
            time.sleep(0.3)
            
            # 시간 옵션 선택 - Select 클래스 사용
            time_selector = Select(time_select)
            time_selector.select_by_value(f"{target_time}0000")  # 시간값에 0000 추가 (예: 080000)
            print("시간 선택 완료")
            
            time.sleep(0.3)
            
            # 10. 조회 및 예약 시도
            search_and_reserve(driver, wait, config)
            
            return True
            
        except TimeoutException:
            print("로그인 실패: 아이디나 비밀번호를 확인해주세요.")
            return False
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(f"상세 오류 정보:\n{traceback.format_exc()}")
        return False

def main():
    try:
        # 설정 로드
        config = load_config()
        
        # 드라이버 설정
        driver, wait = setup_driver()
        
        try:
            # 로그인 및 역 입력 테스트
            test_login_and_search(driver, wait, config)
            
            # 결과 확인을 위해 잠시 대기
            input("프로그램을 종료하려면 Enter를 누르세요...")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 
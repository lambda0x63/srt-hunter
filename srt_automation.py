from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
from version import VERSION

def setup_driver():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
        headless=False,
        args=['--start-maximized']
    )
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    return playwright, browser, context, page

def parse_train_info(row):
    try:
        cols = row.locator("td").all()
        train_type = cols[1].text_content().split('\n')[0]  # 열차종류
        train_number = cols[2].text_content().strip()  # 열차번호
        # 출발역/도착역에서 시간 추출
        dep_info = cols[3].text_content().strip().split('\n')
        dep_time = dep_info[1] if len(dep_info) > 1 else dep_info[0]
        arr_info = cols[4].text_content().strip().split('\n')
        arr_time = arr_info[1] if len(arr_info) > 1 else arr_info[0]
        
        # td[7]이 일반실 예약 버튼 위치
        # 특실 예약 버튼 찾기 (열 6 = td[6])
        special_button = None
        if len(cols) > 5:
            special_text = cols[5].text_content().strip()
            # "예약하기" 또는 "예약 하기" 둘 다 체크
            if "예약" in special_text and "하기" in special_text and "매진" not in special_text:
                # span 태그 내의 텍스트를 찾아서 버튼 선택
                special_buttons = cols[5].locator("a.btn_burgundy_dark").all()
                if special_buttons:
                    special_button = special_buttons[0]
        
        # 일반실 예약 버튼 찾기 (열 7 = td[7])
        general_button = None
        if len(cols) > 6:
            general_text = cols[6].text_content().strip()
            # "예약하기" 또는 "예약 하기" 둘 다 체크
            if "예약" in general_text and "하기" in general_text and "매진" not in general_text:
                # span 태그 내의 텍스트를 찾아서 버튼 선택
                general_buttons = cols[6].locator("a.btn_burgundy_dark").all()
                if general_buttons:
                    general_button = general_buttons[0]
        
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
    h1, m1 = map(int, time1.split(':'))
    h2, m2 = map(int, time2.split(':'))
    return abs((h1 * 60 + m1) - (h2 * 60 + m2))

def find_available_train(page, target_time, time_tolerance, seat_types):
    try:
        # 조회 결과 대기
        page.wait_for_selector("tbody tr", timeout=10000)
        
        # 모든 행을 가져옴 (여러 tbody가 있을 수 있으므로 모두 확인)
        rows = page.locator("tbody tr").all()
        
        print(f"[DEBUG] 찾은 행 수: {len(rows)}")
        print(f"[DEBUG] 목표 시간: {target_time}, 허용 범위: {time_tolerance}분")
        print(f"[DEBUG] 좌석 선택: 특실={seat_types.get('special', False)}, 일반실={seat_types.get('general', False)}")
        
        target_time_str = f"{target_time}:00"
        
        # 각 행을 순서대로 확인
        for idx, row in enumerate(rows):
            try:
                # 모든 td 가져오기
                cols = row.locator("td").all()
                if len(cols) < 7:  # 최소 7개 열이 필요
                    continue
                
                # 열차 정보 추출 (간단하게)
                train_type = cols[1].text_content().strip().split('\n')[0] if len(cols) > 1 else ""
                
                # SRT만 처리
                if "SRT" not in train_type:
                    continue
                
                # 출발 시간 찾기 (보통 3번째 또는 4번째 열)
                dep_time = None
                for i in [3, 4]:
                    if i < len(cols):
                        time_text = cols[i].text_content()
                        if ":" in time_text:
                            # 시간 포맷 찾기 (HH:MM)
                            import re
                            time_match = re.search(r'(\d{2}:\d{2})', time_text)
                            if time_match:
                                dep_time = time_match.group(1)
                                break
                
                if not dep_time:
                    continue
                
                # 시간 범위 체크: target_time <= dep_time <= target_time + tolerance
                # 예: 10:00 목표, 120분 허용 -> 10:00 ~ 12:00 사이
                dep_hour, dep_min = map(int, dep_time.split(':'))
                target_hour, target_min = map(int, target_time_str.split(':'))
                
                # 분 단위로 변환
                dep_total_minutes = dep_hour * 60 + dep_min
                target_total_minutes = target_hour * 60 + target_min
                
                # 출발 시간이 목표 시간보다 이전이면 스킵
                if dep_total_minutes < target_total_minutes:
                    continue
                
                # 출발 시간이 허용 범위를 벗어나면 스킵
                if dep_total_minutes > target_total_minutes + time_tolerance:
                    continue
                
                time_difference = dep_total_minutes - target_total_minutes
                
                print(f"[DEBUG] 행 {idx}: 출발 {dep_time}, 시간차 {time_difference}분")
                
                # 예약 버튼 찾기
                # 일반실 체크 (td[7] = 인덱스 6)
                if seat_types.get('general', False) and len(cols) > 6:
                    general_col = cols[6]  # td[7] = 일반실 열
                    
                    # 매진이 아닌지 먼저 확인
                    if "매진" not in general_col.text_content():
                        # "예약하기" 버튼만 찾기 (좌석선택 버튼은 무시)
                        reserve_buttons = general_col.locator("a").all()
                        for btn in reserve_buttons:
                            btn_text = btn.text_content().strip()
                            # "예약하기" 또는 "예약 하기" 텍스트를 가진 버튼만 선택
                            if "예약" in btn_text and "하기" in btn_text and "좌석" not in btn_text:
                                print(f"[DEBUG] 일반실 예약 가능! 행 {idx}, 출발 {dep_time}")
                                return {
                                    'dep_time': dep_time,
                                    'reserve_button': btn,
                                    'time_diff': time_difference,
                                    'row_index': idx,
                                    'seat_type': '일반실'
                                }
                
                # 특실 체크 (td[6] = 인덱스 5)
                if seat_types.get('special', False) and len(cols) > 5:
                    special_col = cols[5]  # td[6] = 특실 열
                    
                    # 매진이 아닌지 먼저 확인
                    if "매진" not in special_col.text_content():
                        # "예약하기" 버튼만 찾기 (좌석선택 버튼은 무시)
                        reserve_buttons = special_col.locator("a").all()
                        for btn in reserve_buttons:
                            btn_text = btn.text_content().strip()
                            # "예약하기" 또는 "예약 하기" 텍스트를 가진 버튼만 선택
                            if "예약" in btn_text and "하기" in btn_text and "좌석" not in btn_text:
                                print(f"[DEBUG] 특실 예약 가능! 행 {idx}, 출발 {dep_time}")
                                return {
                                    'dep_time': dep_time,
                                    'reserve_button': btn,
                                    'time_diff': time_difference,
                                    'row_index': idx,
                                    'seat_type': '특실'
                                }
                
            except Exception as e:
                print(f"[DEBUG] 행 {idx} 처리 중 오류: {str(e)}")
                continue
        
        return None
        
    except Exception as e:
        print(f"열차 검색 중 오류: {str(e)}")
        return None

def search_and_reserve(page, login_info, train_info, settings, personal_info, progress_signal=None):
    def log(message):
        if progress_signal:
            progress_signal.emit(message)
        print(message)
    
    while True:
        try:
            
            # 조회하기 버튼 클릭
            log("\n새로운 검색 시도...")
            search_button = page.locator("xpath=/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[2]/input")
            search_button.wait_for(timeout=10000)
            
            # JavaScript로 클릭 실행
            page.evaluate("(element) => element.click()", search_button.element_handle())
            log("조회하기 버튼 클릭 완료")
            
            time.sleep(1)  # 검색 결과 로딩 대기
            
            # 허용 시간 내의 예약 가능한 열차 찾기
            target_time = train_info['target_time']
            time_tolerance = int(train_info['time_tolerance'])
            seat_types = train_info['seat_types']
            available_train = find_available_train(page, target_time, time_tolerance, seat_types)
            
            if available_train:
                log(f"\n예약 가능한 열차를 찾았습니다!")
                log(f"출발시간: {available_train['dep_time']}")
                log(f"좌석 유형: {available_train.get('seat_type', 'N/A')}")
                log(f"행 번호: {available_train.get('row_index', 'N/A')}")
                
                # 예약하기 버튼 클릭
                available_train['reserve_button'].click()
                log("예약하기 버튼 클릭 완료")
                
                # SRT 2개 편성 연결 열차 알림창 처리
                page.on("dialog", lambda dialog: dialog.accept())
                
                # confirmReservationInfo 페이지로 이동될 때까지 대기 (대기열 자동 처리)
                page.wait_for_url("**/confirmReservationInfo**", timeout=30000)
                log("예약 확인 페이지 로드 완료")
                
                # 잔여석 없음 메시지 확인
                time.sleep(1)
                if "잔여석 없음" in page.content() or "좌석이 매진" in page.content():
                    log("다른 사용자가 먼저 좌석을 예약했습니다. 다시 검색을 시도합니다.")
                    page.go_back()
                    continue
                
                log("좌석이 있는 것으로 확인됩니다. 결제 진행 중...")
                
                # 결제하기 버튼 클릭
                try:
                    payment_button = page.locator("xpath=/html/body/div/div[4]/div/div[2]/form/fieldset/div[11]/a[1]")
                    payment_button.wait_for(state="visible", timeout=5000)
                    payment_button.click()
                    log("결제하기 버튼 클릭 완료")
                except Exception as e:
                    log(f"결제하기 버튼 클릭 실패: {str(e)}")
                    
                    # 페이지 내용 확인
                    page_content = page.content()
                    if "잔여석 없음" in page_content or "좌석이 매진" in page_content:
                        log("다른 사용자가 먼저 좌석을 예약했습니다. 다시 검색을 시도합니다.")
                    else:
                        log("알 수 없는 이유로 결제하기 버튼을 찾을 수 없습니다.")
                    
                    page.go_back()
                    continue

                
                # 간편결제 탭과 카카오페이 선택
                try:
                    log("간편결제 탭으로 전환 중...")
                    time.sleep(1)
                    
                    # id로 요소 찾기
                    easy_payment_tab = page.locator("#chTab2")
                    page.evaluate("(element) => element.click()", easy_payment_tab.element_handle())
                    log("간편결제 탭 클릭 완료")
                    
                    time.sleep(1)
                    
                    # 카카오페이 라디오 버튼 선택
                    kakao_pay_button = page.locator("#kakaoPay")
                    page.evaluate("(element) => element.click()", kakao_pay_button.element_handle())
                    log("카카오페이 선택 완료")
                    
                except Exception as e:
                    log(f"결제 방식 선택 중 오류: {str(e)}")
                    # 대체 방법 시도
                    try:
                        page.evaluate("window.scrollBy(0, 300)")
                        time.sleep(1)
                        page.evaluate("changeTab(1); return false;")
                        log("간편결제 탭 클릭 완료 (스크립트 호출)")
                        time.sleep(1)
                        page.evaluate("changeStlTpCd(document.getElementById('kakaoPay'))")
                        log("카카오페이 선택 완료 (스크립트 호출)")
                    except Exception as sub_e:
                        log(f"대체 방법 실패: {str(sub_e)}")

                # 스마트폰 발권 옵션 클릭
                smartphone_ticket = page.locator("xpath=/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[11]/div[2]/ul/li[2]/a")
                smartphone_ticket.click()
                log("스마트폰 발권 옵션 선택 완료")

                # alert 창 처리는 이미 설정됨
                time.sleep(1)

                # 결제 및 발권 버튼 클릭
                final_payment_button = page.locator("xpath=/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[11]/div[11]/input[2]")
                final_payment_button.click()
                log("결제 및 발권 버튼 클릭 완료")

                # 새 창/탭 처리 - 레거시처럼 처리
                time.sleep(2)  # 새 창이 열릴 때까지 대기
                
                # 이미 열려있는 모든 페이지 확인
                all_pages = page.context.pages
                log(f"현재 열린 페이지 수: {len(all_pages)}")
                
                if len(all_pages) > 1:
                    # 마지막으로 열린 페이지로 전환 (레거시처럼)
                    new_page = all_pages[-1]
                    log("카카오페이 결제창으로 전환 완료 (이미 열림)")
                else:
                    # 새 페이지가 아직 안 열렸다면 대기
                    try:
                        with page.context.expect_page(timeout=5000) as new_page_info:
                            pass
                        new_page = new_page_info.value
                        log("카카오페이 결제창으로 전환 완료 (새로 열림)")
                    except:
                        log("새 창을 찾을 수 없음 - 현재 페이지에서 계속")
                        new_page = page  # 현재 페이지 사용
                
                # 페이지 완전 로딩 대기
                new_page.wait_for_load_state("networkidle")
                time.sleep(2)  # 추가 대기

                # Tab 키로 카톡결제 탭으로 이동
                log("Tab 키로 카톡결제 탭 선택 시도")
                # Tab 2번 누르기 (QR결제 -> 카톡결제)
                new_page.keyboard.press("Tab")
                time.sleep(0.2)
                new_page.keyboard.press("Tab")
                time.sleep(0.2)
                # 스페이스바 또는 엔터로 선택
                new_page.keyboard.press("Enter")
                log("카톡결제 탭 선택 완료")
                
                time.sleep(2)  # 탭/화면 전환 대기

                # 휴대폰 번호 입력
                try:
                    phone_input = new_page.locator("xpath=/html/body/div[1]/main/div/div[2]/div/div[2]/form/div[1]/div/div/span/input")
                    phone_input.wait_for(state="visible", timeout=5000)
                    phone_input.fill(personal_info['phone'])
                    log("휴대폰 번호 입력 완료")
                except:
                    log("휴대폰 번호 입력 실패")

                # 생년월일 입력
                try:
                    birth_input = new_page.locator("xpath=/html/body/div[1]/main/div/div[2]/div/div[2]/form/div[2]/div/div/span/input")
                    birth_input.wait_for(state="visible", timeout=5000)
                    birth_input.fill(personal_info['birth'])
                    log("생년월일 입력 완료")
                except:
                    log("생년월일 입력 실패")

                # 최종 결제요청 버튼 클릭
                try:
                    # 레거시와 동일한 XPath 사용
                    final_request_button = new_page.locator("xpath=/html/body/div[1]/main/div/div[2]/div/div[2]/form/button")
                    final_request_button.wait_for(state="visible", timeout=5000)
                    time.sleep(0.5)  # 버튼 활성화 대기
                    final_request_button.click()
                    log("최종 결제요청 완료")
                except:
                    log("결제요청 버튼 클릭 실패")

                # 결제 완료 대기 (최대 10분)
                try:
                    completion_indicators = [
                        "text=스마트티켓 발급이 완료되었습니다",
                        "text=결제완료",
                        "text=승인번호",
                        "text=결제금액"
                    ]
                    
                    # 여러 선택자 중 하나라도 나타나면 완료
                    for indicator in completion_indicators:
                        try:
                            new_page.wait_for_selector(indicator, timeout=600000)
                            break
                        except:
                            continue
                    
                    # 결제 정보 추출
                    try:
                        amount = new_page.locator("td:has-text('원')").first.text_content()
                        approval_date = new_page.locator("td:has-text('20')").first.text_content()
                        log(f"결제가 완료되었습니다!")
                        log(f"결제 금액: {amount}")
                        log(f"승인 일시: {approval_date}")
                    except:
                        log("결제가 완료되었습니다!")
                    
                    time.sleep(2)
                    
                    # 모든 페이지 닫기
                    new_page.close()
                    
                    log("예매가 완료되어 브라우저를 종료합니다.")
                    return True
                    
                except PlaywrightTimeoutError:
                    log("결제 시간이 초과되었습니다. (10분 경과)")
                    # 계속 대기
                    while True:
                        try:
                            page_content = new_page.content()
                            if "결제완료" in page_content:
                                log("결제가 완료되었습니다!")
                                time.sleep(2)
                                return True
                            time.sleep(1)
                        except:
                            log("결제가 완료되었습니다!")
                            return True

                return True
            
            log("예약 가능한 열차가 없습니다. 잠시 후 다시 시도합니다...")
            time.sleep(float(settings['refresh_interval']))
                
        except Exception as e:
            log(f"검색 중 오류 발생: {str(e)}")
            if "Connection aborted" in str(e) or "Failed to establish" in str(e):
                log("브라우저 연결이 종료되었습니다.")
                return False
            time.sleep(float(settings['refresh_interval']))

def start_reservation(playwright, browser, context, page, login_info, train_info, personal_info, settings, progress_signal=None):
    def log(message):
        if progress_signal:
            progress_signal.emit(message)
        print(message)
        
    try:
        # 1. 로그인 페이지로 이동
        log("로그인 페이지로 이동 중...")
        page.goto("https://etk.srail.kr/cmc/01/selectLoginForm.do?pageId=TK0701000000")
        time.sleep(0.5)
        
        # 2. 로그인 정보 입력
        member_id = login_info['id']
        member_pw = login_info['password']
        
        log("로그인 시도 중...")
        id_input = page.locator("#srchDvNm01")
        id_input.fill("")
        id_input.fill(member_id)
        
        pw_input = page.locator("#hmpgPwdCphd01")
        pw_input.fill("")
        pw_input.fill(member_pw)
        
        # 3. 로그인 버튼 클릭 (첫 번째 활성화된 버튼 선택)
        # 더 명확한 선택자 사용 - nth(0)로 첫 번째 요소 선택
        submit_button = page.locator("input.submit.btn_pastel2.loginSubmit[type='submit']").nth(0)
        submit_button.click()
        
        # 4. 로그인 성공 확인
        try:
            page.wait_for_url("https://etk.srail.kr/main.do", timeout=10000)
            log("로그인 성공!")
            
            # 5. 일반승차권 조회 페이지로 이동
            log("일반승차권 조회 페이지로 이동 중...")
            page.goto("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000")
            time.sleep(0.5)
            
            # 6. 출발역 입력
            dep_stn = train_info['departure']
            log(f"출발역 입력 시도: {dep_stn}")
            dep_input = page.locator("xpath=/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[1]/div/div/div[1]/input")
            dep_input.fill("")
            dep_input.fill(dep_stn)
            log("출발역 입력 완료")
            
            time.sleep(0.3)
            
            # 7. 도착역 입력
            arr_stn = train_info['arrival']
            log(f"도착역 입력 시도: {arr_stn}")
            arr_input = page.locator("xpath=/html/body/div[1]/div[4]/div/div[2]/form/fieldset/div[1]/div/div/div[2]/input")
            arr_input.fill("")
            arr_input.fill(arr_stn)
            log("도착역 입력 완료")
            
            time.sleep(0.3)
            
            # 8. 날짜 선택
            date = train_info['date']
            log(f"날짜 선택 시도: {date}")
            
            date_select = page.locator("select[name='dptDt']")
            date_select.select_option(label=date)
            log("날짜 선택 완료")
            
            time.sleep(0.3)
            
            # 9. 시간 선택
            target_time = train_info['target_time']
            log(f"시간 선택 시도: {target_time}시")
            
            time_select = page.locator("select[name='dptTm']")
            time_select.select_option(value=f"{target_time}0000")
            log("시간 선택 완료")
            
            time.sleep(0.3)
            
            # 10. 조회 및 예약 시도
            return search_and_reserve(page, login_info, train_info, settings, personal_info, progress_signal)
            
        except PlaywrightTimeoutError:
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
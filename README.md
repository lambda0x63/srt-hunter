# SRT-Hunter

SRT 1-person ticketing automation script

## Notice
- 개인 사용 목적 한정
- 과도한 새로고침 시 서버 부하 유발 가능

## Requirements
- Chrome 브라우저
- Python 3.11
- Poetry

## Features
- SRT 자동 로그인
- 지정 시간대 티켓 자동 검색
- 예매 가능석 자동 예매
- 카카오페이 결제 연동

## Process
1. 로그인
   - SRT 웹사이트 접속
   - 회원번호/비밀번호 로그인

2. 승차권 검색
   - 출발/도착역 설정
   - 날짜/시간대 설정
   - 자동 새로고침

3. 예매
   - 예약 가능석 발견 시 자동 예매
   - 지정 시간 범위 내 열차 선택
   - 스마트폰 발권 자동 설정

4. 결제
   - 카카오페이 결제 선택
   - 개인정보 자동 입력
   - 결제 요청 발송

## Todo
- [ ] 좌석 등급 선택
- [ ] 결제 수단 다양화
- [ ] GUI 개발

## Installation
```bash
git clone https://github.com/root39293/srt-hunter.git
cd srt-hunter
poetry install
```

## Configuration
1. `config.ini-sample` → `config.ini` 복사
2. `config.ini` 정보 입력

```ini
[LOGIN]
id = your_srt_number        # SRT 회원번호
password = your_srt_password # 비밀번호

[PERSONAL]
phone = 01012345678        # 휴대폰번호
birth = 990110            # 생년월일(YYMMDD)

[TRAIN]
departure = 동대구         # 출발역
arrival = 수서            # 도착역
date = 2024/12/28(토)    # 날짜(YYYY/MM/DD(요일))
target_time = 08         # 출발시간(짝수: 00, 02, ..., 22)
time_tolerance = 120     # 시간허용범위(분)

[SETTINGS]
refresh_interval = 0.05   # 새로고침 간격(초)
```

## Usage
```bash
poetry run python main.py
```

## License
MIT License

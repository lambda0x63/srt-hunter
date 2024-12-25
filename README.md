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

## Security
- config.ini 파일에 개인정보가 포함되어 있으므로 절대 공개 저장소에 업로드하지 마세요
- refresh_interval 값을 너무 낮게 설정하면 IP 차단될 수 있습니다
- 브라우저 자동화 탐지를 피하기 위해 불필요한 자동화는 자제해주세요

## Issues
버그를 발견하셨거나 새로운 기능을 제안하고 싶으시다면:
1. GitHub Issues 페이지를 확인해 주세요
2. 이미 보고된 이슈가 없다면 새로운 이슈를 생성해 주세요
3. 가능한 한 자세한 재현 방법과 오류 메시지를 포함해 주세요

## Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Version History
- v1.0.0 (2024-01-01)
  - 최초 릴리즈
  - 기본적인 예매 자동화 기능 구현

## License
MIT License

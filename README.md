# SRT-Hunter

SRT 1-person ticketing automation program (v1.0.0)
> CLI version(v0.1.0) to GUI version(v1.0.0)

## Notice
- 개인 사용 목적 한정
- 과도한 새로고침 시 서버 부하 발생 가능성
- 카카오페이 간편결제 지원 (결제요청이후 10분이내 결제 필요)

## Requirements
- Chrome 브라우저
- Python 3.11
- Poetry

## Features
- GUI 기반 인터페이스
- SRT 자동 로그인 기능
- 출발/도착역 선택 기능
- 날짜/시간대 자동 필터링 기능
- 실시간 예매 진행상황 모니터링
- 카카오페이 자동결제 연동
- 스마트폰 발권 자동화

## TODO

- [X] GUI 


## Installation
```bash
git clone https://github.com/root39293/srt-hunter.git
cd srt-hunter
poetry install
```

## Usage
```bash
poetry run python main.py
```

## Process
1. 로그인 정보 입력
   - SRT 회원번호 입력
   - SRT 비밀번호 입력

2. 결제 정보 입력
   - 휴대폰번호 11자리 입력
   - 생년월일 6자리 입력

3. 예매 정보 설정
   - 출발역/도착역 선택
   - 날짜 선택 (27일 이내)
   - 출발 시간 선택 (짝수 시간대)
   - 허용 시간 범위 입력 (분)
   - 새로고침 간격 입력 (초)

4. 예매 진행
   - 예매 시작 버튼 클릭
   - 실시간 진행상황 확인
   - 중지 버튼으로 진행 중단

## Caution
- 0.05초 이상 새로고침 간격 권장
- 로그인 및 결제 정보 메모리에서만 처리 (파일 저장 없음)
- Chrome 브라우저 유지

## License
MIT License

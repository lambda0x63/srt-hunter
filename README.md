# SRT-Hunter

SRT 자동화 예매 에이전트 (v1.3.4)

## Features
- GUI 기반 인터페이스
- SRT 자동 로그인 및 예매 자동화
- 카카오페이 자동결제 연동
- 다중 승객 예약 지원 (1-4명)
- 중단 및 초기화 기능
- 결제 완료 상세 정보 표시

## UI
![ui](https://github.com/user-attachments/assets/30db9ec0-493e-4cc2-852b-4ec1fe2ff06a)

## Download
- Download: [Latest Release](https://github.com/root39293/srt-hunter/releases/latest)
- Run on your own PC
```bash
git clone https://github.com/root39293/srt-hunter.git
cd srt-hunter
poetry install
poetry run python main.py
```

## Notice
- 개인 사용 목적으로만 사용
- 0.05초 이상 새로고침 간격 권장
- Chrome 브라우저 필요

## Change Log

### v1.3.4
- 빌드스크립트 버그 수정

### v1.3.3
- 다중 승객 예약 기능 추가 (1-4명)
- 로그인 정보 관리 방식 개선 (비밀번호 제외 텍스트 파일 저장)
- 좌석 유형 선택을 라디오 버튼으로 변경
- 중단 및 초기화 버튼 추가
- 사용자 인터페이스 개선

### v1.2.1
- 로그인 정보 저장 기능 추가

### v1.1.1
- 결제 완료 감지 로직 개선
- 결제 상세 정보(금액, 승인일시) 표시 기능 추가
- 결제 완료 페이지 안정성 개선

## License
MIT License
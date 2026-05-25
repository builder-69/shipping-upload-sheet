# 프로젝트명

beclo-order

# 프로젝트 목표

기존 index.html 기반 발주서 생성 웹사이트를
frontend + Python FastAPI backend 구조로 분리한다.

# 현재 구조

- frontend/index.html: 웹 화면
- backend/: 기존 Python 주문 처리 로직 보관
- backend/main.py: FastAPI 서버
- PROJECT_CONTEXT.md: Codex 작업 기준 문서

# 중요한 원칙

- 기존 Python 로직을 원본 로직으로 유지한다.
- JS로 포팅한 주문 처리 로직은 제거한다.
- 프론트엔드는 파일 업로드, API 호출, 결과 표시만 담당한다.
- 백엔드는 업로드 파일을 받아 Python 로직으로 처리한다.

# 목표 배포 구조

- frontend: 개발용 원본 화면
- docs: GitHub Pages 배포용 화면
- backend: Render

# 프론트엔드 배포 운영 규칙

- `frontend/index.html`이 프론트엔드 원본이다.
- `docs/index.html`은 GitHub Pages 배포용 복사본이다.
- `frontend/index.html`을 수정한 뒤에는 반드시 `python sync_frontend_to_docs.py` 또는 `sync_frontend_to_docs.bat`을 실행한다.
- GitHub Pages 설정은 `main` branch의 `/docs` 폴더를 사용한다.

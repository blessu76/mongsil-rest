# mongsil.ipe.rest

몽실이 키우기(Mongsil) 소개 사이트. GitHub Pages 정적 배포, 도메인은 `CNAME`(mongsil.ipe.rest).

## 구성
- 페이지: 홈 · 소개 · 저널(첫 글 1개). 한국어가 루트(`/`), 영어는 `/en/`.
- 메뉴는 모든 페이지에 **홈 / 소개 / 저널** 3개.
- `scripts/build.py` 가 페이지 HTML 을 만든다. 생성 페이지는 손으로 고치지 않는다 — 문구는 `scripts/build.py` 의 `STR` 에서 고친다.
- `assets/mongsil.css` 를 고치면 `scripts/build.py` 의 `CSS_V` 도 올린다(캐시버스팅 `?v=`).
- 캐릭터·아이콘 SVG 는 `assets/img/` (F-032 `design/` 정본에서 복사).

## 시험
```sh
python3 scripts/build.py                 # 페이지 다시 만들기
python3 -m unittest discover -s tests    # 메뉴 3개 · 생성본 최신 · 캐시버스팅 · 금칙어
```

## 약관·개인정보처리방침
- `/privacy/` · `/terms/` (ko) 와 `/en/privacy/` · `/en/terms/` (en) — 푸터 링크로 연결. 문구는 `scripts/build.py` 의 `LEGAL`.
- 문구 출처: 자매 사이트 iltonggi-rest `content/ko.json`·`en.json` 의 기본 문구(ipe 앱 사이트 기본). 몽실 사실로 고친 점: 분석·쿠키·날씨 절 삭제, iCloud(본인 계정, ipe 서버 없음)·Apple 인앱결제 절 추가.
- 연락처 `ipe.haven@gmail.com` · 운영 `Davy Kim (ipe Studio)` · 시행일 2026년 11월 19일 (iltonggi 방식).
- 법적 문구라 게시 전 Davy 확인이 필요할 수 있다. 약관·방침에는 결제·서버 말이 들어가므로 금칙어 시험은 메뉴 페이지에만 건다.

## 아직 없는 것 (미정)
- 릴리즈 노트·결제 안내(메뉴 페이지)·서버 설명은 넣지 않는다.
- 대표 캐릭터 개별 이름은 확정 전이라 본문에 쓰지 않는다(「몽실이」·앱 이름만).

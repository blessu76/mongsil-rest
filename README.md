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

## 아직 없는 것 (미정)
- **약관·개인정보처리방침 페이지는 없다.** ipe_web_kit 에는 약관 모듈이 없고(v0.7.3 기준), 개인정보 모듈은 댓글 저장(Firebase) 전제라 이 앱의 실제 처리와 맞지 않는다. 법적 문구는 Davy 확인 전까지 싣지 않는다.
- 릴리즈 노트·결제 안내·서버 설명은 넣지 않는다.
- 대표 캐릭터 개별 이름은 확정 전이라 본문에 쓰지 않는다(「몽실이」·앱 이름만).

# mongsil.ipe.rest

몽실이 키우기 소개 사이트입니다. 정적 HTML은 GitHub Pages에서 제공하며 도메인은 `CNAME`에 있습니다.

## 페이지와 문안

- 한국어는 루트, 나머지는 `/<언어>/`입니다. 공통 12개 언어는 웹킷 언어 목록을 따릅니다.
- 각 언어의 홈·소개·저널 목록·개인정보처리방침·이용약관을 `scripts/build.py`가 생성합니다. 문안은 `content/site/<언어>.json`에서 고칩니다.
- 저널 원문은 `content/journal/<글>/<언어>.md`입니다. 기존 한국어·영어 글은 두 원본 주소에서 계속 읽을 수 있습니다. 번역판이 없는 언어의 목록은 영어 원문으로 연결합니다.
- `assets/mongsil.css` 또는 사이트 자체 자산을 수정할 때는 `scripts/build.py`의 `CSS_V`도 갱신합니다.

## 생성 및 검사

웹킷은 `vendor/ipe_web_kit.lock`에 고정되어 있습니다. 작업용 로컬 킷 클론에서 설치한 뒤 생성·검사합니다. 생성 HTML과 공개용 언어 스크립트는 레포에 포함합니다.

```sh
python3 scripts/kit_lock.py sync --kit ~/Developer/ipe_web_kit
python3 scripts/build.py
bash scripts/check.sh
```

## 저널 발행

`ops/rest.ipe.mongsil-publish.plist`의 LaunchAgent가 `ops/journal_gate.py`를 호출합니다. 하루 슬롯이 되면 `ops/publish_next.py`가 `~/.ipe/queue/mongsil/`의 앞 글을 처리합니다. 발행 클론에 고정 웹킷이 없으면 `~/Developer/ipe_web_kit` 또는 `MONGSIL_WEB_KIT` 경로의 로컬 클론에서 준비합니다.

번역판을 넣는 글은 12개 언어판 모두에 `copy_review: iris` 및 `copy_review_date` 검수일을 적습니다. 기존 한국어·영어 원문 큐는 그대로 발행할 수 있습니다.

```sh
python3 ops/publish_next.py --queue ~/.ipe/queue/mongsil --dry-run
```

# KISTI ScienceON OpenAPI 통합 스펙 (Bucket H)

scholar-megasearch의 국내(한국어) 소스 버킷. KCI 등재 논문·국내 R&D 보고서·국내 특허를 검색한다.
구현: `scripts/kisti_client.py` · fallback CLI: `scripts/search_local.py kisti "질의"`.

## 자격증명 (환경변수 — 절대 커밋 금지)
| 변수 | 의미 |
|------|------|
| `KISTI_CLIENT_ID` | 발급받은 client_id |
| `KISTI_AUTH_KEY` | 발급받은 인증키(=AES-256 key, 32바이트) |
| `KISTI_MAC` | 토큰 발급 시 바인딩된 MAC 주소 |
| `KISTI_TARGET` (선택) | 검색 대상 한정(`arti,report,patent` 중, 기본 전체) |

토큰은 런타임에 발급하며 저장소에 보존하지 않는다.

## 토큰 발급 (검증됨 — 공식 샘플 `_vendor_kisti_token_sample/`)
- 발급: `GET https://apigateway.kisti.re.kr/tokenrequest.do?client_id=<id>&accounts=<enc>`
- `<enc>` = AES-256-CBC(plaintext, key=인증키, iv=`jvHJ1EFA0IXBrxxz` 고정, PKCS7 pad, block 16) → `base64.urlsafe_b64encode` → `urllib.parse.quote`
- plaintext = `{"datetime":"YYYYMMDDHHMMSS","mac_address":"<MAC>"}` (공백 제거, datetime은 숫자만)
- 응답 JSON: `{access_token, access_token_expire, refresh_token, refresh_token_expire, client_id, issued_at}`
- 재발급(선택): `GET .../tokenrequest.do?refreshToken=<rt>&client_id=<id>` (파라미터명 `refreshToken` 카멜케이스)

## 검색 API 스펙 — ⚠ Task 1에서 실응답으로 확정 (미완)
공식 문서 페이지:
- 논문: `https://scienceon.kisti.re.kr/apigateway/api/way/service/arti/serviceArtiSearchApi.do`
- 논문 상세: `.../service/arti/serviceArtiBrowseApi.do`
- 특허: `.../service/patent/servicePatentSearchApi.do`
- API Test: `https://scienceon.kisti.re.kr/por/api/apiTest/arti/`

아래는 확정 대상 — Task 1 실호출 후 정확한 값으로 교체한다:
- [ ] 검색 호출 엔드포인트 경로(`openapicall.do` 여부)와 access token 전달 방식(쿼리 `token=` vs 헤더)
- [ ] 검색 파라미터명: 검색어(`searchQuery`/`curQuery`?), `target`(ARTI/REPORT/PATENT), 건수(`displayCount`/`rowCount`?), 페이지(`curPage`?)
- [ ] XML 응답 레코드 element명과 필드(title/author/year/journal/DOI/abstract/link)

응답 포맷: XML. 커버리지: KCI 99%, SCI(E) 99.7%, SCOPUS 69.7%.

## 출처/보존
공식 토큰 샘플 원본: `references/_vendor_kisti_token_sample/{TokenSample.py,AES256Util.py}` (KISTI 제공).

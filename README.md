# 행정과정 시뮬레이션 (시연용)

사이드바에서 시나리오를 고른다. API 키 없이 실행하면 세 가지 모두 시연 모드로 동작한다.

- **공공재정관리 · 박물관 신축 예산 설득**: 부처 예산담당자 → 기획예산처 예산실 → 국회 전문위원 (예시 대화 재생)
- **전략관리 · 고용보험–국세청 소득정보 연계 협상**: 국세청 → 기획예산처 예산실 → 국회 환노위 여당 간사 (예시 대화 재생)
- **전략관리 · 애로우 불가능성 정리 시연**: 에이전트 3·4·5명, 집계는 코드가 계산 (AI 호출 없음)

## 내 PC에서 실행

```
pip install -r requirements.txt
python -m streamlit run app.py
```

## Streamlit Community Cloud 배포

1. 깃허브에 새 저장소를 만들고 이 폴더의 파일을 모두 올린다.
2. share.streamlit.io에 깃허브 계정으로 로그인한다.
3. Create app → 저장소, 브랜치(main), 실행 파일(app.py)을 지정하고 Deploy를 누른다.
4. 시연만 할 때는 Secrets를 비워 둔다.

실시간 AI 대화를 켜려면 Secrets에 `.streamlit/secrets.toml.example`의 내용을 넣는다.

## 파일

- `app.py` 화면과 진행
- `arrow_demo.py` 애로우 정리 시연
- `scenarios/` 설득·협상 시나리오(사례, 페르소나, 판단기준, 예시 대화)

"""애로우 불가능성 정리 시연 — 에이전트 3·4·5명.
선호 순위는 정리를 보여 주기 위해 설계한 것이며, 집계는 모두 코드가 계산한다(AI 호출 없음)."""
import pandas as pd
import streamlit as st

NAMES = {"A": "구조개혁", "B": "정책지원", "C": "문화변화", "D": "이민 확대"}
AV = {"경제학자": "📈", "사회학자": "👥", "정책전문가": "🏛️", "지자체 담당자": "🏙️", "청년 당사자": "🧑"}

CASES = {
    3: {
        "alts": "ABC",
        "agents": [
            ("경제학자", "ABC", "노동시장과 주거 구조를 바꾸지 않으면 지원금은 밑 빠진 독입니다."),
            ("사회학자", "CAB", "성평등과 일·생활 균형 문화가 먼저입니다. 돈만으로는 선택이 바뀌지 않습니다."),
            ("정책전문가", "BCA", "당장 체감되는 돌봄·현금 지원이 우선입니다. 구조개혁은 시간이 너무 걸립니다."),
        ],
    },
    4: {
        "alts": "ABCD",
        "agents": [
            ("경제학자", "ADBC", "구조개혁이 우선이고, 인구 문제는 이민으로 보완해야 합니다."),
            ("사회학자", "CADB", "문화가 바뀌어야 합니다. 그다음이 구조개혁입니다."),
            ("정책전문가", "BCAD", "정책지원이 가장 빠릅니다. 이민은 사회적 합의가 멉니다."),
            ("지자체 담당자", "BACD", "현장에서는 지원 사업이 가장 급합니다. 이민은 지역에서 감당하기 어렵습니다."),
        ],
    },
    5: {
        "alts": "ABCD",
        "agents": [
            ("경제학자", "ADBC", "구조개혁이 우선이고, 인구 문제는 이민으로 보완해야 합니다."),
            ("사회학자", "CADB", "문화가 바뀌어야 합니다. 그다음이 구조개혁입니다."),
            ("정책전문가", "BCAD", "정책지원이 가장 빠릅니다. 이민은 사회적 합의가 멉니다."),
            ("지자체 담당자", "BACD", "현장에서는 지원 사업이 가장 급합니다."),
            ("청년 당사자", "CABD", "일하면서 아이를 키울 수 있는 문화가 아니면 소용없습니다."),
        ],
        "liar": 2, "lie": "CBDA",
    },
}


# ── 집계 함수 ───────────────────────────────────────────
def prefers(rank, a, b):
    return rank.index(a) < rank.index(b)


def pair_count(prof, a, b):
    return sum(prefers(r, a, b) for r in prof)


def borda(prof, alts):
    sc = {a: 0 for a in alts}
    for r in prof:
        rr = [a for a in r if a in alts]
        for i, a in enumerate(rr):
            sc[a] += len(rr) - 1 - i
    return sc


def plurality(prof, alts):
    sc = {a: 0 for a in alts}
    for r in prof:
        sc[[a for a in r if a in alts][0]] += 1
    return sc


def winner(sc):
    m = max(sc.values())
    w = [a for a in sc if sc[a] == m]
    return w[0] if len(w) == 1 else None


def agenda_winner(prof, order):
    cur = order[0]
    for nxt in order[1:]:
        cur = cur if pair_count(prof, cur, nxt) > len(prof) / 2 else nxt
    return cur


def fmt(rank):
    return "  >  ".join(NAMES[a] for a in rank)


def score_chart(sc, label):
    df = pd.DataFrame({label: [sc[a] for a in sc]}, index=[NAMES[a] for a in sc])
    st.bar_chart(df, height=220)


def speak(agents):
    for name, rank, line in agents:
        with st.chat_message("assistant", avatar=AV[name]):
            st.markdown(f"**{name}**  {line}")
            st.caption(f"선호 순위: {fmt(rank)}")


# ── 3명: 순환과 의제 조작 ───────────────────────────────
def case3(step):
    c = CASES[3]; prof = [a[1] for a in c["agents"]]
    st.subheader("① 세 에이전트의 주장과 선호")
    speak(c["agents"])
    st.info("각 에이전트의 선호는 내부적으로 일관됩니다(이행성 충족).")
    if step < 2: return
    st.subheader("② 두 대안씩 다수결에 부치면")
    rows = []
    for a, b in [("A", "B"), ("B", "C"), ("C", "A")]:
        n = pair_count(prof, a, b)
        rows.append({"대결": f"{NAMES[a]} 대 {NAMES[b]}", "득표": f"{n} : {len(prof) - n}", "승자": NAMES[a if n > len(prof) / 2 else b]})
    l, r = st.columns([3, 2])
    l.table(pd.DataFrame(rows).set_index("대결"))
    r.graphviz_chart('digraph{rankdir=LR; node[shape=box,style="rounded,filled",fillcolor="#EFF2F8",color="#003A8E",fontname="sans-serif"];'
                     'edge[color="#003A8E"]; "구조개혁"->"정책지원"->"문화변화"->"구조개혁"}')
    st.error("구조개혁 > 정책지원 > 문화변화 > 구조개혁. 사회 전체의 선호가 순환해 1위를 정할 수 없습니다.")
    if step < 3: return
    st.subheader("③ 표결 순서를 정하는 사람이 결과를 정한다")
    rows = []
    for order in ["ABC", "BCA", "CAB"]:
        w = agenda_winner(prof, order)
        rows.append({"표결 순서": f"{NAMES[order[0]]} 대 {NAMES[order[1]]}, 승자가 {NAMES[order[2]]}와 대결", "최종 승자": NAMES[w]})
    st.table(pd.DataFrame(rows).set_index("표결 순서"))
    st.warning("같은 선호, 같은 다수결인데 의제 순서에 따라 세 대안이 모두 승자가 될 수 있습니다.")
    if step < 4: return
    st.subheader("④ 정리")
    st.success("개인은 합리적이어도 다수결로 합친 집단의 선호는 합리적이지 않을 수 있습니다. "
               "쌍대 다수결은 **이행성**을 지키지 못합니다.")


# ── 4명: 규칙에 따라 달라지는 승자, IIA 위반 ────────────
def case4(step):
    c = CASES[4]; prof = [a[1] for a in c["agents"]]; alts = c["alts"]
    st.subheader("① 네 에이전트의 주장과 선호")
    st.caption("대안에 '이민 확대'가 추가되고, 지자체 담당자가 참여합니다.")
    speak(c["agents"])
    if step < 2: return
    st.subheader("② 순환을 피하려고 집계 규칙을 바꾸면")
    p, b = plurality(prof, alts), borda(prof, alts)
    l, r = st.columns(2)
    with l:
        st.markdown(f"**최다득표제** (1순위 표만 계산) → 승자: **{NAMES[winner(p)]}**")
        score_chart(p, "1순위 득표")
    with r:
        st.markdown(f"**보르다 점수제** (순위마다 점수 부여) → 승자: **{NAMES[winner(b)]}**")
        score_chart(b, "보르다 점수")
    st.warning("선호는 그대로인데 집계 규칙에 따라 승자가 달라집니다.")
    if step < 3: return
    st.subheader("③ 보르다 점수제에서 '이민 확대'를 의제에서 빼면")
    rest = [a for a in alts if a != "D"]; b2 = borda(prof, rest)
    l, r = st.columns(2)
    with l:
        st.markdown(f"**이민 확대 포함** → 승자: **{NAMES[winner(b)]}**")
        score_chart(b, "보르다 점수")
    with r:
        st.markdown(f"**이민 확대 제외** → 승자: **{NAMES[winner(b2)]}**")
        score_chart(b2, "보르다 점수")
    n = pair_count(prof, "A", "B")
    st.error(f"구조개혁과 정책지원 사이의 선호는 아무도 바꾸지 않았습니다({n}명 대 {len(prof) - n}명 그대로). "
             "그런데 무관한 대안 하나를 빼자 둘의 순위가 뒤집혔습니다.")
    if step < 4: return
    st.subheader("④ 정리")
    st.success("보르다 점수제는 순환을 만들지 않지만 **무관한 대안으로부터의 독립성(IIA)** 을 지키지 못합니다. "
               "어떤 대안을 의제에 올리느냐로 결과를 바꿀 수 있습니다.")


# ── 5명: 전략적 허위 표명, 독재 ─────────────────────────
def case5(step):
    c = CASES[5]; prof = [a[1] for a in c["agents"]]; alts = c["alts"]
    st.subheader("① 다섯 에이전트의 주장과 선호")
    st.caption("청년 당사자가 참여합니다.")
    speak(c["agents"])
    if step < 2: return
    st.subheader("② 보르다 점수제로 집계")
    b = borda(prof, alts)
    st.markdown(f"승자: **{NAMES[winner(b)]}**")
    score_chart(b, "보르다 점수")
    if step < 3: return
    i, lie = c["liar"], c["lie"]; name, true, _ = c["agents"][i]
    st.subheader(f"③ {name}가 선호를 거짓으로 말하면")
    with st.chat_message("assistant", avatar=AV[name]):
        st.markdown(f"**{name}의 속마음**  내 1순위인 정책지원은 어차피 안 됩니다. 구조개혁이 되는 것보다는 문화변화가 낫습니다. "
                    "문화변화를 1순위로, 구조개혁을 꼴찌로 적어 내겠습니다.")
        st.caption(f"실제 선호: {fmt(true)}")
        st.caption(f"표명한 선호: {fmt(lie)}")
    p2 = list(prof); p2[i] = lie; b2 = borda(p2, alts)
    l, r = st.columns(2)
    with l:
        st.markdown(f"**정직하게 표명** → 승자: **{NAMES[winner(b)]}**")
        score_chart(b, "보르다 점수")
    with r:
        st.markdown(f"**거짓으로 표명** → 승자: **{NAMES[winner(b2)]}**")
        score_chart(b2, "보르다 점수")
    st.error(f"{name}는 거짓말로 자신에게 더 나은 결과({NAMES[winner(b2)]})를 얻었습니다. "
             "규칙이 정직한 선호 표명을 보장하지 못합니다.")
    if step < 4: return
    st.subheader("④ 그렇다면 모든 조건을 지키는 규칙은?")
    st.markdown(f"**독재 규칙**: 경제학자의 순위를 그대로 사회의 순위로 채택 → {fmt(prof[0])}")
    df = pd.DataFrame(
        {"이행성": ["✗ 순환 발생", "✓", "✓"], "파레토 원칙": ["✓", "✓", "✓"],
         "무관한 대안으로부터의 독립성": ["✓", "✗ 의제에 따라 역전", "✓"], "비독재성": ["✓", "✓", "✗"]},
        index=["쌍대 다수결", "보르다 점수제", "독재 규칙"])
    st.table(df)
    st.success("**애로우의 불가능성 정리(1951)**: 대안이 셋 이상일 때 이행성, 파레토 원칙, 무관한 대안으로부터의 독립성을 "
               "모두 지키는 집계 규칙은 독재뿐입니다.")
    st.info("**토론** 합의 실패는 참여자의 무능이나 악의 때문이 아니라 집계 구조에서 비롯됩니다. "
            "그래서 현실의 정책 결정은 투표가 아니라 협상, 중재, 의제 설정 규칙 같은 제도 설계에 의존합니다.")


def render():
    ss = st.session_state
    st.title("🗳️ 애로우 불가능성 정리 시연")
    st.caption("저출산 대책의 우선순위 정하기 · 에이전트 수를 늘려 가며 집계 규칙의 한계를 확인 · 선호는 시연용 설계, 집계는 코드가 계산")
    n = st.radio("에이전트 수", [3, 4, 5], horizontal=True,
                 format_func=lambda k: {3: "3명 · 다수결의 순환", 4: "4명 · 규칙과 의제에 따른 역전", 5: "5명 · 거짓 표명과 독재"}[k])
    key = f"arrow_step_{n}"
    ss.setdefault(key, 1)
    {3: case3, 4: case4, 5: case5}[n](ss[key])
    st.divider()
    l, r, _ = st.columns([1, 1, 4])
    if ss[key] < 4 and l.button("다음 단계 ▶", type="primary"):
        ss[key] += 1
        st.rerun()
    if ss[key] > 1 and r.button("처음부터"):
        ss[key] = 1
        st.rerun()

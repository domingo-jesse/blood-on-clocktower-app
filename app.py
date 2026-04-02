import math
from dataclasses import dataclass
from html import escape
from textwrap import dedent
from typing import Dict, List

import streamlit as st

st.set_page_config(page_title="Blood on the Clocktower Assistant", layout="wide")

ALIGNMENTS = ["Unknown", "Good", "Evil"]
REMINDER_KEYS = ["poisoned", "drunk", "safe", "protected", "no_ability", "resurrected", "cursed"]
QUICK_TAG_OPTIONS = [
    "claims X",
    "hard claim",
    "bluffing",
    "suspicious",
    "confirmed",
    "lied",
    "first night info",
    "nominated",
    "voted",
    "executed",
    "died at night",
    "probably demon",
    "probably minion",
    "probably outsider",
    "probably townsfolk",
]

@dataclass
class Player:
    seat: int
    name: str
    pronouns: str
    alive: bool
    alignment: str
    notes: str
    quick_tags: List[str]
    reminders: Dict[str, bool]
    suspicion: int


def default_player(seat: int) -> Player:
    return Player(
        seat=seat,
        name=f"Player {seat}",
        pronouns="",
        alive=True,
        alignment="Unknown",
        notes="",
        quick_tags=[],
        reminders={key: False for key in REMINDER_KEYS},
        suspicion=1,
    )


def fuzzy_includes(query: str, value: str) -> bool:
    q = query.lower().strip()
    if not q:
        return True
    source = value.lower()
    idx = 0
    for ch in source:
        if idx < len(q) and ch == q[idx]:
            idx += 1
        if idx >= len(q):
            return True
    return False


def render_grimoire_circle(players: List[Player], selected_seat: int | None) -> None:
    count = len(players)
    if count == 0:
        return

    center = 50
    radius = max(26, min(34, 44 - count))
    seat_markup = []

    for idx, player in enumerate(players):
        angle_deg = -90 + (360 / count) * idx
        angle = math.radians(angle_deg)
        x = center + radius * math.cos(angle)
        y = center + radius * math.sin(angle)
        initials = "".join(part[0] for part in player.name.split()[:2]).upper() if player.name.strip() else str(player.seat)
        alive_class = "alive" if player.alive else "dead"
        pronouns = f"<div class='grim-pronouns'>{escape(player.pronouns)}</div>" if player.pronouns.strip() else ""
        is_selected = "selected" if selected_seat == player.seat else ""
        seat_markup.append(
            (
                f'<a class="grim-seat-link" href="?seat={player.seat}">'
                f'<div class="grim-seat-wrapper" style="left:{x:.2f}%; top:{y:.2f}%;">'
                f'<div class="grim-token {alive_class} {is_selected}"><span>{escape(initials)}</span></div>'
                f'<div class="grim-name">{escape(player.name)}</div>'
                f"{pronouns}"
                "</div></a>"
            )
        )

    st.markdown(
        dedent(
            """
            <style>
                .grim-board {
                    width: min(76vw, 820px);
                    aspect-ratio: 1 / 1;
                    margin: 0 auto 1.6rem auto;
                    border-radius: 999px;
                    position: relative;
                    overflow: visible;
                    background: radial-gradient(circle at center, #2b0d3a 0%, #15051f 68%, #09020f 100%);
                    border: 2px solid #3f2853;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.45), inset 0 0 90px rgba(255, 255, 255, 0.04);
                }
                .grim-center {
                    position: absolute;
                    inset: 39% 39%;
                    border-radius: 999px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #f4e9d8;
                    font-weight: 700;
                    font-size: clamp(0.75rem, 1.2vw, 1rem);
                    letter-spacing: 0.05em;
                    text-transform: uppercase;
                    background: rgba(0, 0, 0, 0.35);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                }
                .grim-seat-link {
                    color: inherit;
                    text-decoration: none;
                    position: absolute;
                    inset: 0;
                }
                .grim-seat-wrapper {
                    position: absolute;
                    transform: translate(-50%, -50%);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    width: 98px;
                    z-index: 3;
                }
                .grim-token {
                    width: clamp(44px, 5.2vw, 58px);
                    height: clamp(44px, 5.2vw, 58px);
                    border-radius: 999px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #26170d;
                    font-weight: 700;
                    background: radial-gradient(circle at 35% 30%, #fff6dd 0%, #e6d5ad 65%, #c7b183 100%);
                    border: 2px solid #2f1f10;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
                }
                .grim-token.selected {
                    box-shadow: 0 0 0 3px #6ce5ff, 0 0 18px rgba(108, 229, 255, 0.7);
                }
                .grim-token.dead {
                    filter: grayscale(1);
                    opacity: 0.7;
                    border-color: #7d7d7d;
                }
                .grim-name {
                    margin-top: 0.45rem;
                    font-size: clamp(0.66rem, 0.9vw, 0.8rem);
                    color: #ffffff;
                    font-weight: 600;
                    text-align: center;
                    line-height: 1.1;
                    text-shadow: 0 1px 4px rgba(0, 0, 0, 0.7);
                }
                .grim-pronouns {
                    margin-top: 0.1rem;
                    font-size: 0.72rem;
                    color: #d0c0de;
                    text-align: center;
                    line-height: 1.05;
                }
                @media (max-width: 900px) {
                    .grim-seat-wrapper { width: 80px; }
                    .grim-token { font-size: 0.82rem; }
                    .grim-name { font-size: 0.7rem; }
                    .grim-pronouns { font-size: 0.68rem; }
                }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        dedent(
            f"""
            <div class="grim-board">
                <div class="grim-center">Storyteller</div>
                {''.join(seat_markup)}
            </div>
            """
        ),
        unsafe_allow_html=True,
    )


if "players" not in st.session_state:
    st.session_state.players = [default_player(seat) for seat in range(1, 13)]
if "selected_seat" not in st.session_state:
    st.session_state.selected_seat = None

players: List[Player] = st.session_state.players

st.title("🩸 Blood on the Clocktower Notes")

query_params = st.query_params
if "seat" in query_params:
    try:
        seat_from_query = int(query_params["seat"])
        if any(p.seat == seat_from_query for p in players):
            st.session_state.selected_seat = seat_from_query
    except (ValueError, TypeError):
        pass

st.divider()
render_grimoire_circle(players, st.session_state.selected_seat)
st.caption("Live seat layout: players are arranged in a circle with names under each token.")

query = st.text_input("Search players / notes / tags")
filtered_players = []
for p in players:
    haystack = " ".join(
        [
            p.name,
            p.pronouns,
            p.notes,
            " ".join(p.quick_tags),
        ]
    )
    if fuzzy_includes(query, haystack):
        filtered_players.append(p)

if query.strip():
    st.write(f"{len(filtered_players)} result(s)")

selected = next((p for p in players if p.seat == st.session_state.selected_seat), None)
if selected is not None:
    st.info(f"**Suspicion:** {selected.suspicion}/5")
else:
    st.info("**Suspicion:** Select a player token")

with st.container():
    if selected is None:
        st.info("Click a player token in the circle above to edit that player below the grim.")
    else:
        st.subheader(f"Seat {selected.seat} details")
        if st.button("Clear selection"):
            st.session_state.selected_seat = None
            st.query_params.clear()
            st.rerun()

        selected.name = st.text_input("Name", value=selected.name)
        selected.pronouns = st.text_input("Pronouns", value=selected.pronouns)
        identity_cols = st.columns(3)
        selected.alive = identity_cols[0].toggle("Alive", value=selected.alive)
        selected.alignment = identity_cols[1].selectbox("Alignment", ALIGNMENTS, index=ALIGNMENTS.index(selected.alignment))
        selected.suspicion = identity_cols[2].slider("Suspicion", 1, 5, value=selected.suspicion)

        selected.quick_tags = st.multiselect("Quick tags", QUICK_TAG_OPTIONS, default=selected.quick_tags)
        selected.notes = st.text_area("Notes", value=selected.notes, height=140)

        selected_idx = next(i for i, p in enumerate(players) if p.seat == selected.seat)
        players[selected_idx] = selected

st.session_state.players = players

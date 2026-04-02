import json
import math
from dataclasses import asdict, dataclass
from html import escape
from io import StringIO
from textwrap import dedent
from typing import Dict, List

import streamlit as st

st.set_page_config(page_title="Blood on the Clocktower Assistant", layout="wide")

TEAMS = ["Townsfolk", "Outsider", "Minion", "Demon", "Traveller"]
ALIGNMENTS = ["Unknown", "Good", "Evil"]
CONFIDENCE_LEVELS = ["Low", "Medium", "High"]
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

CHARACTER_POOL = [
    {"name": "Washerwoman", "team": "Townsfolk", "ability": "Learns one of two players is a particular Townsfolk."},
    {"name": "Librarian", "team": "Townsfolk", "ability": "Learns one of two players is a particular Outsider."},
    {"name": "Undertaker", "team": "Townsfolk", "ability": "Learns the character of the executed player."},
    {"name": "Empath", "team": "Townsfolk", "ability": "Learns how many evil neighbors they have."},
    {"name": "Fortune Teller", "team": "Townsfolk", "ability": "Picks two players and learns if one is the Demon."},
    {"name": "Ravenkeeper", "team": "Townsfolk", "ability": "If killed at night, learns another player’s character."},
    {"name": "Saint", "team": "Outsider", "ability": "If executed, good loses."},
    {"name": "Recluse", "team": "Outsider", "ability": "May register as evil and as a Minion or Demon."},
    {"name": "Drunk", "team": "Outsider", "ability": "You think you are a Townsfolk but are not."},
    {"name": "Poisoner", "team": "Minion", "ability": "Poisons a player each night."},
    {"name": "Spy", "team": "Minion", "ability": "Sees the grim each night and might register as good."},
    {"name": "Scarlet Woman", "team": "Minion", "ability": "Becomes Demon if Demon dies with 5+ players alive."},
    {"name": "Imp", "team": "Demon", "ability": "Kills a player each night and may pass Demonhood on self-kill."},
    {"name": "No Dashii", "team": "Demon", "ability": "Poisons Townsfolk neighbors and kills nightly."},
    {"name": "Vortox", "team": "Demon", "ability": "Good info is false, and an execution must occur daily."},
    {"name": "Gunslinger", "team": "Traveller", "ability": "May publicly execute a player once per game."},
]


@dataclass
class CharacterSlot:
    name: str = ""
    confidence: str = "Medium"
    note: str = ""


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
    possibilities: List[CharacterSlot]


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
        possibilities=[CharacterSlot(), CharacterSlot(), CharacterSlot()],
    )


def to_dict(players: List[Player]) -> List[dict]:
    out = []
    for player in players:
        record = asdict(player)
        out.append(record)
    return out


def from_dict(raw_players: List[dict]) -> List[Player]:
    players: List[Player] = []
    for raw in raw_players:
        possibilities = [CharacterSlot(**slot) for slot in raw.get("possibilities", [])][:3]
        while len(possibilities) < 3:
            possibilities.append(CharacterSlot())
        reminders = {key: bool(raw.get("reminders", {}).get(key, False)) for key in REMINDER_KEYS}
        players.append(
            Player(
                seat=int(raw.get("seat", len(players) + 1)),
                name=str(raw.get("name", f"Player {len(players) + 1}")),
                pronouns=str(raw.get("pronouns", "")),
                alive=bool(raw.get("alive", True)),
                alignment=raw.get("alignment", "Unknown") if raw.get("alignment", "Unknown") in ALIGNMENTS else "Unknown",
                notes=str(raw.get("notes", "")),
                quick_tags=[tag for tag in raw.get("quick_tags", []) if tag in QUICK_TAG_OPTIONS],
                reminders=reminders,
                suspicion=max(1, min(5, int(raw.get("suspicion", 1)))),
                possibilities=possibilities,
            )
        )
    return players


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
    radius = 38
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
            f"""
            <a class="grim-seat-link" href="?seat={player.seat}">
                <div class="grim-seat-wrapper" style="left:{x:.2f}%; top:{y:.2f}%;">
                    <div class="grim-token {alive_class} {is_selected}">
                        <span>{escape(initials)}</span>
                    </div>
                    <div class="grim-name">{escape(player.name)}</div>
                    {pronouns}
                </div>
            </a>
            """
        )

    st.markdown(
        dedent(
            """
            <style>
                .grim-board {
                    width: min(72vw, 760px);
                    aspect-ratio: 1 / 1;
                    margin: 0 auto 1rem auto;
                    border-radius: 999px;
                    position: relative;
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
                }
                .grim-seat-wrapper {
                    position: absolute;
                    transform: translate(-50%, -50%);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    width: 92px;
                }
                .grim-token {
                    width: 60px;
                    height: 60px;
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
                    font-size: 0.82rem;
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
                    .grim-seat-wrapper { width: 78px; }
                    .grim-token { width: 52px; height: 52px; font-size: 0.82rem; }
                    .grim-name { font-size: 0.74rem; }
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
if "meta_title" not in st.session_state:
    st.session_state.meta_title = "Trouble Brewing"
if "meta_edition" not in st.session_state:
    st.session_state.meta_edition = "Standard"
if "selected_seat" not in st.session_state:
    st.session_state.selected_seat = None

players: List[Player] = st.session_state.players

st.title("🩸 Blood on the Clocktower Notes")
st.caption("Python + Streamlit build for quick game-state tracking and theory notes.")

with st.sidebar:
    st.subheader("Game info")
    st.session_state.meta_title = st.text_input("Script", value=st.session_state.meta_title)
    st.session_state.meta_edition = st.text_input("Edition", value=st.session_state.meta_edition)

    alive_count = sum(1 for p in players if p.alive)
    reminder_count = sum(sum(1 for v in p.reminders.values() if v) for p in players)

    st.metric("Players alive", alive_count)
    st.metric("Active reminders", reminder_count)

    st.subheader("Save / load")
    export_blob = {
        "title": st.session_state.meta_title,
        "edition": st.session_state.meta_edition,
        "players": to_dict(players),
    }
    st.download_button(
        "Download game JSON",
        data=json.dumps(export_blob, indent=2),
        file_name="clocktower_game_state.json",
        mime="application/json",
        use_container_width=True,
    )

    uploaded = st.file_uploader("Load game JSON", type=["json"])
    if uploaded is not None:
        data = json.load(StringIO(uploaded.getvalue().decode("utf-8")))
        st.session_state.meta_title = data.get("title", "Trouble Brewing")
        st.session_state.meta_edition = data.get("edition", "Standard")
        st.session_state.players = from_dict(data.get("players", []))
        if not st.session_state.players:
            st.session_state.players = [default_player(seat) for seat in range(1, 13)]
        st.session_state.selected_seat = None
        st.success("Imported game state.")
        st.rerun()

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

query = st.text_input("Search players / notes / tags / possibilities")
filtered_players = []
for p in players:
    haystack = " ".join(
        [
            p.name,
            p.pronouns,
            p.notes,
            " ".join(p.quick_tags),
            " ".join(slot.name for slot in p.possibilities),
        ]
    )
    if fuzzy_includes(query, haystack):
        filtered_players.append(p)

if query.strip():
    st.write(f"{len(filtered_players)} result(s)")

selected = next((p for p in players if p.seat == st.session_state.selected_seat), None)

summary_cols = st.columns(3)
summary_cols[0].info(f"**Script:** {st.session_state.meta_title}")
summary_cols[1].info(f"**Edition:** {st.session_state.meta_edition}")
if selected is not None:
    summary_cols[2].info(f"**Suspicion:** {selected.suspicion}/5")
else:
    summary_cols[2].info("**Suspicion:** Select a player token")

roster_col, editor_col = st.columns([1.1, 1.7], gap="large")

with roster_col:
    st.subheader("Roster")
    for p in filtered_players if query.strip() else players:
        badge = "🟢" if p.alive else "💀"
        st.markdown(f"**Seat {p.seat}** · {badge} {p.name}  ")
        st.caption(f"{p.alignment} · Tags: {', '.join(p.quick_tags) if p.quick_tags else 'none'}")

with editor_col:
    if selected is None:
        st.subheader("Player details")
        st.info("Click a player token in the circle above to open and edit that player's information.")
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

        st.markdown("#### Reminders")
        reminder_cols = st.columns(len(REMINDER_KEYS))
        for idx, key in enumerate(REMINDER_KEYS):
            reminder_cols[idx].checkbox(key.replace("_", " ").title(), key=f"{selected.seat}-{key}", value=selected.reminders.get(key, False), on_change=None)
            selected.reminders[key] = st.session_state[f"{selected.seat}-{key}"]

        st.markdown("#### Possible characters")
        for idx, slot in enumerate(selected.possibilities):
            with st.expander(f"Possibility {idx + 1}", expanded=True):
                team_filter = st.selectbox(
                    "Team filter",
                    ["All", *TEAMS],
                    key=f"team-filter-{selected.seat}-{idx}",
                )
                pool = CHARACTER_POOL if team_filter == "All" else [c for c in CHARACTER_POOL if c["team"] == team_filter]
                option_names = [""] + [c["name"] for c in pool]
                if slot.name and slot.name not in option_names:
                    option_names.append(slot.name)
                slot.name = st.selectbox(
                    "Character",
                    option_names,
                    index=option_names.index(slot.name) if slot.name in option_names else 0,
                    key=f"char-{selected.seat}-{idx}",
                )
                slot.confidence = st.selectbox(
                    "Confidence",
                    CONFIDENCE_LEVELS,
                    index=CONFIDENCE_LEVELS.index(slot.confidence),
                    key=f"conf-{selected.seat}-{idx}",
                )
                slot.note = st.text_area(
                    "Reasoning",
                    value=slot.note,
                    key=f"slot-note-{selected.seat}-{idx}",
                )

        selected_idx = next(i for i, p in enumerate(players) if p.seat == selected.seat)
        players[selected_idx] = selected

st.session_state.players = players

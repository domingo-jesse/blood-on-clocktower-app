import math
from dataclasses import dataclass
from html import escape
from textwrap import dedent
from typing import Dict, List

import streamlit as st

st.set_page_config(page_title="Blood on the Clocktower Assistant", layout="wide")

ALIGNMENTS = ["Unknown", "Good", "Evil"]
ROLE_OPTIONS = sorted(
    [
        # Trouble Brewing
        "Washerwoman",
        "Librarian",
        "Investigator",
        "Chef",
        "Empath",
        "Fortune Teller",
        "Undertaker",
        "Monk",
        "Ravenkeeper",
        "Virgin",
        "Slayer",
        "Soldier",
        "Mayor",
        "Butler",
        "Drunk",
        "Recluse",
        "Saint",
        "Poisoner",
        "Spy",
        "Scarlet Woman",
        "Baron",
        "Imp",
        # Bad Moon Rising
        "Grandmother",
        "Sailor",
        "Chambermaid",
        "Exorcist",
        "Innkeeper",
        "Gambler",
        "Gossip",
        "Courtier",
        "Professor",
        "Minstrel",
        "Tea Lady",
        "Pacifist",
        "Fool",
        "Tinker",
        "Moonchild",
        "Goon",
        "Lunatic",
        "Godfather",
        "Devil's Advocate",
        "Assassin",
        "Mastermind",
        "Zombuul",
        "Pukka",
        "Shabaloth",
        "Po",
        # Sects & Violets
        "Clockmaker",
        "Dreamer",
        "Snake Charmer",
        "Mathematician",
        "Flowergirl",
        "Town Crier",
        "Oracle",
        "Savant",
        "Seamstress",
        "Philosopher",
        "Artist",
        "Juggler",
        "Sage",
        "Mutant",
        "Sweetheart",
        "Barber",
        "Klutz",
        "Evil Twin",
        "Witch",
        "Cerenovus",
        "Pit-Hag",
        "Fang Gu",
        "Vigormortis",
        "No Dashii",
        "Vortox",
        # Travellers
        "Beggar",
        "Bishop",
        "Bureaucrat",
        "Bone Collector",
        "Butcher",
        "Deviant",
        "Fool (Traveller)",
        "Gangster",
        "Gunslinger",
        "Harlot",
        "Judge",
        "Matron",
        "Scapegoat",
        "Thief",
    ]
)
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
    role: str
    alive: bool
    dead_vote_used: bool
    alignment: str
    notes: str
    quick_tags: List[str]
    reminders: Dict[str, bool]
    suspicion: int


def default_player(seat: int) -> Player:
    return Player(
        seat=seat,
        name=f"Player {seat}",
        role="",
        alive=True,
        dead_vote_used=False,
        alignment="Unknown",
        notes="",
        quick_tags=[],
        reminders={key: False for key in REMINDER_KEYS},
        suspicion=1,
    )


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
        dead_vote_class = "dead-vote-used" if (not player.alive and player.dead_vote_used) else ""
        role_markup = f"<div class='grim-role'>{escape(player.role)}</div>" if player.role.strip() else ""
        is_selected = "selected" if selected_seat == player.seat else ""
        seat_markup.append(
            (
                f'<div class="grim-seat-wrapper" style="left:{x:.2f}%; top:{y:.2f}%;">'
                f'<div class="grim-token {alive_class} {dead_vote_class} {is_selected}"><span>{escape(initials)}</span></div>'
                f'<div class="grim-name">{escape(player.name)}</div>'
                f"{role_markup}"
                "</div>"
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
                    background: radial-gradient(circle at 35% 30%, #262626 0%, #111111 65%, #000000 100%);
                    color: #f0f0f0;
                    border-color: #7d7d7d;
                }
                .grim-token.dead-vote-used::after {
                    content: "✕";
                    position: absolute;
                    inset: 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: #ff2c2c;
                    font-size: clamp(1.8rem, 4.6vw, 2.8rem);
                    text-shadow: 0 0 6px rgba(0, 0, 0, 0.9);
                    font-weight: 900;
                    pointer-events: none;
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
                .grim-role {
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
                    .grim-role { font-size: 0.68rem; }
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
# Backward compatibility for old saved session objects.
for player in players:
    if not hasattr(player, "role"):
        player.role = ""
    if not hasattr(player, "dead_vote_used"):
        player.dead_vote_used = False

st.title("🩸 Blood on the Clocktower Notes")

st.divider()
render_grimoire_circle(players, st.session_state.selected_seat)
st.caption("Live seat layout: players are arranged in a circle with names under each token.")

st.write("Select a token below to edit details under the grim:")
tokens_per_row = 6
for row_start in range(0, len(players), tokens_per_row):
    row_players = players[row_start : row_start + tokens_per_row]
    row_cols = st.columns(tokens_per_row)
    for col_idx, player in enumerate(row_players):
        initials = "".join(part[0] for part in player.name.split()[:2]).upper() if player.name.strip() else str(player.seat)
        label = f"{player.seat}: {initials}"
        if row_cols[col_idx].button(label, key=f"seat_btn_{player.seat}", use_container_width=True):
            st.session_state.selected_seat = player.seat

selected = next((p for p in players if p.seat == st.session_state.selected_seat), None)
if selected is not None:
    st.info(f"**Suspicion:** {selected.suspicion}/5")
else:
    st.info("**Suspicion:** Select a player token")

with st.container():
    if selected is None:
        st.info("Select a token above to edit that player below the grim.")
    else:
        st.subheader(f"Seat {selected.seat} details")
        if st.button("Clear selection"):
            st.session_state.selected_seat = None
            st.rerun()

        selected.name = st.text_input("Name", value=selected.name)
        selected.role = st.selectbox(
            "Role (searchable)",
            [""] + ROLE_OPTIONS,
            index=([""] + ROLE_OPTIONS).index(selected.role) if selected.role in ROLE_OPTIONS else 0,
            format_func=lambda role: role if role else "Select role",
        )
        status_cols = st.columns(2)
        previous_alive = selected.alive
        previous_dead_vote_used = selected.dead_vote_used
        is_dead = status_cols[0].toggle("Dead", value=not selected.alive)
        selected.alive = not is_dead
        selected.dead_vote_used = status_cols[1].toggle(
            "Dead vote used",
            value=selected.dead_vote_used,
            disabled=selected.alive,
            help="Enable this only after a player is dead and has spent their ghost vote.",
        )

        detail_cols = st.columns(2)
        selected.alignment = detail_cols[0].selectbox("Alignment", ALIGNMENTS, index=ALIGNMENTS.index(selected.alignment))
        selected.suspicion = detail_cols[1].slider("Suspicion", 1, 5, value=selected.suspicion)

        selected.quick_tags = st.multiselect("Quick tags", QUICK_TAG_OPTIONS, default=selected.quick_tags)
        selected.notes = st.text_area("Notes", value=selected.notes, height=140)

        selected_idx = next(i for i, p in enumerate(players) if p.seat == selected.seat)
        players[selected_idx] = selected

        if (selected.alive != previous_alive) or (selected.dead_vote_used != previous_dead_vote_used):
            st.rerun()

st.session_state.players = players

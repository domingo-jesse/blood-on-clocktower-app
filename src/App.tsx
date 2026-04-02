import { Search, Skull, Sparkles, ShieldCheck, FlaskConical, HeartPulse, CircleDashed } from 'lucide-react';
import { type Dispatch, type ReactNode, type SetStateAction, useEffect, useMemo, useState } from 'react';

type Team = 'Townsfolk' | 'Outsider' | 'Minion' | 'Demon' | 'Traveller';
type Alignment = 'Unknown' | 'Good' | 'Evil';
type Confidence = 'Low' | 'Medium' | 'High';

type CharacterOption = {
  name: string;
  team: Team;
  ability: string;
};

type CharacterSlot = {
  name: string;
  confidence: Confidence;
  note: string;
};

type ReminderKey = 'poisoned' | 'drunk' | 'safe' | 'protected' | 'noAbility' | 'resurrected' | 'cursed';

type Player = {
  id: string;
  seat: number;
  name: string;
  pronouns: string;
  alive: boolean;
  alignment: Alignment;
  notes: string;
  quickTags: string[];
  reminders: Record<ReminderKey, boolean>;
  suspicion: number;
  possibilities: [CharacterSlot, CharacterSlot, CharacterSlot];
};

type GameMeta = {
  title: string;
  edition: string;
};

const quickTagOptions = [
  'claims X', 'hard claim', 'bluffing', 'suspicious', 'confirmed', 'lied', 'first night info', 'nominated',
  'voted', 'executed', 'died at night', 'probably demon', 'probably minion', 'probably outsider', 'probably townsfolk',
];

const characterPool: CharacterOption[] = [
  { name: 'Washerwoman', team: 'Townsfolk', ability: 'Learns one of two players is a particular Townsfolk.' },
  { name: 'Librarian', team: 'Townsfolk', ability: 'Learns one of two players is a particular Outsider.' },
  { name: 'Undertaker', team: 'Townsfolk', ability: 'Learns the character of the executed player.' },
  { name: 'Empath', team: 'Townsfolk', ability: 'Learns how many evil neighbors they have.' },
  { name: 'Fortune Teller', team: 'Townsfolk', ability: 'Picks two players and learns if one is the Demon.' },
  { name: 'Ravenkeeper', team: 'Townsfolk', ability: 'If killed at night, learns another player’s character.' },
  { name: 'Saint', team: 'Outsider', ability: 'If executed, good loses.' },
  { name: 'Recluse', team: 'Outsider', ability: 'May register as evil and as a Minion or Demon.' },
  { name: 'Drunk', team: 'Outsider', ability: 'You think you are a Townsfolk but are not.' },
  { name: 'Poisoner', team: 'Minion', ability: 'Poisons a player each night.' },
  { name: 'Spy', team: 'Minion', ability: 'Sees the grim each night and might register as good.' },
  { name: 'Scarlet Woman', team: 'Minion', ability: 'Becomes Demon if Demon dies with 5+ players alive.' },
  { name: 'Imp', team: 'Demon', ability: 'Kills a player each night and may pass Demonhood on self-kill.' },
  { name: 'No Dashii', team: 'Demon', ability: 'Poisons Townsfolk neighbors and kills nightly.' },
  { name: 'Vortox', team: 'Demon', ability: 'Good info is false, and an execution must occur daily.' },
  { name: 'Gunslinger', team: 'Traveller', ability: 'May publicly execute a player once per game.' },
];

const defaultPlayers = Array.from({ length: 12 }).map((_, index): Player => ({
  id: crypto.randomUUID(),
  seat: index + 1,
  name: `Player ${index + 1}`,
  pronouns: '',
  alive: true,
  alignment: 'Unknown',
  notes: '',
  quickTags: [],
  suspicion: 1,
  reminders: {
    poisoned: false,
    drunk: false,
    safe: false,
    protected: false,
    noAbility: false,
    resurrected: false,
    cursed: false,
  },
  possibilities: [
    { name: '', confidence: 'Medium', note: '' },
    { name: '', confidence: 'Medium', note: '' },
    { name: '', confidence: 'Medium', note: '' },
  ],
}));

const reminderMeta: { key: ReminderKey; label: string; icon: ReactNode }[] = [
  { key: 'poisoned', label: 'Poisoned', icon: <FlaskConical className="h-4 w-4" /> },
  { key: 'drunk', label: 'Drunk', icon: <CircleDashed className="h-4 w-4" /> },
  { key: 'safe', label: 'Safe', icon: <ShieldCheck className="h-4 w-4" /> },
  { key: 'protected', label: 'Protected', icon: <HeartPulse className="h-4 w-4" /> },
  { key: 'noAbility', label: 'No ability', icon: <Skull className="h-4 w-4" /> },
  { key: 'resurrected', label: 'Resurrected', icon: <Sparkles className="h-4 w-4" /> },
  { key: 'cursed', label: 'Cursed', icon: <Search className="h-4 w-4" /> },
];

const STORAGE_KEY = 'clocktower-note-app-v1';

function fuzzyIncludes(query: string, value: string) {
  const q = query.toLowerCase().trim();
  if (!q) return true;
  const source = value.toLowerCase();
  let i = 0;
  for (const char of source) {
    if (char === q[i]) i += 1;
    if (i >= q.length) return true;
  }
  return false;
}

export function App() {
  const [players, setPlayers] = useState<Player[]>(defaultPlayers);
  const [selectedId, setSelectedId] = useState<string>(defaultPlayers[0].id);
  const [globalQuery, setGlobalQuery] = useState('');
  const [characterQuery, setCharacterQuery] = useState<Record<string, string>>({});
  const [characterTeamFilter, setCharacterTeamFilter] = useState<Record<string, Team | 'All'>>({});
  const [recentCharacters, setRecentCharacters] = useState<string[]>([]);
  const [meta, setMeta] = useState<GameMeta>({ title: 'Trouble Brewing', edition: 'Standard' });

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) return;
    const parsed = JSON.parse(saved) as {
      players: Player[];
      selectedId: string;
      meta: GameMeta;
      recentCharacters: string[];
    };
    setPlayers(parsed.players);
    setSelectedId(parsed.selectedId ?? parsed.players[0]?.id ?? '');
    setMeta(parsed.meta ?? { title: 'Trouble Brewing', edition: 'Standard' });
    setRecentCharacters(parsed.recentCharacters ?? []);
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ players, selectedId, meta, recentCharacters }));
  }, [players, selectedId, meta, recentCharacters]);

  const selectedPlayer = players.find((player) => player.id === selectedId) ?? players[0];

  const reminderCount = useMemo(
    () => players.reduce((sum, player) => sum + Object.values(player.reminders).filter(Boolean).length, 0),
    [players],
  );

  const globalResults = useMemo(() => {
    if (!globalQuery.trim()) return [];
    return players.filter((player) => {
      const quickJoined = player.quickTags.join(' ');
      const charJoined = player.possibilities.map((slot) => slot.name).join(' ');
      const haystack = `${player.name} ${player.pronouns} ${player.notes} ${quickJoined} ${charJoined}`;
      return fuzzyIncludes(globalQuery, haystack);
    });
  }, [globalQuery, players]);

  function updatePlayer(id: string, update: (current: Player) => Player) {
    setPlayers((current) => current.map((player) => (player.id === id ? update(player) : player)));
  }

  function seatPosition(index: number, total: number) {
    const angle = (Math.PI * 2 * index) / total - Math.PI / 2;
    const radius = 42;
    const x = 50 + radius * Math.cos(angle);
    const y = 50 + radius * Math.sin(angle);
    return { x, y };
  }

  function pickCharacter(slotIndex: number, value: string) {
    if (!selectedPlayer) return;
    updatePlayer(selectedPlayer.id, (current) => {
      const next = [...current.possibilities] as Player['possibilities'];
      next[slotIndex] = { ...next[slotIndex], name: value };
      return { ...current, possibilities: next };
    });
    if (value) {
      setRecentCharacters((current) => [value, ...current.filter((entry) => entry !== value)].slice(0, 8));
    }
  }

  const isMobileSheetVisible = !!selectedPlayer;

  return (
    <main className="fog-overlay min-h-screen bg-midnight px-3 pb-8 text-slate-100 md:px-6">
      <section className="mx-auto flex w-full max-w-7xl flex-col gap-4 pt-3 md:pt-6">
        <div className="sticky top-0 z-30 rounded-2xl border border-slate-700/70 bg-slate-950/80 p-3 backdrop-blur">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-slate-300" />
            <input
              value={globalQuery}
              onChange={(event) => setGlobalQuery(event.target.value)}
              placeholder="Search players, notes, tags, characters"
              className="w-full rounded-xl border border-slate-700/50 bg-slate-900/70 px-3 py-2 text-sm outline-none ring-amber-300 transition focus:ring-2"
            />
          </div>
          {globalResults.length > 0 && (
            <div className="mt-2 max-h-44 overflow-y-auto rounded-xl border border-slate-700/60 bg-slate-900/95 p-2 scrollbar-thin">
              {globalResults.map((player) => (
                <button
                  key={player.id}
                  onClick={() => {
                    setSelectedId(player.id);
                    setGlobalQuery('');
                  }}
                  className="mb-1 flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm hover:bg-slate-800"
                >
                  <span>{player.name}</span>
                  <span className="text-xs text-slate-400">Seat {player.seat}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <section className="rounded-3xl border border-slate-700/60 bg-dusk/70 p-3 shadow-2xl shadow-black/40 md:p-6">
            <div className="relative mx-auto aspect-square w-full max-w-[820px] rounded-full border border-amber-100/20 bg-gradient-to-br from-slate-950/90 via-slate-900/65 to-indigo-900/60 p-4 shadow-inner shadow-indigo-500/10">
              <div className="absolute inset-[14%] rounded-full border border-amber-100/20 bg-gradient-to-br from-slate-950/80 to-indigo-950/40" />

              <div className="absolute left-1/2 top-1/2 z-10 w-56 -translate-x-1/2 -translate-y-1/2 rounded-3xl border border-amber-100/25 bg-slate-950/80 p-4 text-center shadow-xl shadow-black/50 md:w-64">
                <h1 className="font-title text-xl tracking-wide text-parchment md:text-2xl">Clocktower Notes</h1>
                <input
                  value={meta.title}
                  onChange={(event) => setMeta((current) => ({ ...current, title: event.target.value }))}
                  className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900/70 px-2 py-1 text-center text-xs"
                />
                <select
                  value={meta.edition}
                  onChange={(event) => setMeta((current) => ({ ...current, edition: event.target.value }))}
                  className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900/70 px-2 py-1 text-xs"
                >
                  <option>Standard</option>
                  <option>Sects & Violets</option>
                  <option>Bad Moon Rising</option>
                  <option>Custom Script</option>
                </select>
                <p className="mt-2 text-xs text-slate-300">Reminders active: {reminderCount}</p>
              </div>

              {players.map((player, index) => {
                const point = seatPosition(index, players.length);
                const selected = player.id === selectedPlayer?.id;
                const activeReminders = Object.values(player.reminders).filter(Boolean).length;
                return (
                  <button
                    key={player.id}
                    onClick={() => setSelectedId(player.id)}
                    style={{ left: `${point.x}%`, top: `${point.y}%` }}
                    className={`absolute z-20 w-[108px] -translate-x-1/2 -translate-y-1/2 rounded-2xl border px-2 py-2 text-left text-xs transition sm:w-[120px] ${
                      selected
                        ? 'scale-105 border-amber-200/80 bg-slate-900/95 shadow-glow'
                        : 'border-slate-600/70 bg-slate-900/75 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-100">{player.name}</span>
                      <span className={`h-2.5 w-2.5 rounded-full ${player.alive ? 'bg-emerald-400' : 'bg-rose-500'}`} />
                    </div>
                    <p className="truncate text-[10px] text-slate-300">{player.pronouns || `Seat ${player.seat}`}</p>
                    <p className="mt-1 truncate text-[10px] text-amber-100/90">
                      {player.possibilities.map((slot) => slot.name).filter(Boolean).slice(0, 3).join(' · ') || 'No role reads yet'}
                    </p>
                    <div className="mt-1 text-[10px] text-slate-400">R:{activeReminders} · S:{player.suspicion}/3</div>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="hidden lg:block">{selectedPlayer && <DetailPanel
            player={selectedPlayer}
            updatePlayer={updatePlayer}
            characterQuery={characterQuery}
            setCharacterQuery={setCharacterQuery}
            characterTeamFilter={characterTeamFilter}
            setCharacterTeamFilter={setCharacterTeamFilter}
            pickCharacter={pickCharacter}
            recentCharacters={recentCharacters}
          />}</section>
        </div>
      </section>

      {isMobileSheetVisible && selectedPlayer && (
        <div className="fixed inset-x-0 bottom-0 z-40 rounded-t-3xl border border-slate-700 bg-slate-950/95 p-3 shadow-2xl shadow-black/60 backdrop-blur lg:hidden">
          <DetailPanel
            player={selectedPlayer}
            updatePlayer={updatePlayer}
            characterQuery={characterQuery}
            setCharacterQuery={setCharacterQuery}
            characterTeamFilter={characterTeamFilter}
            setCharacterTeamFilter={setCharacterTeamFilter}
            pickCharacter={pickCharacter}
            recentCharacters={recentCharacters}
          />
        </div>
      )}
    </main>
  );
}

type DetailProps = {
  player: Player;
  updatePlayer: (id: string, update: (current: Player) => Player) => void;
  characterQuery: Record<string, string>;
  setCharacterQuery: Dispatch<SetStateAction<Record<string, string>>>;
  characterTeamFilter: Record<string, Team | 'All'>;
  setCharacterTeamFilter: Dispatch<SetStateAction<Record<string, Team | 'All'>>>;
  pickCharacter: (slotIndex: number, value: string) => void;
  recentCharacters: string[];
};

function DetailPanel({
  player,
  updatePlayer,
  characterQuery,
  setCharacterQuery,
  characterTeamFilter,
  setCharacterTeamFilter,
  pickCharacter,
  recentCharacters,
}: DetailProps) {
  return (
    <div className="max-h-[52vh] overflow-y-auto rounded-2xl border border-slate-700/60 bg-slate-900/90 p-3 scrollbar-thin lg:max-h-[78vh] lg:p-4">
      <div className="flex items-center justify-between gap-2">
        <input
          value={player.name}
          onChange={(event) => updatePlayer(player.id, (current) => ({ ...current, name: event.target.value }))}
          className="w-full rounded-lg border border-slate-700 bg-slate-950/70 px-2 py-2 font-semibold"
        />
        <span className="rounded bg-slate-800 px-2 py-1 text-xs">Seat {player.seat}</span>
      </div>
      <input
        value={player.pronouns}
        onChange={(event) => updatePlayer(player.id, (current) => ({ ...current, pronouns: event.target.value }))}
        placeholder="Pronouns / subtitle"
        className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950/70 px-2 py-2 text-sm"
      />

      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
        <button
          onClick={() => updatePlayer(player.id, (current) => ({ ...current, alive: !current.alive }))}
          className={`rounded-lg px-2 py-2 ${player.alive ? 'bg-emerald-700/40 text-emerald-100' : 'bg-rose-700/40 text-rose-100'}`}
        >
          {player.alive ? 'Alive' : 'Dead'}
        </button>
        {(['Unknown', 'Good', 'Evil'] as Alignment[]).map((alignment) => (
          <button
            key={alignment}
            onClick={() => updatePlayer(player.id, (current) => ({ ...current, alignment }))}
            className={`rounded-lg px-2 py-2 ${player.alignment === alignment ? 'bg-amber-700/50 text-amber-100' : 'bg-slate-800 text-slate-300'}`}
          >
            {alignment}
          </button>
        ))}
      </div>

      <label className="mt-3 block text-xs text-slate-300">Suspicion / confidence</label>
      <input
        type="range"
        min={0}
        max={3}
        value={player.suspicion}
        onChange={(event) => updatePlayer(player.id, (current) => ({ ...current, suspicion: Number(event.target.value) }))}
        className="w-full"
      />

      <label className="mt-3 block text-xs text-slate-300">Quick tags</label>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {quickTagOptions.map((tag) => {
          const active = player.quickTags.includes(tag);
          return (
            <button
              key={tag}
              onClick={() => updatePlayer(player.id, (current) => ({
                ...current,
                quickTags: active ? current.quickTags.filter((entry) => entry !== tag) : [...current.quickTags, tag],
              }))}
              className={`rounded-full border px-2 py-1 text-[11px] ${
                active ? 'border-amber-200/70 bg-amber-800/50 text-amber-100' : 'border-slate-600 bg-slate-800/80 text-slate-300'
              }`}
            >
              {tag}
            </button>
          );
        })}
      </div>

      <label className="mt-3 block text-xs text-slate-300">Reminders</label>
      <div className="mt-1 grid grid-cols-2 gap-2">
        {reminderMeta.map((reminder) => {
          const active = player.reminders[reminder.key];
          return (
            <button
              key={reminder.key}
              onClick={() => updatePlayer(player.id, (current) => ({
                ...current,
                reminders: { ...current.reminders, [reminder.key]: !current.reminders[reminder.key] },
              }))}
              className={`flex items-center gap-2 rounded-lg border px-2 py-2 text-xs ${
                active ? 'border-sky-300/70 bg-sky-700/30 text-sky-100' : 'border-slate-600 bg-slate-800/70 text-slate-200'
              }`}
            >
              {reminder.icon}
              {reminder.label}
            </button>
          );
        })}
      </div>

      <div className="mt-4 space-y-3">
        {player.possibilities.map((slot, index) => {
          const slotKey = `${player.id}-${index}`;
          const query = characterQuery[slotKey] ?? '';
          const teamFilter = characterTeamFilter[slotKey] ?? 'All';
          const filtered = characterPool.filter((char) => {
            if (teamFilter !== 'All' && char.team !== teamFilter) return false;
            return fuzzyIncludes(query, `${char.name} ${char.ability} ${char.team}`);
          });

          return (
            <div key={slotKey} className="rounded-xl border border-slate-700/70 bg-slate-950/60 p-2">
              <div className="mb-2 flex items-center justify-between text-xs text-slate-300">
                <span>Character slot {index + 1}</span>
                <button
                  onClick={() => {
                    pickCharacter(index, '');
                    updatePlayer(player.id, (current) => {
                      const next = [...current.possibilities] as Player['possibilities'];
                      next[index] = { name: '', confidence: 'Medium', note: '' };
                      return { ...current, possibilities: next };
                    });
                  }}
                  className="rounded bg-slate-800 px-2 py-1"
                >
                  Clear
                </button>
              </div>

              <input
                placeholder="Search character"
                value={query}
                onChange={(event) => setCharacterQuery((current) => ({ ...current, [slotKey]: event.target.value }))}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm"
              />
              <select
                value={teamFilter}
                onChange={(event) => setCharacterTeamFilter((current) => ({ ...current, [slotKey]: event.target.value as Team | 'All' }))}
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs"
              >
                <option>All</option>
                <option>Townsfolk</option>
                <option>Outsider</option>
                <option>Minion</option>
                <option>Demon</option>
                <option>Traveller</option>
              </select>
              <div className="mt-2 max-h-28 overflow-y-auto rounded border border-slate-700/60 bg-slate-900/70 p-1 text-xs scrollbar-thin">
                {recentCharacters.length > 0 && !query && (
                  <p className="px-2 py-1 text-[10px] uppercase tracking-wide text-slate-400">Recent</p>
                )}
                {!query && recentCharacters.map((name) => (
                  <button
                    key={`${slotKey}-${name}`}
                    onClick={() => pickCharacter(index, name)}
                    className="block w-full rounded px-2 py-1 text-left hover:bg-slate-800"
                  >
                    {name}
                  </button>
                ))}

                {filtered.map((char) => (
                  <button
                    key={`${slotKey}-${char.name}`}
                    onClick={() => pickCharacter(index, char.name)}
                    className="mb-1 block w-full rounded border border-transparent px-2 py-1 text-left hover:border-slate-500 hover:bg-slate-800"
                  >
                    <div className="flex items-center justify-between">
                      <span>{char.name}</span>
                      <span className="text-[10px] text-amber-100">{char.team}</span>
                    </div>
                    <p className="text-[10px] text-slate-400">{char.ability}</p>
                  </button>
                ))}
              </div>

              <input
                value={slot.name}
                onChange={(event) => pickCharacter(index, event.target.value)}
                placeholder="Selected character"
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm"
              />
              <select
                value={slot.confidence}
                onChange={(event) => updatePlayer(player.id, (current) => {
                  const next = [...current.possibilities] as Player['possibilities'];
                  next[index] = { ...next[index], confidence: event.target.value as Confidence };
                  return { ...current, possibilities: next };
                })}
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs"
              >
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
              </select>
              <input
                value={slot.note}
                onChange={(event) => updatePlayer(player.id, (current) => {
                  const next = [...current.possibilities] as Player['possibilities'];
                  next[index] = { ...next[index], note: event.target.value };
                  return { ...current, possibilities: next };
                })}
                placeholder="Slot notes"
                className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-xs"
              />
            </div>
          );
        })}
      </div>

      <label className="mt-3 block text-xs text-slate-300">Freeform notes</label>
      <textarea
        value={player.notes}
        onChange={(event) => updatePlayer(player.id, (current) => ({ ...current, notes: event.target.value }))}
        rows={5}
        placeholder="Night info, social reads, worldbuilding..."
        className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm"
      />
    </div>
  );
}

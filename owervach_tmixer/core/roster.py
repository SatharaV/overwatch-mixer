"""Roster model — single source of truth for player management with living entities."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import GameMode, Player, Role


class RosterError(ValueError):
    """Raised for invalid roster operations (duplicates, full teams...)."""


@dataclass
class Roster:
    game_mode: GameMode
    team1_slots: list[Player | None] = field(default_factory=list)
    team2_slots: list[Player | None] = field(default_factory=list)
    bench: list[Player] = field(default_factory=list)
    saved: list[Player] = field(default_factory=list)

    def __post_init__(self):
        self._normalize_slots()

    # ------------------------------------------------------------------ #
    # Basic accessors
    # ------------------------------------------------------------------ #
    @property
    def team_size(self) -> int:
        return self.game_mode.players_per_team

    def _normalize_slots(self):
        """Ensure team slots have exactly ``team_size`` entries."""
        size = self.team_size
        overflow = []
        for name in ("team1_slots", "team2_slots"):
            slots = getattr(self, name)
            if len(slots) < size:
                slots.extend([None] * (size - len(slots)))
            elif len(slots) > size:
                overflow.extend(p for p in slots[size:] if p is not None)
                setattr(self, name, slots[:size])
        if overflow:
            self.bench.extend(self._reset_for_bench(p) for p in overflow)

    def active_players(self) -> list[Player]:
        return [p for p in self.team1_slots + self.team2_slots if p is not None]

    def bench_players(self) -> list[Player]:
        return list(self.bench)

    def saved_names(self) -> set[str]:
        return {p.name.casefold() for p in self.saved}

    def player_at(self, team_num: int, slot_idx: int) -> Player | None:
        slots = self.team1_slots if team_num == 1 else self.team2_slots
        if 0 <= slot_idx < len(slots):
            return slots[slot_idx]
        return None

    def slot_of(self, player: Player) -> tuple[int, int] | None:
        for team_num in (1, 2):
            slots = self.team1_slots if team_num == 1 else self.team2_slots
            for i, p in enumerate(slots):
                if p is player or (p and p.name.casefold() == player.name.casefold()):
                    return team_num, i
        return None

    def is_saved(self, player: Player) -> bool:
        return player.name.casefold() in self.saved_names()

    def find_bench(self, name: str) -> Player | None:
        folded = name.strip().casefold()
        return next((p for p in self.bench if p.name.casefold() == folded), None)

    def find_saved(self, name: str) -> Player | None:
        folded = name.strip().casefold()
        return next((p for p in self.saved if p.name.casefold() == folded), None)

    # ------------------------------------------------------------------ #
    # Mutations
    # ------------------------------------------------------------------ #
    def name_taken(self, name: str, exclude: Player | None = None) -> bool:
        folded = name.strip().casefold()
        if not folded:
            return False
        for p in self.active_players() + self.bench:
            if p is exclude:
                continue
            if p.name.casefold() == folded:
                return True
        return False

    def set_slot(self, team_num: int, slot_idx: int, player: Player | None):
        slots = self.team1_slots if team_num == 1 else self.team2_slots
        slots[slot_idx] = player

    def clear_slot(self, team_num: int, slot_idx: int) -> Player | None:
        player = self.player_at(team_num, slot_idx)
        if player is not None:
            self.set_slot(team_num, slot_idx, None)
        return player

    def first_free_slot(self, team_num: int) -> int | None:
        slots = self.team1_slots if team_num == 1 else self.team2_slots
        for i, p in enumerate(slots):
            if p is None:
                return i
        return None

    def any_free_slot(self) -> tuple[int, int] | None:
        for team in (1, 2):
            idx = self.first_free_slot(team)
            if idx is not None:
                return team, idx
        return None

    def create_in_slot(self, team_num: int, slot_idx: int, name: str) -> Player:
        name = name.strip()
        if not name:
            raise RosterError("El nombre no puede estar vacío.")
        if self.name_taken(name):
            raise RosterError(f"El jugador '{name}' ya existe.")
        
        saved_p = self.find_saved(name)
        if saved_p:
            player = Player(
                name=name,
                role=saved_p.role if saved_p.fixed_role else None,
                fixed_team=saved_p.fixed_team,
                fixed_role=saved_p.fixed_role,
                mmr=saved_p.mmr,
                mmr_tank=saved_p.mmr_tank,
                mmr_damage=saved_p.mmr_damage,
                mmr_support=saved_p.mmr_support,
                custom_title=saved_p.custom_title,
                custom_color=saved_p.custom_color,
                auto_mmr_enabled=saved_p.auto_mmr_enabled,
                calculated_mmr=saved_p.calculated_mmr,
                calculated_mmr_tank=saved_p.calculated_mmr_tank,
                calculated_mmr_damage=saved_p.calculated_mmr_damage,
                calculated_mmr_support=saved_p.calculated_mmr_support,
                wins=saved_p.wins,
                losses=saved_p.losses,
                draws=saved_p.draws,
            )
        else:
            player = Player(name=name)
        self.set_slot(team_num, slot_idx, player)
        return player

    def rename_player(self, player: Player, new_name: str):
        new_name = new_name.strip()
        if not new_name:
            raise RosterError("El nombre no puede estar vacío.")
        if new_name.casefold() == player.name.casefold():
            player.name = new_name
            return
        if self.name_taken(new_name, exclude=player):
            raise RosterError(f"El jugador '{new_name}' ya existe.")
        player.name = new_name

    @staticmethod
    def _reset_for_bench(player: Player) -> Player:
        player.role = None
        player.fixed_team = None
        player.fixed_role = False
        return player

    def apply_default_roles(self, order: list[Role]) -> bool:
        changed = False
        for team in (self.team1_slots, self.team2_slots):
            for idx, player in enumerate(team):
                if player is None or (player.fixed_role and player.role is not None):
                    continue
                desired = order[min(idx, len(order) - 1)]
                if player.role != desired:
                    player.role = desired
                    changed = True
        return changed

    def send_to_bench(self, team_num: int, slot_idx: int) -> Player | None:
        player = self.clear_slot(team_num, slot_idx)
        if player is not None:
            self.bench.append(self._reset_for_bench(player))
        return player

    def remove_from_bench(self, name: str) -> Player | None:
        player = self.find_bench(name)
        if player is not None:
            self.bench.remove(player)
        return player

    def add_from_bench_to_team(self, player: Player, team_num: int) -> int:
        slot = self.first_free_slot(team_num)
        if slot is None:
            raise RosterError(f"El Equipo {team_num} está lleno.")
        if player in self.bench:
            self.bench.remove(player)
        self.set_slot(team_num, slot, player)
        return slot

    def add_pending_to_team(
        self,
        name: str,
        role=None,
        fixed_team=None,
        team_num: int = 0,
        slot_idx: int | None = None,
        fixed_role: bool = False,
        custom_color: str | None = None,
    ) -> int:
        folded = name.strip().casefold()
        if not folded:
            raise RosterError("El nombre no puede estar vacío.")

        # Si ya está activo en partida
        for p in self.active_players():
            if p.name.casefold() == folded:
                raise RosterError(f"El jugador '{name}' ya está en la alineación.")

        # Auto-promoción: Si está en espera, se extrae limpiamente sin error
        existing_bench = self.find_bench(name)
        if existing_bench:
            self.bench.remove(existing_bench)

        if team_num not in (1, 2):
            if fixed_team in (1, 2) and self.first_free_slot(fixed_team) is not None:
                team_num = fixed_team
            else:
                free = self.any_free_slot()
                if free is None:
                    raise RosterError("Ambos equipos están llenos. Añádelo a Zona de Espera.")
                team_num, _ = free

        target_slot = slot_idx if (slot_idx is not None and 0 <= slot_idx < self.team_size) else self.first_free_slot(team_num)
        if target_slot is None:
            raise RosterError(f"El Equipo {team_num} está lleno.")

        saved_p = self.find_saved(name)
        if saved_p:
            player = Player(
                name=name,
                role=role or (saved_p.role if saved_p.fixed_role else None),
                fixed_team=fixed_team or saved_p.fixed_team,
                fixed_role=fixed_role or saved_p.fixed_role,
                mmr=saved_p.mmr,
                mmr_tank=saved_p.mmr_tank,
                mmr_damage=saved_p.mmr_damage,
                mmr_support=saved_p.mmr_support,
                custom_title=saved_p.custom_title,
                custom_color=custom_color or saved_p.custom_color,
                auto_mmr_enabled=saved_p.auto_mmr_enabled,
                calculated_mmr=saved_p.calculated_mmr,
                calculated_mmr_tank=saved_p.calculated_mmr_tank,
                calculated_mmr_damage=saved_p.calculated_mmr_damage,
                calculated_mmr_support=saved_p.calculated_mmr_support,
                wins=saved_p.wins,
                losses=saved_p.losses,
                draws=saved_p.draws,
            )
        elif existing_bench:
            player = existing_bench
            player.role = role
            player.fixed_team = fixed_team
            player.fixed_role = fixed_role
            if custom_color:
                player.custom_color = custom_color
        else:
            player = Player(
                name=name,
                role=role,
                fixed_team=fixed_team,
                fixed_role=fixed_role,
                custom_color=custom_color,
            )

        # Si el slot objetivo tenía un ocupante, enviarlo a espera
        occupant = self.player_at(team_num, target_slot)
        if occupant is not None and occupant is not player:
            self.bench.append(self._reset_for_bench(occupant))

        self.set_slot(team_num, target_slot, player)
        return target_slot

    def add_to_bench(self, name: str):
        folded = name.strip().casefold()
        if not folded:
            raise RosterError("El nombre no puede estar vacío.")
        if self.name_taken(name):
            raise RosterError(f"El jugador '{name}' ya está en la partida o en espera.")
        saved_p = self.find_saved(name)
        if saved_p:
            p = Player(
                name=name,
                mmr=saved_p.mmr,
                mmr_tank=saved_p.mmr_tank,
                mmr_damage=saved_p.mmr_damage,
                mmr_support=saved_p.mmr_support,
                custom_title=saved_p.custom_title,
                custom_color=saved_p.custom_color,
                auto_mmr_enabled=saved_p.auto_mmr_enabled,
                calculated_mmr=saved_p.calculated_mmr,
                calculated_mmr_tank=saved_p.calculated_mmr_tank,
                calculated_mmr_damage=saved_p.calculated_mmr_damage,
                calculated_mmr_support=saved_p.calculated_mmr_support,
                wins=saved_p.wins,
                losses=saved_p.losses,
                draws=saved_p.draws,
            )
        else:
            p = Player(name=name)
        self.bench.append(self._reset_for_bench(p))

    def save_player(self, player: Player):
        if self.is_saved(player):
            saved_p = self.find_saved(player.name)
            if saved_p:
                saved_p.custom_color = player.custom_color
                saved_p.custom_title = player.custom_title
                saved_p.mmr = player.mmr
                saved_p.mmr_tank = player.mmr_tank
                saved_p.mmr_damage = player.mmr_damage
                saved_p.mmr_support = player.mmr_support
                saved_p.auto_mmr_enabled = player.auto_mmr_enabled
                saved_p.calculated_mmr = player.calculated_mmr
                saved_p.calculated_mmr_tank = player.calculated_mmr_tank
                saved_p.calculated_mmr_damage = player.calculated_mmr_damage
                saved_p.calculated_mmr_support = player.calculated_mmr_support
                saved_p.wins = player.wins
                saved_p.losses = player.losses
                saved_p.draws = player.draws
                if player.fixed_role:
                    saved_p.role = player.role
                    saved_p.fixed_role = True
            return
        role = player.role if player.fixed_role else None
        self.saved.append(
            Player(
                name=player.name,
                role=role,
                fixed_team=player.fixed_team,
                fixed_role=player.fixed_role,
                mmr=player.mmr,
                mmr_tank=player.mmr_tank,
                mmr_damage=player.mmr_damage,
                mmr_support=player.mmr_support,
                custom_title=player.custom_title,
                custom_color=player.custom_color,
                auto_mmr_enabled=player.auto_mmr_enabled,
                calculated_mmr=player.calculated_mmr,
                calculated_mmr_tank=player.calculated_mmr_tank,
                calculated_mmr_damage=player.calculated_mmr_damage,
                calculated_mmr_support=player.calculated_mmr_support,
                wins=player.wins,
                losses=player.losses,
                draws=player.draws,
            )
        )

    def save_name(self, name: str, role=None, fixed_team=None, fixed_role: bool = False):
        if not name.strip():
            return
        if name.strip().casefold() in self.saved_names():
            return
        self.saved.append(
            Player(name=name.strip(), role=role, fixed_team=fixed_team, fixed_role=fixed_role)
        )

    def remove_saved(self, player: Player):
        folded = player.name.casefold()
        self.saved = [p for p in self.saved if p.name.casefold() != folded]

    def remove_saved_name(self, name: str):
        folded = name.strip().casefold()
        self.saved = [p for p in self.saved if p.name.casefold() != folded]

    def fill_from_bench(self):
        remaining: list[Player] = []
        for p in self.bench:
            team_num = 0
            if p.fixed_team in (1, 2) and self.first_free_slot(p.fixed_team) is not None:
                team_num = p.fixed_team
            else:
                free = self.any_free_slot()
                if free is None:
                    remaining.append(p)
                    continue
                team_num = free[0]
            self.set_slot(team_num, self.first_free_slot(team_num), p)
        self.bench = remaining

    # ------------------------------------------------------------------ #
    # Drag & drop relocation
    # ------------------------------------------------------------------ #
    def relocate(self, payload: dict, target_team: int, target_idx: int | None,
                 cross_team_swap: bool = False) -> str:
        if target_team not in (1, 2):
            raise RosterError("Destino inválido.")

        if payload.get("kind") == "bench":
            player = self.find_bench(payload.get("name", ""))
            if player is None:
                raise RosterError(f"'{payload.get('name')}' ya no está en Zona de Espera.")
            return self._relocate_from_bench(player, target_team, target_idx)

        if payload.get("kind") == "slot":
            src_team = payload.get("team")
            src_idx = payload.get("idx")
            player = self.player_at(src_team, src_idx)
            if player is None:
                raise RosterError(f"'{payload.get('name')}' ya no está en la partida.")
            return self._relocate_from_slot(
                player, src_team, src_idx, target_team, target_idx, cross_team_swap)

        raise RosterError("Origen inválido para el arrastre.")

    def _clamp_target(self, target_team: int, target_idx: int | None) -> int:
        if target_idx is not None:
            slots = self.team1_slots if target_team == 1 else self.team2_slots
            if not 0 <= target_idx < len(slots):
                raise RosterError("Celda destino inválida.")
            return target_idx
        free = self.first_free_slot(target_team)
        if free is None:
            raise RosterError(f"El Equipo {target_team} está lleno: sin celdas libres.")
        return free

    def _relocate_from_slot(self, player: Player, src_team: int, src_idx: int,
                            target_team: int, target_idx: int | None,
                            cross_team_swap: bool) -> str:
        if target_team == src_team and target_idx == src_idx:
            return "Sin cambios"
        if player.fixed_team is not None and player.fixed_team != target_team:
            raise RosterError(
                f"'{player.name}' está fijado a Equipo {player.fixed_team} "
                f"y no puede moverse a Equipo {target_team}.")

        target_idx = self._clamp_target(target_team, target_idx)
        occupant = self.player_at(target_team, target_idx)
        if occupant is None:
            self.set_slot(target_team, target_idx, player)
            self.set_slot(src_team, src_idx, None)
            return f"'{player.name}' movido a Equipo {target_team}."

        if target_team == src_team:
            self.set_slot(src_team, src_idx, occupant)
            self.set_slot(target_team, target_idx, player)
            return f"'{player.name}' y '{occupant.name}' intercambiados dentro de Equipo {target_team}."

        if not cross_team_swap:
            raise RosterError(
                f"El Equipo {target_team} ocupa esa celda y el cruce no está permitido. "
                "Activa 'Intercambiar' en Configuración para permitir swaps entre equipos.")
        if occupant.fixed_team is not None:
            raise RosterError(
                f"'{occupant.name}' está fijado a Equipo {target_team} "
                f"y no puede pasar a Equipo {src_team}.")
        self.set_slot(src_team, src_idx, occupant)
        self.set_slot(target_team, target_idx, player)
        return f"'{player.name}' y '{occupant.name}' intercambiados entre equipos."

    def _relocate_from_bench(self, player: Player, target_team: int,
                             target_idx: int | None) -> str:
        if player.fixed_team is not None and player.fixed_team != target_team:
            raise RosterError(
                f"'{player.name}' está fijado a Equipo {player.fixed_team}; solo puede entrar ahí.")

        target_idx = self._clamp_target(target_team, target_idx)
        occupant = self.player_at(target_team, target_idx)
        if occupant is not None:
            occupant = self._reset_for_bench(occupant)
            self.set_slot(target_team, target_idx, player)
            self.bench.remove(player)
            self.bench.append(occupant)
            return f"'{player.name}' entra a Equipo {target_team}; '{occupant.name}' pasa a Zona de Espera."
        self.set_slot(target_team, target_idx, player)
        self.bench.remove(player)
        return f"'{player.name}' entra a Equipo {target_team}."

    def on_game_mode_change(self, mode: GameMode):
        if mode == self.game_mode:
            return
        self.game_mode = mode
        self._normalize_slots()
        self.fill_from_bench()

    def clear_teams_and_bench(self):
        self.team1_slots = [None] * self.team_size
        self.team2_slots = [None] * self.team_size
        self.bench = []

    # ------------------------------------------------------------------ #
    # Serialization
    # ------------------------------------------------------------------ #
    VERSION = 2

    def to_dict(self) -> dict:
        return {
            "version": self.VERSION,
            "mode": self.game_mode.value,
            "team1": [p.to_dict() if p else None for p in self.team1_slots],
            "team2": [p.to_dict() if p else None for p in self.team2_slots],
            "bench": [p.to_dict() for p in self.bench],
            "saved": [p.to_dict() for p in self.saved],
        }

    @classmethod
    def from_dict(cls, data: dict, mode: GameMode) -> Roster:
        file_mode = GameMode(data.get("mode", mode.value))
        return cls(
            game_mode=file_mode,
            team1_slots=[Player.from_dict(p) if p else None for p in data.get("team1", [])],
            team2_slots=[Player.from_dict(p) if p else None for p in data.get("team2", [])],
            bench=[cls._reset_for_bench(Player.from_dict(p)) for p in data.get("bench", [])],
            saved=[Player.from_dict(p) for p in data.get("saved", [])],
        )

    @classmethod
    def empty(cls, mode: GameMode) -> Roster:
        size = mode.players_per_team
        return cls(game_mode=mode, team1_slots=[None] * size, team2_slots=[None] * size)

    @classmethod
    def from_legacy(cls, players: list[Player], mode: GameMode) -> Roster:
        size = mode.players_per_team
        t1: list[Player | None] = []
        t2: list[Player | None] = []
        bench: list[Player] = []
        seen: set[str] = set()

        def _place(p: Player) -> bool:
            if p.fixed_team == 1:
                if len(t1) < size:
                    t1.append(p)
                    return True
            elif p.fixed_team == 2:
                if len(t2) < size:
                    t2.append(p)
                    return True
            else:
                if len(t1) < size:
                    t1.append(p)
                    return True
                if len(t2) < size:
                    t2.append(p)
                    return True
            bench.append(Roster._reset_for_bench(p))
            return True

        for p in players:
            folded = p.name.casefold()
            if not p.name or folded in seen:
                continue
            seen.add(folded)
            _place(p)

        t1 += [None] * (size - len(t1))
        t2 += [None] * (size - len(t2))

        saved = []
        saved_seen: set[str] = set()
        for p in players:
            if p.name and p.name.casefold() not in saved_seen:
                saved_seen.add(p.name.casefold())
                saved.append(
                    Player(
                        name=p.name,
                        role=p.role,
                        fixed_team=p.fixed_team,
                        fixed_role=p.fixed_role,
                        mmr=p.mmr,
                        mmr_tank=p.mmr_tank,
                        mmr_damage=p.mmr_damage,
                        mmr_support=p.mmr_support,
                        custom_title=p.custom_title,
                        custom_color=p.custom_color,
                    )
                )
        return cls(game_mode=mode, team1_slots=t1, team2_slots=t2, bench=bench, saved=saved)

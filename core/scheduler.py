"""
Scheduler per generazione turni con vincolo HARD sulle ore settimanali.
Ogni dipendente deve fare esattamente le ore previste dal contratto.
"""
import pandas as pd
import random
import math
from datetime import date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from copy import deepcopy

HOURS_PER_SHIFT = 7
DAYS_IT = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
VOLUNTEER = "Volontario esperto"
UNCOVERED = "SCOPERTO"
MAX_RETRY_ATTEMPTS = 50


@dataclass
class PersonState:
    """Stato di una persona durante lo scheduling."""
    name: str
    weekly_budget: int  # Budget ore settimanale (38 o 28)
    can_night: bool
    can_sunday: bool
    # Contatori totali
    total_hours: int = 0
    morning_count: int = 0
    afternoon_count: int = 0
    night_count: int = 0
    sunday_count: int = 0
    # Stato corrente
    consecutive_days: int = 0
    last_work_date: Optional[date] = None
    worked_night_yesterday: bool = False
    # Ore per settimana
    hours_per_week: Dict[int, int] = field(default_factory=dict)

    def hours_this_week(self, week_idx: int) -> int:
        return self.hours_per_week.get(week_idx, 0)

    def remaining_hours_this_week(self, week_idx: int) -> int:
        """Ore ancora da assegnare questa settimana per raggiungere il budget."""
        return self.weekly_budget - self.hours_this_week(week_idx)

    def can_take_shift_this_week(self, week_idx: int) -> bool:
        """Verifica se ha ancora budget per un turno questa settimana."""
        return self.hours_this_week(week_idx) + HOURS_PER_SHIFT <= self.weekly_budget

    def week_budget_satisfied(self, week_idx: int) -> bool:
        """Verifica se ha raggiunto esattamente il budget settimanale."""
        return self.hours_this_week(week_idx) == self.weekly_budget

    def add_shift(self, week_idx: int, shift_type: str, work_date: date, is_sunday: bool):
        """Registra un turno assegnato."""
        self.total_hours += HOURS_PER_SHIFT
        self.hours_per_week[week_idx] = self.hours_per_week.get(week_idx, 0) + HOURS_PER_SHIFT

        if shift_type == 'morning':
            self.morning_count += 1
        elif shift_type == 'afternoon':
            self.afternoon_count += 1
        elif shift_type == 'night':
            self.night_count += 1

        if is_sunday:
            self.sunday_count += 1

        # Aggiorna consecutivi
        if self.last_work_date and (work_date - self.last_work_date).days == 1:
            self.consecutive_days += 1
        else:
            self.consecutive_days = 1

        self.last_work_date = work_date
        self.worked_night_yesterday = (shift_type == 'night')


@dataclass
class Slot:
    """Uno slot turno da coprire."""
    date: date
    week_idx: int
    day_name: str
    shift_type: str  # 'morning', 'afternoon', 'night'
    required: int  # quante persone servono
    assigned: List[str] = field(default_factory=list)

    @property
    def is_sunday(self) -> bool:
        return self.day_name == 'Domenica'

    @property
    def remaining(self) -> int:
        return max(0, self.required - len(self.assigned))

    @property
    def is_filled(self) -> bool:
        return self.remaining == 0


def create_weekly_slots(start_date: date, week_idx: int, vincoli: dict) -> List[Slot]:
    """Crea tutti gli slot per una settimana."""
    slots = []
    notte_attiva = vincoli.get('notte_attiva', False)
    giorni_notte = vincoli.get('giorni_notte', [])
    min_notte = vincoli.get('min_notte', 0)

    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        day_name = DAYS_IT[day_offset]
        is_sunday = day_offset == 6

        if is_sunday:
            # Domenica: configurabile
            if vincoli['min_dom_mattino'] > 0:
                slots.append(Slot(
                    date=current_date,
                    week_idx=week_idx,
                    day_name=day_name,
                    shift_type='morning',
                    required=vincoli['min_dom_mattino']
                ))
            if vincoli['min_dom_pomeriggio'] > 0:
                slots.append(Slot(
                    date=current_date,
                    week_idx=week_idx,
                    day_name=day_name,
                    shift_type='afternoon',
                    required=vincoli['min_dom_pomeriggio']
                ))
        else:
            # Lun-Sab: mattino e pomeriggio
            slots.append(Slot(
                date=current_date,
                week_idx=week_idx,
                day_name=day_name,
                shift_type='morning',
                required=vincoli['min_mattino_lun_sab']
            ))
            slots.append(Slot(
                date=current_date,
                week_idx=week_idx,
                day_name=day_name,
                shift_type='afternoon',
                required=vincoli['min_pomeriggio_lun_sab']
            ))

        # Notte (se attiva per questo giorno)
        if notte_attiva and day_name in giorni_notte and min_notte > 0:
            slots.append(Slot(
                date=current_date,
                week_idx=week_idx,
                day_name=day_name,
                shift_type='night',
                required=min_notte
            ))

    return slots


def is_candidate_eligible(
    person: PersonState,
    slot: Slot,
    vincoli: dict,
    day_assignments: Dict[str, str]
) -> bool:
    """Verifica se una persona può essere assegnata a questo slot (vincoli HARD)."""

    # Già assegnato a un turno oggi
    if person.name in day_assignments:
        return False

    # VINCOLO HARD: non può superare budget ore settimanali
    if not person.can_take_shift_this_week(slot.week_idx):
        return False

    # Max giorni consecutivi raggiunto
    max_cons = vincoli.get('max_consecutivi', 6)
    if person.last_work_date:
        days_since = (slot.date - person.last_work_date).days
        if days_since == 1 and person.consecutive_days >= max_cons:
            return False

    # Riposo dopo notte: se ha fatto notte ieri, non lavora oggi
    if person.worked_night_yesterday:
        if person.last_work_date and (slot.date - person.last_work_date).days == 1:
            return False

    # Domenica: solo chi può lavorare domenica
    if slot.is_sunday and not person.can_sunday:
        return False

    # Notte: solo chi può fare notte
    if slot.shift_type == 'night' and not person.can_night:
        return False

    return True


def calc_candidate_score(
    person: PersonState,
    slot: Slot,
    all_people: List[PersonState],
    vincoli: dict
) -> float:
    """
    Calcola score per un candidato. Score più basso = migliore candidato.
    Priorità: chi ha più ore rimanenti da fare questa settimana.
    """
    score = 0.0

    # 1. PRIORITA' MASSIMA: ore rimanenti questa settimana (chi deve fare più ore ha priorità)
    remaining = person.remaining_hours_this_week(slot.week_idx)
    score -= remaining * 20  # Più ore da fare = score più basso = priorità più alta

    # 2. Bilanciamento tipo turno
    if slot.shift_type == 'morning':
        avg_morning = sum(p.morning_count for p in all_people) / len(all_people) if all_people else 0
        score += (person.morning_count - avg_morning) * 3
    elif slot.shift_type == 'afternoon':
        avg_afternoon = sum(p.afternoon_count for p in all_people) / len(all_people) if all_people else 0
        score += (person.afternoon_count - avg_afternoon) * 3

    # 3. Bilanciamento domeniche
    if slot.is_sunday:
        avg_sunday = sum(p.sunday_count for p in all_people) / len(all_people) if all_people else 0
        score += (person.sunday_count - avg_sunday) * 4

    # 4. Penalità se vicino al limite consecutivi
    max_cons = vincoli.get('max_consecutivi', 6)
    if person.consecutive_days >= max_cons - 1:
        score += 30

    return score


def weighted_random_choice(candidates_scored: List[tuple], randomness: float, top_k: int = 3) -> 'PersonState':
    """Seleziona un candidato usando weighted random tra i top-K."""
    if len(candidates_scored) == 1 or randomness == 0:
        return candidates_scored[0][0]

    k = min(top_k, len(candidates_scored))
    top_candidates = candidates_scored[:k]

    scores = [c[1] for c in top_candidates]
    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        weights = [1.0] * k
    else:
        temperature = 0.1 + randomness * 2.0
        weights = []
        for score in scores:
            normalized = (max_score - score) / (max_score - min_score + 0.001)
            weight = math.exp(normalized / temperature)
            weights.append(weight)

    total = sum(weights)
    weights = [w / total for w in weights]

    r = random.random()
    cumulative = 0
    for i, w in enumerate(weights):
        cumulative += w
        if r <= cumulative:
            return top_candidates[i][0]

    return top_candidates[-1][0]


def update_night_flags(people: List[PersonState], current_date: date):
    """Aggiorna flag worked_night_yesterday per il nuovo giorno."""
    for p in people:
        if p.last_work_date and (current_date - p.last_work_date).days > 1:
            p.worked_night_yesterday = False


def assign_slot(
    slot: Slot,
    people: List[PersonState],
    vincoli: dict,
    day_assignments: Dict[str, str],
    usa_volontario: bool,
    randomness: float = 0.0
) -> List[str]:
    """Assegna persone a uno slot. Usa Volontario esperto se nessuno disponibile."""
    assigned = []
    top_k = max(3, len(people) // 2)

    while slot.remaining > 0:
        candidates = [
            p for p in people
            if is_candidate_eligible(p, slot, vincoli, day_assignments)
            and p.name not in slot.assigned
        ]

        if not candidates:
            # Nessun candidato: usa volontario o segna scoperto
            if usa_volontario:
                slot.assigned.append(VOLUNTEER)
                assigned.append(VOLUNTEER)
            else:
                slot.assigned.append(UNCOVERED)
                assigned.append(UNCOVERED)
            continue

        # Calcola score e ordina
        candidates_scored = [
            (p, calc_candidate_score(p, slot, people, vincoli))
            for p in candidates
        ]
        candidates_scored.sort(key=lambda x: x[1])

        # Selezione
        best = weighted_random_choice(candidates_scored, randomness, top_k)

        # Assegna
        slot.assigned.append(best.name)
        assigned.append(best.name)
        day_assignments[best.name] = slot.shift_type
        best.add_shift(slot.week_idx, slot.shift_type, slot.date, slot.is_sunday)

    return assigned


def check_week_budgets(people: List[PersonState], week_idx: int) -> Tuple[bool, List[str]]:
    """
    Verifica che tutti abbiano raggiunto esattamente il budget settimanale.
    Ritorna (success, lista_problemi).
    """
    problems = []
    all_ok = True

    for p in people:
        actual = p.hours_this_week(week_idx)
        expected = p.weekly_budget
        if actual != expected:
            all_ok = False
            diff = actual - expected
            problems.append(f"{p.name}: {actual}h vs {expected}h budget (diff: {diff:+}h)")

    return all_ok, problems


def schedule_single_attempt(
    staff: pd.DataFrame,
    data_inizio: date,
    num_weeks: int,
    vincoli: dict,
    usa_volontario: bool,
    randomness: float,
    seed: int
) -> Tuple[dict, bool, List[str]]:
    """
    Singolo tentativo di scheduling.
    Ritorna (risultato, success, problemi).
    """
    random.seed(seed)

    # Inizializza stato persone
    people = []
    for _, row in staff.iterrows():
        people.append(PersonState(
            name=row['Nome'],
            weekly_budget=int(row['Ore settimanali']),
            can_night=bool(row['Può fare notte']),
            can_sunday=bool(row['Può lavorare domenica'])
        ))

    all_slots = []
    all_problems = []
    week_success = True

    # Schedula settimana per settimana
    for week_idx in range(num_weeks):
        week_start = data_inizio + timedelta(weeks=week_idx)
        week_slots = create_weekly_slots(week_start, week_idx, vincoli)

        # Raggruppa per giorno
        days_in_week = sorted(set(s.date for s in week_slots))

        # Shuffle giorni se randomness > 0
        if randomness > 0.3 and len(days_in_week) > 1:
            non_sunday = [d for d in days_in_week if d.weekday() != 6]
            sunday = [d for d in days_in_week if d.weekday() == 6]
            if randomness > 0.5:
                random.shuffle(non_sunday)
            days_in_week = non_sunday + sunday

        for current_date in days_in_week:
            update_night_flags(people, current_date)

            day_slots = [s for s in week_slots if s.date == current_date]
            day_assignments: Dict[str, str] = {}

            # Ordine: notte prima, poi mattino, poi pomeriggio
            day_slots.sort(key=lambda s: {'night': 0, 'morning': 1, 'afternoon': 2}[s.shift_type])

            for slot in day_slots:
                assign_slot(slot, people, vincoli, day_assignments, usa_volontario, randomness)

        all_slots.extend(week_slots)

        # Verifica budget settimanale
        ok, problems = check_week_budgets(people, week_idx)
        if not ok:
            week_success = False
            all_problems.extend([f"Sett {week_idx+1}: {p}" for p in problems])

    # Costruisci output
    result = build_output(all_slots, people, data_inizio, num_weeks, vincoli)
    return result, week_success, all_problems


def build_output(
    all_slots: List[Slot],
    people: List[PersonState],
    data_inizio: date,
    num_weeks: int,
    vincoli: dict
) -> dict:
    """Costruisce il dizionario di output con calendario, summary e meta."""
    notte_attiva = vincoli.get('notte_attiva', False)

    # Calendario DataFrame
    calendario_rows = []
    slots_by_date = {}
    for s in all_slots:
        if s.date not in slots_by_date:
            slots_by_date[s.date] = {}
        slots_by_date[s.date][s.shift_type] = s.assigned

    for d in sorted(slots_by_date.keys()):
        day_data = slots_by_date[d]
        week_idx = (d - data_inizio).days // 7

        row = {
            'Data': d,
            'Giorno': DAYS_IT[d.weekday()],
            'Settimana': week_idx + 1,
            'Mattino': ', '.join(day_data.get('morning', [])) or '-',
            'Pomeriggio': ', '.join(day_data.get('afternoon', [])) or '-',
        }
        if notte_attiva:
            row['Notte'] = ', '.join(day_data.get('night', [])) or '-'

        calendario_rows.append(row)

    calendario_df = pd.DataFrame(calendario_rows)

    # Summary per persona con breakdown settimanale
    summary_rows = []
    for p in people:
        row = {
            'Nome': p.name,
            'Ore totali': p.total_hours,
            'Budget (5 sett)': p.weekly_budget * num_weeks,
            'Scostamento': p.total_hours - (p.weekly_budget * num_weeks),
        }
        # Breakdown per settimana
        for w in range(num_weeks):
            row[f'Sett {w+1}'] = p.hours_this_week(w)
        row['Mattini'] = p.morning_count
        row['Pomeriggi'] = p.afternoon_count
        row['Domeniche'] = p.sunday_count
        if notte_attiva:
            row['Notti'] = p.night_count
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)

    # Metriche
    total_slots = sum(s.required for s in all_slots)
    volunteer_slots = sum(1 for s in all_slots for a in s.assigned if a == VOLUNTEER)
    uncovered_slots = sum(1 for s in all_slots for a in s.assigned if a == UNCOVERED)
    covered_internal = total_slots - volunteer_slots - uncovered_slots

    # Scostamento ore (deve essere 0 con vincolo HARD)
    deviations = [abs(p.total_hours - p.weekly_budget * num_weeks) for p in people]
    max_deviation = max(deviations) if deviations else 0

    meta = {
        'turni_totali': total_slots,
        'turni_coperti_interni': covered_internal,
        'turni_volontario': volunteer_slots,
        'turni_scoperti': uncovered_slots,
        'copertura_interna_pct': round(covered_internal / total_slots * 100, 1) if total_slots > 0 else 0,
        'scostamento_ore': max_deviation,
        'budget_rispettato': max_deviation == 0
    }

    return {
        'calendario': calendario_df,
        'summary': summary_df,
        'meta': meta
    }


def genera_turnazione(
    staff: pd.DataFrame,
    data_inizio: date,
    num_weeks: int,
    vincoli: dict,
    usa_volontario: bool = True,
    randomness: float = 0.0,
    seed: Optional[int] = None
) -> dict:
    """
    Genera la turnazione rispettando il vincolo HARD sulle ore settimanali.
    Riprova con seed diversi se necessario.
    """
    if seed is None:
        seed = random.randint(0, 99999)

    best_result = None
    best_volunteer_count = float('inf')

    for attempt in range(MAX_RETRY_ATTEMPTS):
        current_seed = seed + attempt
        result, success, problems = schedule_single_attempt(
            staff, data_inizio, num_weeks, vincoli, usa_volontario, randomness, current_seed
        )

        volunteer_count = result['meta']['turni_volontario']

        # Se budget rispettato per tutti, verifica se è il miglior risultato
        if result['meta']['budget_rispettato']:
            if volunteer_count < best_volunteer_count:
                best_volunteer_count = volunteer_count
                best_result = result
                best_result['meta']['seed_used'] = current_seed
                best_result['meta']['attempts'] = attempt + 1

            # Se abbiamo 0 volontari, abbiamo la soluzione ottima
            if volunteer_count == 0:
                break

        # Se dopo tutti i tentativi non abbiamo una soluzione valida, prendi l'ultima
        if attempt == MAX_RETRY_ATTEMPTS - 1 and best_result is None:
            best_result = result
            best_result['meta']['seed_used'] = current_seed
            best_result['meta']['attempts'] = MAX_RETRY_ATTEMPTS
            best_result['meta']['constraint_failure'] = True
            best_result['meta']['problems'] = problems

    return best_result

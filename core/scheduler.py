"""
Scheduler per generazione turni con rotazione settimanale bilanciata.
"""
import pandas as pd
from datetime import date, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field

HOURS_PER_SHIFT = 7
DAYS_IT = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
VOLUNTEER = "Volontario esperto"
UNCOVERED = "SCOPERTO"


@dataclass
class PersonState:
    """Stato di una persona durante lo scheduling."""
    name: str
    weekly_hours: int
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

    def can_work_more_this_week(self, week_idx: int) -> bool:
        return self.hours_this_week(week_idx) + HOURS_PER_SHIFT <= self.weekly_hours

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

    def reset_night_flag(self):
        """Reset flag notte per nuovo giorno."""
        pass  # Il flag viene gestito in add_shift


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


def create_weekly_slots(
    start_date: date,
    week_idx: int,
    vincoli: dict
) -> List[Slot]:
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
            # Domenica: solo mattino (se richiesto)
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


def calc_candidate_score(
    person: PersonState,
    slot: Slot,
    all_people: List[PersonState],
    vincoli: dict
) -> float:
    """
    Calcola score per un candidato. Score più basso = migliore candidato.
    """
    score = 0.0

    # 1. Meno ore totali assegnate (peso alto)
    avg_hours = sum(p.total_hours for p in all_people) / len(all_people) if all_people else 0
    score += (person.total_hours - avg_hours) * 10

    # 2. Meno ore questa settimana (peso medio-alto)
    avg_week_hours = sum(p.hours_this_week(slot.week_idx) for p in all_people) / len(all_people) if all_people else 0
    score += (person.hours_this_week(slot.week_idx) - avg_week_hours) * 8

    # 3. Bilanciamento tipo turno
    if slot.shift_type == 'morning':
        avg_morning = sum(p.morning_count for p in all_people) / len(all_people) if all_people else 0
        score += (person.morning_count - avg_morning) * 5
    elif slot.shift_type == 'afternoon':
        avg_afternoon = sum(p.afternoon_count for p in all_people) / len(all_people) if all_people else 0
        score += (person.afternoon_count - avg_afternoon) * 5
    elif slot.shift_type == 'night':
        avg_night = sum(p.night_count for p in all_people) / len(all_people) if all_people else 0
        score += (person.night_count - avg_night) * 5

    # 4. Bilanciamento domeniche
    if slot.is_sunday:
        avg_sunday = sum(p.sunday_count for p in all_people) / len(all_people) if all_people else 0
        score += (person.sunday_count - avg_sunday) * 6

    # 5. Penalità se vicino al limite consecutivi
    max_cons = vincoli.get('max_consecutivi', 6)
    if person.consecutive_days >= max_cons - 1:
        score += 50  # Forte penalità

    # 6. Penalità se ha lavorato ieri (per alternanza)
    if person.last_work_date and (slot.date - person.last_work_date).days == 1:
        score += 3  # Leggera penalità per favorire alternanza

    return score


def is_candidate_eligible(
    person: PersonState,
    slot: Slot,
    vincoli: dict,
    day_assignments: Dict[str, str]  # nome -> turno già assegnato oggi
) -> bool:
    """Verifica se una persona può essere assegnata a questo slot."""

    # Già assegnato a un turno oggi
    if person.name in day_assignments:
        return False

    # Non può superare ore settimanali
    if not person.can_work_more_this_week(slot.week_idx):
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


def assign_slot(
    slot: Slot,
    people: List[PersonState],
    vincoli: dict,
    day_assignments: Dict[str, str],
    usa_volontario: bool
) -> List[str]:
    """
    Assegna persone a uno slot. Ritorna lista nomi assegnati.
    """
    assigned = []

    while slot.remaining > 0:
        # Trova candidati eleggibili
        candidates = [
            p for p in people
            if is_candidate_eligible(p, slot, vincoli, day_assignments)
            and p.name not in slot.assigned
        ]

        if not candidates:
            # Nessun candidato disponibile
            if usa_volontario:
                slot.assigned.append(VOLUNTEER)
                assigned.append(VOLUNTEER)
            else:
                slot.assigned.append(UNCOVERED)
                assigned.append(UNCOVERED)
            continue

        # Calcola score e scegli il migliore
        candidates_scored = [
            (p, calc_candidate_score(p, slot, people, vincoli))
            for p in candidates
        ]
        candidates_scored.sort(key=lambda x: x[1])
        best = candidates_scored[0][0]

        # Assegna
        slot.assigned.append(best.name)
        assigned.append(best.name)
        day_assignments[best.name] = slot.shift_type
        best.add_shift(slot.week_idx, slot.shift_type, slot.date, slot.is_sunday)

    return assigned


def update_night_flags(people: List[PersonState], current_date: date):
    """Aggiorna flag worked_night_yesterday per il nuovo giorno."""
    for p in people:
        if p.last_work_date and (current_date - p.last_work_date).days > 1:
            p.worked_night_yesterday = False


def genera_turnazione(
    staff: pd.DataFrame,
    data_inizio: date,
    num_weeks: int,
    vincoli: dict,
    usa_volontario: bool = True
) -> dict:
    """
    Genera la turnazione per il periodo richiesto.
    """
    # Inizializza stato persone
    people = []
    for _, row in staff.iterrows():
        people.append(PersonState(
            name=row['Nome'],
            weekly_hours=int(row['Ore settimanali']),
            can_night=bool(row['Può fare notte']),
            can_sunday=bool(row['Può lavorare domenica'])
        ))

    # Genera slot per tutte le settimane
    all_slots = []
    for week_idx in range(num_weeks):
        week_start = data_inizio + timedelta(weeks=week_idx)
        slots = create_weekly_slots(week_start, week_idx, vincoli)
        all_slots.extend(slots)

    # Assegna turni settimana per settimana
    for week_idx in range(num_weeks):
        week_slots = [s for s in all_slots if s.week_idx == week_idx]

        # Raggruppa per giorno
        days_in_week = sorted(set(s.date for s in week_slots))

        for current_date in days_in_week:
            # Aggiorna flag notte
            update_night_flags(people, current_date)

            # Slot di questo giorno
            day_slots = [s for s in week_slots if s.date == current_date]
            day_assignments: Dict[str, str] = {}

            # Ordine: notte prima (così il riposo funziona), poi mattino, poi pomeriggio
            day_slots.sort(key=lambda s: {'night': 0, 'morning': 1, 'afternoon': 2}[s.shift_type])

            for slot in day_slots:
                assign_slot(slot, people, vincoli, day_assignments, usa_volontario)

    # Costruisci output DataFrame calendario
    calendario_rows = []
    notte_attiva = vincoli.get('notte_attiva', False)

    # Raggruppa slot per data
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

    # Costruisci summary per persona
    summary_rows = []
    for p in people:
        row = {
            'Nome': p.name,
            'Ore totali': p.total_hours,
            'Target (5 sett)': p.weekly_hours * num_weeks,
            'Scostamento': p.total_hours - (p.weekly_hours * num_weeks),
        }
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

    # Scostamento ore
    hours_list = [p.total_hours for p in people]
    scostamento = max(hours_list) - min(hours_list) if hours_list else 0

    meta = {
        'turni_totali': total_slots,
        'turni_coperti_interni': covered_internal,
        'turni_volontario': volunteer_slots,
        'turni_scoperti': uncovered_slots,
        'copertura_interna_pct': round(covered_internal / total_slots * 100, 1) if total_slots > 0 else 0,
        'scostamento_ore': scostamento
    }

    return {
        'calendario': calendario_df,
        'summary': summary_df,
        'meta': meta
    }

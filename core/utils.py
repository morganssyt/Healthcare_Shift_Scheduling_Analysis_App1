"""
Utility functions per validazione e gestione dati staff.
"""
import pandas as pd
from typing import Tuple, List


def get_default_staff() -> pd.DataFrame:
    """Restituisce lo staff di default con le colonne richieste."""
    return pd.DataFrame({
        'Nome': [
            'Francesco La Rosa',
            'Enzo La Gamba',
            'Thomas Ardissone',
            'Giacomo Rosso',
            'Daniele Ramella'
        ],
        'Ore settimanali': [38, 38, 28, 38, 38],
        'Può fare notte': [True, True, False, True, True],
        'Può lavorare domenica': [True, True, True, True, True]
    })


def validate_staff(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Valida i dati dello staff.
    Ritorna (is_valid, lista_errori).
    """
    errors = []

    # Check nomi vuoti
    empty_names = df[df['Nome'].str.strip() == '']
    if len(empty_names) > 0:
        errors.append("Alcuni dipendenti hanno il nome vuoto.")

    # Check nomi duplicati
    names = df['Nome'].str.strip().str.lower()
    duplicates = names[names.duplicated()].unique()
    if len(duplicates) > 0:
        errors.append(f"Nomi duplicati: {', '.join(duplicates)}")

    # Check ore > 0
    invalid_hours = df[df['Ore settimanali'] <= 0]
    if len(invalid_hours) > 0:
        errors.append("Le ore settimanali devono essere maggiori di 0.")

    return len(errors) == 0, errors


def validate_coverage(
    df: pd.DataFrame,
    notte_attiva: bool,
    giorni_notte: List[str],
    min_notte: int,
    min_domenica_mattino: int
) -> List[str]:
    """
    Verifica che ci sia personale sufficiente per coprire i turni richiesti.
    Ritorna lista di avvisi (non errori bloccanti).
    """
    warnings = []

    # Se notte attiva e min_notte > 0, serve almeno 1 persona che può fare notte
    if notte_attiva and min_notte > 0 and len(giorni_notte) > 0:
        can_night = df[df['Può fare notte'] == True]
        if len(can_night) == 0:
            warnings.append(
                "Attenzione: nessun dipendente può fare il turno di notte, "
                "ma hai richiesto copertura notturna."
            )
        elif len(can_night) < min_notte:
            warnings.append(
                f"Attenzione: hai {len(can_night)} dipendenti che possono fare notte, "
                f"ma ne servono minimo {min_notte} per turno."
            )

    # Se domenica mattina richiede min 1, serve almeno 1 persona disponibile
    if min_domenica_mattino > 0:
        can_sunday = df[df['Può lavorare domenica'] == True]
        if len(can_sunday) == 0:
            warnings.append(
                "Attenzione: nessun dipendente può lavorare la domenica, "
                "ma hai richiesto copertura domenica mattina."
            )
        elif len(can_sunday) < min_domenica_mattino:
            warnings.append(
                f"Attenzione: hai {len(can_sunday)} dipendenti disponibili la domenica, "
                f"ma ne servono minimo {min_domenica_mattino}."
            )

    return warnings


def add_employee(
    df: pd.DataFrame,
    nome: str,
    ore: int,
    puo_notte: bool,
    puo_domenica: bool
) -> Tuple[pd.DataFrame, str | None]:
    """
    Aggiunge un dipendente al dataframe.
    Ritorna (nuovo_df, errore) dove errore è None se ok.
    """
    nome = nome.strip()

    if not nome:
        return df, "Il nome non può essere vuoto."

    # Check duplicato
    if nome.lower() in df['Nome'].str.lower().values:
        return df, f"Esiste già un dipendente con nome '{nome}'."

    if ore <= 0:
        return df, "Le ore devono essere maggiori di 0."

    new_row = pd.DataFrame({
        'Nome': [nome],
        'Ore settimanali': [ore],
        'Può fare notte': [puo_notte],
        'Può lavorare domenica': [puo_domenica]
    })

    return pd.concat([df, new_row], ignore_index=True), None


def calc_total_hours_required(
    num_weeks: int,
    min_mattino_lun_sab: int,
    min_pomeriggio_lun_sab: int,
    min_domenica_mattino: int,
    min_domenica_pomeriggio: int,
    notte_attiva: bool,
    giorni_notte: List[str],
    min_notte: int
) -> dict:
    """
    Calcola le ore totali richieste per il periodo.
    Turno = 7 ore.
    """
    HOURS_PER_SHIFT = 7
    days_lun_sab = 6 * num_weeks
    days_dom = num_weeks

    # Turni lun-sab
    shifts_mattino = days_lun_sab * min_mattino_lun_sab
    shifts_pomeriggio = days_lun_sab * min_pomeriggio_lun_sab

    # Turni domenica
    shifts_dom_mattino = days_dom * min_domenica_mattino
    shifts_dom_pomeriggio = days_dom * min_domenica_pomeriggio

    # Turni notte
    shifts_notte = 0
    if notte_attiva and min_notte > 0:
        nights_per_week = len(giorni_notte)
        shifts_notte = nights_per_week * num_weeks * min_notte

    total_shifts = (
        shifts_mattino + shifts_pomeriggio +
        shifts_dom_mattino + shifts_dom_pomeriggio +
        shifts_notte
    )

    return {
        'turni_mattino_lun_sab': shifts_mattino,
        'turni_pomeriggio_lun_sab': shifts_pomeriggio,
        'turni_dom_mattino': shifts_dom_mattino,
        'turni_dom_pomeriggio': shifts_dom_pomeriggio,
        'turni_notte': shifts_notte,
        'turni_totali': total_shifts,
        'ore_totali_richieste': total_shifts * HOURS_PER_SHIFT
    }

"""
App Streamlit per generazione turnazione 5 settimane.
Croce Rossa - Pianificazione Turni
Vincolo HARD: ogni dipendente deve fare esattamente le ore settimanali previste.
"""
import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
from datetime import date, timedelta
from io import BytesIO
from core.utils import (
    get_default_staff,
    validate_staff,
    validate_coverage,
    calc_total_hours_required
)
from core.scheduler import genera_turnazione
from core.exporters import export_csv, export_excel, export_pdf

# --- Configurazione pagina ---
st.set_page_config(
    page_title="Pianificazione Turni",
    page_icon="🏥",
    layout="wide"
)

st.title("Pianificazione Turni - 5 Settimane")
st.markdown("Genera la turnazione del personale con vincoli e copertura garantita.")


# --- Funzione helper per visualizzazione ---
def mostra_turnazione(risultato: dict, vincoli: dict,
                      data_inizio: date, usa_volontario: bool, notte_attiva: bool):
    """Mostra la turnazione completa con calendario, summary e download."""

    meta = risultato['meta']

    # Verifica se ci sono problemi con i vincoli
    if meta.get('constraint_failure'):
        st.error("Impossibile soddisfare i vincoli senza volontari aggiuntivi.")
        if 'problems' in meta:
            with st.expander("Dettaglio problemi"):
                for p in meta['problems']:
                    st.write(f"- {p}")

    # Metriche
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Turni totali", meta['turni_totali'])
    with col2:
        st.metric("Copertura interna", f"{meta['copertura_interna_pct']}%")
    with col3:
        vol = meta['turni_volontario']
        st.metric("Volontario esperto", vol,
                  delta=f"{vol} turni" if vol > 0 else None,
                  delta_color="inverse" if vol > 0 else "off")
    with col4:
        budget_ok = meta.get('budget_rispettato', False)
        st.metric("Budget rispettato",
                  "Si" if budget_ok else "No",
                  delta="OK" if budget_ok else "Attenzione",
                  delta_color="off" if budget_ok else "inverse")

    # Avvisi
    if meta['turni_volontario'] > 0:
        st.warning(f"Volontario richiesto per {meta['turni_volontario']} turni per rispettare i budget ore.")
    if meta['turni_scoperti'] > 0:
        st.error(f"{meta['turni_scoperti']} turni SCOPERTI!")

    # Info tentativi
    if 'attempts' in meta:
        st.caption(f"Soluzione trovata in {meta['attempts']} tentativi (seed: {meta.get('seed_used', 'N/A')})")

    # Calendario
    with st.expander("Calendario turni", expanded=True):
        calendario_df = risultato['calendario']

        for week_num in range(1, 6):
            week_data = calendario_df[calendario_df['Settimana'] == week_num].copy()
            if week_data.empty:
                continue

            first_date = week_data['Data'].iloc[0]
            last_date = week_data['Data'].iloc[-1]
            st.markdown(f"**Settimana {week_num}** ({first_date.strftime('%d/%m')} - {last_date.strftime('%d/%m/%Y')})")

            display_df = week_data.copy()
            display_df['Data'] = display_df['Data'].apply(lambda d: d.strftime('%d/%m'))
            display_df = display_df.drop(columns=['Settimana'])

            def highlight_issues(val):
                if 'Volontario esperto' in str(val):
                    return 'background-color: #fff3cd'
                elif 'SCOPERTO' in str(val):
                    return 'background-color: #f8d7da'
                return ''

            st.dataframe(display_df.style.applymap(highlight_issues),
                         use_container_width=True, hide_index=True)

    # Riepilogo ore con breakdown settimanale
    with st.expander("Riepilogo ore per persona", expanded=True):
        summary_df = risultato['summary']

        # Evidenzia scostamenti (dovrebbero essere tutti 0)
        def highlight_deviation(val):
            if isinstance(val, (int, float)):
                if val != 0:
                    return 'color: #dc3545; font-weight: bold'
            return ''

        st.dataframe(summary_df.style.applymap(highlight_deviation, subset=['Scostamento']),
                     use_container_width=True, hide_index=True)

        # Verifica che tutti gli scostamenti siano 0
        all_zero = (summary_df['Scostamento'] == 0).all()
        if all_zero:
            st.success("Tutti i dipendenti rispettano esattamente il budget ore settimanale.")
        else:
            st.warning("Alcuni dipendenti non hanno raggiunto il budget ore (turni coperti da Volontario).")

        # Grafico ore per persona
        fig, ax = plt.subplots(figsize=(10, 5))
        names = summary_df['Nome'].tolist()
        hours = summary_df['Ore totali'].tolist()
        budgets = summary_df['Budget (5 sett)'].tolist()

        x = range(len(names))
        width = 0.35

        bars1 = ax.bar([i - width/2 for i in x], hours, width, label='Ore assegnate', color='#2E86AB')
        bars2 = ax.bar([i + width/2 for i in x], budgets, width, label='Budget', color='#A23B72', alpha=0.7)

        ax.set_ylabel('Ore')
        ax.set_title('Ore assegnate vs Budget (5 settimane)')
        ax.set_xticks(list(x))
        ax.set_xticklabels([n.split()[0] for n in names], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        # Aggiungi valori sopra le barre
        for bar, val in zip(bars1, hours):
            ax.annotate(f'{val}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Tabella breakdown settimanale
        st.markdown("**Breakdown ore per settimana:**")
        week_cols = [c for c in summary_df.columns if c.startswith('Sett ')]
        if week_cols:
            breakdown_df = summary_df[['Nome'] + week_cols].copy()

            # Aggiungi colonna budget settimanale per riferimento
            budgets_weekly = []
            for _, row in summary_df.iterrows():
                budget_5w = row['Budget (5 sett)']
                weekly_budget = budget_5w // 5
                budgets_weekly.append(weekly_budget)
            breakdown_df['Budget/sett'] = budgets_weekly

            st.dataframe(breakdown_df, use_container_width=True, hide_index=True)

    # Download
    st.subheader("Esporta")
    date_str = data_inizio.strftime('%Y%m%d')
    file_base = f"turnazione_{date_str}"

    col_csv, col_excel, col_pdf = st.columns(3)
    with col_csv:
        st.download_button(
            "CSV",
            export_csv(risultato['calendario'], notte_attiva),
            f"{file_base}.csv", "text/csv",
            use_container_width=True
        )
    with col_excel:
        st.download_button(
            "Excel",
            export_excel(risultato, notte_attiva),
            f"{file_base}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_pdf:
        st.download_button(
            "PDF",
            export_pdf(risultato, data_inizio, vincoli, usa_volontario, notte_attiva),
            f"{file_base}.pdf", "application/pdf",
            use_container_width=True
        )


# --- Inizializza session state ---
if 'staff' not in st.session_state:
    st.session_state.staff = get_default_staff()

# --- Sidebar: Impostazioni generali ---
st.sidebar.header("Impostazioni")

data_inizio = st.sidebar.date_input(
    "Data inizio (primo lunedì)",
    value=date(2025, 2, 3),
    help="Seleziona il lunedì di inizio della settimana 1"
)

if data_inizio.weekday() != 0:
    days_to_monday = data_inizio.weekday()
    data_inizio = data_inizio - timedelta(days=days_to_monday)
    st.sidebar.info(f"Corretto al lunedì: {data_inizio.strftime('%d/%m/%Y')}")

st.sidebar.divider()

usa_volontario = st.sidebar.toggle(
    "Usa Volontario esperto nei buchi",
    value=True,
    help="Se attivo, i turni non coperti vengono assegnati a 'Volontario esperto'"
)

notte_attiva = st.sidebar.toggle("Notte attiva", value=False)

giorni_notte = []
min_notte = 0
if notte_attiva:
    giorni_notte = st.sidebar.multiselect(
        "Giorni con turno notte",
        options=['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica'],
        default=['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì']
    )
    min_notte = st.sidebar.number_input("Min persone notte", min_value=1, max_value=5, value=1)

st.sidebar.divider()
st.sidebar.subheader("Variazione turni")

randomness = st.sidebar.slider(
    "Randomness",
    min_value=0.0, max_value=1.0, value=0.3, step=0.1,
    help="0 = deterministico, 1 = massima variazione nei turni"
)

use_fixed_seed = st.sidebar.toggle("Usa seed fisso", value=False, help="Per risultati riproducibili")

if use_fixed_seed:
    seed_value = st.sidebar.number_input("Seed", min_value=0, max_value=99999, value=42)
else:
    # Genera seed casuale e salvalo in session_state
    if 'current_seed' not in st.session_state:
        st.session_state.current_seed = random.randint(0, 99999)
    seed_value = st.session_state.current_seed

# --- Sezione principale ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Staff")
    st.caption("Modifica la tabella per aggiungere, rimuovere o modificare dipendenti. Budget: 38h FT, 28h PT.")
    edited_staff = st.data_editor(
        st.session_state.staff,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            'Nome': st.column_config.TextColumn('Nome', required=True),
            'Ore settimanali': st.column_config.NumberColumn('Budget ore/sett', min_value=1, max_value=48, step=1),
            'Può fare notte': st.column_config.CheckboxColumn('Notte', default=False),
            'Può lavorare domenica': st.column_config.CheckboxColumn('Domenica', default=True)
        },
        hide_index=True,
        key="staff_editor"
    )
    st.session_state.staff = edited_staff
    total_hours = edited_staff['Ore settimanali'].sum()
    st.caption(f"**{len(edited_staff)} dipendenti** - **{total_hours}h/settimana budget totale**")

with col_right:
    st.subheader("Vincoli copertura")
    st.markdown("**Lun-Sab**")
    c1, c2 = st.columns(2)
    min_mattino = c1.number_input("Min mattino", 1, 5, 2, key="min_matt")
    min_pomeriggio = c2.number_input("Min pomeriggio", 1, 5, 2, key="min_pom")

    st.markdown("**Domenica**")
    c3, c4 = st.columns(2)
    min_dom_mattino = c3.number_input("Min mattino", 0, 3, 1, key="min_dom_m")
    min_dom_pomeriggio = c4.number_input("Min pomeriggio", 0, 3, 0, key="min_dom_p")

    st.markdown("**Altri**")
    max_consecutivi = st.number_input("Max giorni consecutivi", 3, 7, 6)

# --- Validazioni ---
st.divider()
is_valid, errors = validate_staff(st.session_state.staff)
warnings = validate_coverage(st.session_state.staff, notte_attiva, giorni_notte, min_notte, min_dom_mattino)

for err in errors:
    st.error(err)
for warn in warnings:
    st.warning(warn)

# --- Riepilogo fabbisogno ---
with st.expander("Riepilogo fabbisogno ore", expanded=True):
    fabbisogno = calc_total_hours_required(
        5, min_mattino, min_pomeriggio, min_dom_mattino, min_dom_pomeriggio,
        notte_attiva, giorni_notte, min_notte
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Turni totali", fabbisogno['turni_totali'])
    c2.metric("Ore richieste", f"{fabbisogno['ore_totali_richieste']}h")
    ore_disp = total_hours * 5
    c3.metric("Budget disponibile", f"{ore_disp}h")
    delta = ore_disp - fabbisogno['ore_totali_richieste']
    c4.metric("Bilancio", f"{delta:+}h", delta_color="normal" if delta >= 0 else "inverse")

    if delta < 0:
        st.warning(f"Budget insufficiente: servono {abs(delta)}h in più. Alcuni turni richiederanno Volontario esperto.")

# --- Genera turnazione ---
st.divider()

col_gen, col_regen = st.columns([3, 1])
with col_gen:
    genera_btn = st.button("Genera turnazione", type="primary", disabled=not is_valid, use_container_width=True)
with col_regen:
    rigenera_btn = st.button("Rigenera", disabled=not is_valid, use_container_width=True,
                              help="Genera una variante diversa con nuovo seed")

# Se rigenera, cambia il seed
if rigenera_btn and not use_fixed_seed:
    st.session_state.current_seed = random.randint(0, 99999)
    seed_value = st.session_state.current_seed

if (genera_btn or rigenera_btn) and is_valid:
    vincoli = {
        'min_mattino_lun_sab': min_mattino,
        'min_pomeriggio_lun_sab': min_pomeriggio,
        'min_dom_mattino': min_dom_mattino,
        'min_dom_pomeriggio': min_dom_pomeriggio,
        'max_consecutivi': max_consecutivi,
        'notte_attiva': notte_attiva,
        'giorni_notte': giorni_notte,
        'min_notte': min_notte
    }

    with st.spinner("Generazione in corso (ricerca soluzione ottimale)..."):
        risultato = genera_turnazione(
            st.session_state.staff, data_inizio, 5, vincoli, usa_volontario,
            randomness=randomness, seed=seed_value
        )

    if risultato['meta'].get('budget_rispettato', False):
        st.success("Turnazione generata! Budget ore rispettato per tutti.")
    else:
        st.warning("Turnazione generata con alcuni turni assegnati a Volontario esperto.")

    st.caption(f"Seed iniziale: **{seed_value}** | Randomness: **{randomness}**")

    # Mostra risultato
    mostra_turnazione(risultato, vincoli, data_inizio, usa_volontario, notte_attiva)

# --- Footer ---
st.divider()
st.caption("Croce Rossa - Sistema Pianificazione Turni | v2.0")

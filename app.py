"""
App Streamlit per generazione turnazione 5 settimane.
Croce Rossa - Pianificazione Turni

Supporta confronto versioni:
- A: Staff attuale
- B: Staff + nuovo dipendente (ore scelte)
- C: Staff + nuovo dipendente (alternativa PT/FT)
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
    add_employee,
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


# --- Funzioni helper per visualizzazione ---
def mostra_versione(nome_versione: str, risultato: dict, vincoli: dict,
                    data_inizio: date, usa_volontario: bool, notte_attiva: bool):
    """Mostra una versione completa con calendario, summary e download."""

    meta = risultato['meta']

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
        unc = meta['turni_scoperti']
        st.metric("Scoperture", unc,
                  delta=f"{unc} turni" if unc > 0 else None,
                  delta_color="inverse" if unc > 0 else "off")

    # Avvisi
    if meta['turni_volontario'] > 0:
        st.warning(f"Volontario richiesto per {meta['turni_volontario']} turni.")
    if meta['turni_scoperti'] > 0:
        st.error(f"{meta['turni_scoperti']} turni SCOPERTI!")

    # Calendario
    with st.expander("Calendario turni", expanded=False):
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

    # Riepilogo ore
    with st.expander("Riepilogo ore per persona", expanded=False):
        summary_df = risultato['summary']

        def highlight_scost(val):
            if isinstance(val, (int, float)):
                if val < 0:
                    return 'color: #dc3545'
                elif val > 0:
                    return 'color: #28a745'
            return ''

        st.dataframe(summary_df.style.applymap(highlight_scost, subset=['Scostamento']),
                     use_container_width=True, hide_index=True)
        st.caption(f"Scostamento max-min: **{meta['scostamento_ore']}h**")

        # Grafico ore per persona
        fig, ax = plt.subplots(figsize=(8, 4))
        names = summary_df['Nome'].tolist()
        hours = summary_df['Ore totali'].tolist()
        targets = summary_df['Target (5 sett)'].tolist()

        x = range(len(names))
        width = 0.35

        bars1 = ax.bar([i - width/2 for i in x], hours, width, label='Ore assegnate')
        bars2 = ax.bar([i + width/2 for i in x], targets, width, label='Target', alpha=0.6)

        ax.set_ylabel('Ore')
        ax.set_title('Ore assegnate vs Target (5 settimane)')
        ax.set_xticks(list(x))
        ax.set_xticklabels([n.split()[0] for n in names], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Download
    date_str = data_inizio.strftime('%Y%m%d')
    file_base = f"turnazione_{date_str}_{nome_versione.lower().replace(' ', '_').replace('+', 'plus')}"

    col_csv, col_excel, col_pdf = st.columns(3)
    with col_csv:
        st.download_button(
            f"CSV {nome_versione}",
            export_csv(risultato['calendario'], notte_attiva),
            f"{file_base}.csv", "text/csv",
            use_container_width=True, key=f"csv_{nome_versione}"
        )
    with col_excel:
        st.download_button(
            f"Excel {nome_versione}",
            export_excel(risultato, notte_attiva),
            f"{file_base}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, key=f"xlsx_{nome_versione}"
        )
    with col_pdf:
        st.download_button(
            f"PDF {nome_versione}",
            export_pdf(risultato, data_inizio, vincoli, usa_volontario, notte_attiva),
            f"{file_base}.pdf", "application/pdf",
            use_container_width=True, key=f"pdf_{nome_versione}"
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
    st.subheader("Staff attuale")
    edited_staff = st.data_editor(
        st.session_state.staff,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            'Nome': st.column_config.TextColumn('Nome', required=True),
            'Ore settimanali': st.column_config.NumberColumn('Ore/sett', min_value=1, max_value=48, step=1),
            'Può fare notte': st.column_config.CheckboxColumn('Notte', default=False),
            'Può lavorare domenica': st.column_config.CheckboxColumn('Domenica', default=True)
        },
        hide_index=True,
        key="staff_editor"
    )
    st.session_state.staff = edited_staff
    total_hours = edited_staff['Ore settimanali'].sum()
    st.caption(f"**{len(edited_staff)} dipendenti** - **{total_hours}h/settimana**")

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

# --- Nuovo dipendente per confronto ---
st.divider()
st.subheader("Nuovo dipendente (per confronto versioni)")
st.caption("Lascia vuoto per generare solo la versione attuale. Compila per confrontare scenari.")

col_nome, col_tipo, col_opz = st.columns([2, 2, 1])

with col_nome:
    nuovo_nome = st.text_input("Nome nuovo dipendente", placeholder="Es: Mario Rossi", key="nuovo_nome")

with col_tipo:
    tipo_contratto = st.radio(
        "Tipo contratto",
        options=['PT 28h', 'FT 38h', 'Personalizzato'],
        horizontal=True,
        key="tipo_contratto"
    )

with col_opz:
    if tipo_contratto == 'PT 28h':
        nuove_ore = 28
        st.metric("Ore", "28h")
    elif tipo_contratto == 'FT 38h':
        nuove_ore = 38
        st.metric("Ore", "38h")
    else:
        nuove_ore = st.number_input("Ore custom", 1, 48, 30, key="ore_custom")

col_n, col_d = st.columns(2)
nuovo_puo_notte = col_n.checkbox("Può fare notte", value=True, key="nuovo_notte")
nuovo_puo_dom = col_d.checkbox("Può lavorare domenica", value=True, key="nuovo_dom")

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
    c3.metric("Ore disponibili", f"{ore_disp}h")
    delta = ore_disp - fabbisogno['ore_totali_richieste']
    c4.metric("Bilancio", f"{delta:+}h", delta_color="normal" if delta >= 0 else "inverse")

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

    versioni = {}
    staff_base = st.session_state.staff.copy()

    with st.spinner("Generazione in corso..."):

        # Versione A: Staff attuale
        versioni['A - Staff attuale'] = genera_turnazione(
            staff_base, data_inizio, 5, vincoli, usa_volontario,
            randomness=randomness, seed=seed_value
        )

        # Se c'è un nuovo dipendente, genera anche B e C
        nuovo_nome_clean = nuovo_nome.strip()
        if nuovo_nome_clean:

            # Versione B: con ore scelte
            staff_b, err_b = add_employee(staff_base, nuovo_nome_clean, nuove_ore, nuovo_puo_notte, nuovo_puo_dom)
            if not err_b:
                label_b = f"B - +{nuovo_nome_clean} ({nuove_ore}h)"
                versioni[label_b] = genera_turnazione(
                    staff_b, data_inizio, 5, vincoli, usa_volontario,
                    randomness=randomness, seed=seed_value + 1
                )

            # Versione C: alternativa
            if tipo_contratto == 'PT 28h':
                ore_alt = 38
                label_alt = "FT 38h"
            elif tipo_contratto == 'FT 38h':
                ore_alt = 28
                label_alt = "PT 28h"
            else:
                # Custom: genera sia PT che FT
                ore_alt = 28
                label_alt = "PT 28h"
                # Versione C1: PT
                staff_c1, _ = add_employee(staff_base, nuovo_nome_clean, 28, nuovo_puo_notte, nuovo_puo_dom)
                versioni[f"C1 - +{nuovo_nome_clean} (PT 28h)"] = genera_turnazione(
                    staff_c1, data_inizio, 5, vincoli, usa_volontario,
                    randomness=randomness, seed=seed_value + 2
                )
                # Versione C2: FT
                staff_c2, _ = add_employee(staff_base, nuovo_nome_clean, 38, nuovo_puo_notte, nuovo_puo_dom)
                versioni[f"C2 - +{nuovo_nome_clean} (FT 38h)"] = genera_turnazione(
                    staff_c2, data_inizio, 5, vincoli, usa_volontario,
                    randomness=randomness, seed=seed_value + 3
                )
                ore_alt = None  # Skip versione C singola

            if ore_alt and tipo_contratto != 'Personalizzato':
                staff_c, err_c = add_employee(staff_base, nuovo_nome_clean, ore_alt, nuovo_puo_notte, nuovo_puo_dom)
                if not err_c:
                    label_c = f"C - +{nuovo_nome_clean} ({label_alt})"
                    versioni[label_c] = genera_turnazione(
                        staff_c, data_inizio, 5, vincoli, usa_volontario,
                        randomness=randomness, seed=seed_value + 4
                    )

    st.success(f"Generate {len(versioni)} versioni!")
    st.caption(f"Seed usato: **{seed_value}** | Randomness: **{randomness}**")

    # --- Tabella comparativa ---
    st.subheader("Confronto versioni")

    compare_data = []
    for nome_v, ris in versioni.items():
        m = ris['meta']
        s = ris['summary']
        row = {
            'Versione': nome_v,
            'Volontario (turni)': m['turni_volontario'],
            'Ore volontario': m['turni_volontario'] * 7,
            'Scoperture': m['turni_scoperti'],
            'Copertura %': m['copertura_interna_pct'],
            'Scost. ore max-min': m['scostamento_ore'],
            'Domeniche (distribuzione)': '/'.join(str(x) for x in s['Domeniche'].tolist()),
        }
        if notte_attiva and 'Notti' in s.columns:
            row['Notti (distribuzione)'] = '/'.join(str(x) for x in s['Notti'].tolist())
        compare_data.append(row)

    compare_df = pd.DataFrame(compare_data)

    # Evidenzia la migliore (meno volontario)
    def highlight_best(row):
        styles = [''] * len(row)
        if row['Volontario (turni)'] == compare_df['Volontario (turni)'].min():
            styles[0] = 'background-color: #d4edda'
        return styles

    st.dataframe(
        compare_df.style.apply(highlight_best, axis=1),
        use_container_width=True,
        hide_index=True
    )

    # --- Testo "Cosa cambia" ---
    if len(versioni) > 1:
        st.subheader("Cosa cambia?")

        meta_a = versioni['A - Staff attuale']['meta']
        vol_a = meta_a['turni_volontario']

        for nome_v, ris in versioni.items():
            if nome_v == 'A - Staff attuale':
                continue

            m = ris['meta']
            vol_diff = vol_a - m['turni_volontario']
            ore_diff = vol_diff * 7

            if vol_diff > 0:
                st.markdown(
                    f"**{nome_v}**: riduce il ricorso a Volontario esperto di **{vol_diff} turni** "
                    f"({ore_diff}h), portando la copertura interna al **{m['copertura_interna_pct']}%**."
                )
            elif vol_diff < 0:
                st.markdown(
                    f"**{nome_v}**: aumenta il ricorso a Volontario esperto di **{abs(vol_diff)} turni**. "
                    f"Potrebbe indicare un problema di distribuzione."
                )
            else:
                st.markdown(
                    f"**{nome_v}**: stesso numero di turni Volontario ({m['turni_volontario']}), "
                    f"ma migliore distribuzione del carico (scostamento: {m['scostamento_ore']}h)."
                )

        # Raccomandazione
        st.divider()
        best_version = min(versioni.items(), key=lambda x: (x[1]['meta']['turni_volontario'], x[1]['meta']['scostamento_ore']))
        best_name = best_version[0]
        best_meta = best_version[1]['meta']

        if best_meta['turni_volontario'] == 0:
            st.success(
                f"**Raccomandazione**: {best_name} garantisce copertura completa al 100% "
                f"senza ricorso a volontari esterni."
            )
        else:
            st.info(
                f"**Raccomandazione**: {best_name} minimizza il ricorso a volontari "
                f"({best_meta['turni_volontario']} turni). Valuta l'aggiunta di personale per eliminare le carenze."
            )

    # --- Mostra ogni versione ---
    st.divider()
    st.subheader("Dettaglio versioni")

    tabs = st.tabs(list(versioni.keys()))
    for tab, (nome_v, ris) in zip(tabs, versioni.items()):
        with tab:
            mostra_versione(nome_v, ris, vincoli, data_inizio, usa_volontario, notte_attiva)

# --- Footer ---
st.divider()
st.caption("Croce Rossa - Sistema Pianificazione Turni | v1.0")

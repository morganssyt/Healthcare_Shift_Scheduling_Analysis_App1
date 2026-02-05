"""
Exporters per output in vari formati: CSV, Excel, PDF.
"""
import pandas as pd
from io import BytesIO
from datetime import date
from typing import Dict, Any

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

VOLUNTEER = "Volontario esperto"
SHIFT_NAMES = {'morning': 'Mattino', 'afternoon': 'Pomeriggio', 'night': 'Notte'}


def export_csv(calendario_df: pd.DataFrame, notte_attiva: bool) -> bytes:
    """
    Esporta calendario in CSV turn-level.
    Formato: date, shift, assignee (una riga per persona assegnata)
    """
    rows = []

    for _, row in calendario_df.iterrows():
        data = row['Data']
        date_str = data.strftime('%Y-%m-%d') if hasattr(data, 'strftime') else str(data)

        # Mattino
        mattino = row.get('Mattino', '-')
        if mattino and mattino != '-':
            for person in mattino.split(', '):
                rows.append({'date': date_str, 'shift': 'Mattino', 'assignee': person.strip()})

        # Pomeriggio
        pomeriggio = row.get('Pomeriggio', '-')
        if pomeriggio and pomeriggio != '-':
            for person in pomeriggio.split(', '):
                rows.append({'date': date_str, 'shift': 'Pomeriggio', 'assignee': person.strip()})

        # Notte
        if notte_attiva:
            notte = row.get('Notte', '-')
            if notte and notte != '-':
                for person in notte.split(', '):
                    rows.append({'date': date_str, 'shift': 'Notte', 'assignee': person.strip()})

    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode('utf-8')


def export_excel(risultato: dict, notte_attiva: bool) -> bytes:
    """
    Esporta risultato completo in Excel con due fogli:
    - Calendario: data, giorno, settimana, turni
    - Riepilogo: summary per persona
    """
    output = BytesIO()

    calendario_df = risultato['calendario'].copy()
    summary_df = risultato['summary'].copy()

    # Formatta date per Excel
    if 'Data' in calendario_df.columns:
        calendario_df['Data'] = pd.to_datetime(calendario_df['Data']).dt.strftime('%d/%m/%Y')

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet Calendario
        calendario_df.to_excel(writer, sheet_name='Calendario', index=False)

        # Formattazione Calendario
        ws_cal = writer.sheets['Calendario']
        for col in ws_cal.columns:
            max_length = max(len(str(cell.value or '')) for cell in col)
            ws_cal.column_dimensions[col[0].column_letter].width = min(max_length + 2, 40)
        # Abilita testo a capo
        from openpyxl.styles import Alignment
        for row in ws_cal.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical='top')

        # Sheet Riepilogo
        summary_df.to_excel(writer, sheet_name='Riepilogo', index=False)

        # Formattazione Riepilogo
        ws_sum = writer.sheets['Riepilogo']
        for col in ws_sum.columns:
            max_length = max(len(str(cell.value or '')) for cell in col)
            ws_sum.column_dimensions[col[0].column_letter].width = max_length + 2

    return output.getvalue()


def export_pdf(
    risultato: dict,
    data_inizio: date,
    vincoli: dict,
    usa_volontario: bool,
    notte_attiva: bool
) -> bytes:
    """
    Genera report PDF visivo stampabile.
    """
    output = BytesIO()

    # Usa landscape per tabelle larghe
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )

    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=12
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey
    )

    elements = []

    # --- Titolo ---
    elements.append(Paragraph("Turnazione 5 Settimane", title_style))
    elements.append(Spacer(1, 0.3*cm))

    # --- Periodo ---
    data_fine = data_inizio + pd.Timedelta(weeks=5) - pd.Timedelta(days=1)
    periodo_text = f"Periodo: {data_inizio.strftime('%d/%m/%Y')} - {data_fine.strftime('%d/%m/%Y')}"
    elements.append(Paragraph(periodo_text, normal_style))

    # --- Parametri ---
    params = []
    params.append(f"Min staff mattino lun-sab: {vincoli['min_mattino_lun_sab']}")
    params.append(f"Min staff pomeriggio lun-sab: {vincoli['min_pomeriggio_lun_sab']}")
    params.append(f"Min domenica mattino: {vincoli['min_dom_mattino']}")
    params.append(f"Max giorni consecutivi: {vincoli['max_consecutivi']}")

    if notte_attiva:
        giorni_str = ', '.join(vincoli.get('giorni_notte', []))
        params.append(f"Notte attiva: {giorni_str} (min {vincoli.get('min_notte', 1)})")
    else:
        params.append("Notte: non attiva")

    params.append(f"Volontario esperto: {'Attivo' if usa_volontario else 'Disattivo'}")

    elements.append(Paragraph(" | ".join(params), small_style))
    elements.append(Spacer(1, 0.5*cm))

    # --- Metriche ---
    meta = risultato['meta']
    metriche_text = (
        f"Turni totali: {meta['turni_totali']} | "
        f"Copertura interna: {meta['copertura_interna_pct']}% | "
        f"Volontario esperto: {meta['turni_volontario']} turni | "
        f"Scoperture: {meta['turni_scoperti']}"
    )
    elements.append(Paragraph(metriche_text, normal_style))
    elements.append(Spacer(1, 0.5*cm))

    # --- Calendari per settimana ---
    calendario_df = risultato['calendario']

    for week_num in range(1, 6):
        week_data = calendario_df[calendario_df['Settimana'] == week_num]
        if week_data.empty:
            continue

        first_date = week_data['Data'].iloc[0]
        last_date = week_data['Data'].iloc[-1]
        week_title = f"Settimana {week_num} ({first_date.strftime('%d/%m')} - {last_date.strftime('%d/%m/%Y')})"
        elements.append(Paragraph(week_title, heading_style))

        # Costruisci tabella
        if notte_attiva:
            headers = ['Giorno', 'Data', 'Mattino', 'Pomeriggio', 'Notte']
        else:
            headers = ['Giorno', 'Data', 'Mattino', 'Pomeriggio']

        table_data = [headers]

        for _, row in week_data.iterrows():
            data_str = row['Data'].strftime('%d/%m')
            if notte_attiva:
                table_row = [
                    row['Giorno'],
                    data_str,
                    row['Mattino'],
                    row['Pomeriggio'],
                    row.get('Notte', '-')
                ]
            else:
                table_row = [
                    row['Giorno'],
                    data_str,
                    row['Mattino'],
                    row['Pomeriggio']
                ]
            table_data.append(table_row)

        # Crea tabella
        if notte_attiva:
            col_widths = [2.5*cm, 2*cm, 6*cm, 6*cm, 6*cm]
        else:
            col_widths = [2.5*cm, 2*cm, 8*cm, 8*cm]

        table = Table(table_data, colWidths=col_widths)

        # Stile tabella
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]

        # Evidenzia celle con Volontario esperto
        for row_idx, row in enumerate(table_data[1:], start=1):
            for col_idx, cell in enumerate(row):
                if VOLUNTEER in str(cell):
                    style_commands.append(
                        ('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#fff3cd'))
                    )
                    style_commands.append(
                        ('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold')
                    )
                elif 'SCOPERTO' in str(cell):
                    style_commands.append(
                        ('BACKGROUND', (col_idx, row_idx), (col_idx, row_idx), colors.HexColor('#f8d7da'))
                    )
                    style_commands.append(
                        ('FONTNAME', (col_idx, row_idx), (col_idx, row_idx), 'Helvetica-Bold')
                    )

        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        elements.append(Spacer(1, 0.3*cm))

    # --- Nuova pagina per riepilogo ---
    elements.append(PageBreak())
    elements.append(Paragraph("Riepilogo Ore per Persona", title_style))
    elements.append(Spacer(1, 0.5*cm))

    # Tabella riepilogo
    summary_df = risultato['summary']

    # Headers
    summary_headers = list(summary_df.columns)
    summary_data = [summary_headers]

    for _, row in summary_df.iterrows():
        summary_data.append([str(v) for v in row.values])

    # Calcola larghezze colonne
    num_cols = len(summary_headers)
    available_width = 25 * cm  # landscape A4 width approx
    col_width = available_width / num_cols

    summary_table = Table(summary_data, colWidths=[col_width] * num_cols)

    summary_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]

    # Evidenzia scostamenti negativi
    scost_col_idx = summary_headers.index('Scostamento') if 'Scostamento' in summary_headers else -1
    if scost_col_idx >= 0:
        for row_idx, row in enumerate(summary_data[1:], start=1):
            try:
                val = int(row[scost_col_idx])
                if val < 0:
                    summary_style.append(
                        ('TEXTCOLOR', (scost_col_idx, row_idx), (scost_col_idx, row_idx), colors.HexColor('#dc3545'))
                    )
            except (ValueError, TypeError):
                pass

    summary_table.setStyle(TableStyle(summary_style))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*cm))

    # Note finali
    elements.append(Paragraph(
        f"Scostamento ore max-min: {meta['scostamento_ore']}h",
        normal_style
    ))

    if meta['turni_volontario'] > 0:
        elements.append(Paragraph(
            f"Volontario esperto richiesto per {meta['turni_volontario']} turni.",
            ParagraphStyle('Warning', parent=normal_style, textColor=colors.HexColor('#856404'))
        ))

    if meta['turni_scoperti'] > 0:
        elements.append(Paragraph(
            f"ATTENZIONE: {meta['turni_scoperti']} turni rimangono SCOPERTI!",
            ParagraphStyle('Error', parent=normal_style, textColor=colors.HexColor('#dc3545'))
        ))

    # Footer
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph(
        "Croce Rossa - Sistema Pianificazione Turni",
        ParagraphStyle('Footer', parent=small_style, alignment=TA_CENTER)
    ))

    # Genera PDF
    doc.build(elements)

    return output.getvalue()

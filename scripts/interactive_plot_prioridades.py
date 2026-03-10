import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
import datetime

EVENTS = [
    (datetime.date(2014, 1, 1), "Caso Penta"),
    (datetime.date(2015, 1, 1), 'Caso Caval, Corpesca, "Milicogate" y SQM'),
    (datetime.date(2017, 1, 1), '"Pacogate"'),
    (datetime.date(2023, 1, 1), "Caso Convenios/Fundaciones"),
    (datetime.date(2024, 1, 1), "Caso Audios/Hermosilla"),
]

EVENT_LABEL_HEIGHTS = [0.92, 0.82, 0.72, 0.88, 0.78]
EVENT_COLORS = ["#c0392b", "#2980b9", "#16a085", "#8e44ad", "#d35400"]

def load_data():
    # Intenta cargar los datos; si no existe el archivo, se maneja el error.
    try:
        data_prioridades_cep = pd.read_csv("data/PrioridadesTable_rows.csv")
    except FileNotFoundError:
        print("Error: El archivo 'data/PrioridadesTable_rows.csv' no fue encontrado.")
        return None
    return data_prioridades_cep

def clean_data(data_prioridades_cep):
    if data_prioridades_cep is None:
        return None
    
    # Filtrar por Corrupción
    data_prioridades_cep_corrupcion = data_prioridades_cep[
        data_prioridades_cep["Prioridades"] == "Corrupción"].copy()

    # Convertir fecha a datetime y luego a date
    data_prioridades_cep_corrupcion["fecha"] = pd.to_datetime(
        data_prioridades_cep_corrupcion["fecha"], errors="coerce", utc=True).dt.date
    
    # Eliminar nulos y ordenar cronológicamente
    data_prioridades_cep_corrupcion = data_prioridades_cep_corrupcion.dropna(subset=['fecha'])
    data_prioridades_cep_corrupcion = data_prioridades_cep_corrupcion.sort_values("fecha")
    
    return data_prioridades_cep_corrupcion

def grafico_animado_matplotlib(df):
    if df is None or df.empty:
        print("No hay datos para graficar.")
        return

    # --- Configuración Estética (Material Design) ---
    COLOR_BLUE = "#0077cc"
    COLOR_GREY = "#555"
    COLOR_WHITE = "#ffffff"
    
    plt.rcParams['font.family'] = 'sans-serif'
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLOR_WHITE)
    plt.subplots_adjust(bottom=0.2) # Espacio para botones

    # Titulo y fuente en estilo sutil para contexto del grafico.
    ax.set_title(
        "Evolución de la corrupción como primera prioridad",
        color=COLOR_GREY,
        fontsize=12,
        fontweight='normal',
        pad=12,
    )
    fig.text(
        0.5,
        0.03,
        "Fuente: Encuesta Centro de Estudios Públicos 1991-2025",
        ha='center',
        va='center',
        color=COLOR_GREY,
        fontsize=9,
        alpha=0.85,
    )
    
    # Elementos del gráfico
    line, = ax.plot([], [], color=COLOR_BLUE, linewidth=2.5, marker='o', 
                    markersize=6, markerfacecolor=COLOR_WHITE, markeredgewidth=1.5)
    event_artists = []
    for (event_date, event_label), label_height, event_color in zip(EVENTS, EVENT_LABEL_HEIGHTS, EVENT_COLORS):
        event_v_line = ax.axvline(
            x=event_date,
            color=event_color,
            alpha=0,
            linestyle='--',
            linewidth=1.5,
        )
        event_text = ax.text(
            event_date,
            0,
            event_label,
            color=event_color,
            alpha=0,
            fontweight='bold',
            fontsize=10,
            ha='center',
        )
        event_artists.append((event_v_line, event_text, label_height))

    # Configuración de ejes (estilo moderno: sin líneas de eje, ticks finos)
    ax.set_facecolor(COLOR_WHITE)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.tick_params(axis='both', colors=COLOR_GREY, width=0.8, length=4)
    ax.set_xlabel("Fecha (Año)", color=COLOR_GREY)
    ax.set_ylabel("Porcentaje (%)", color=COLOR_GREY)
    ax.grid(True, linestyle=':', alpha=0.3, color=COLOR_GREY)

    # Límites de los ejes
    ax.set_xlim(df['fecha'].min() - datetime.timedelta(days=365), df['fecha'].max() + datetime.timedelta(days=365))
    ax.set_ylim(0, 50)

    # --- Lógica de Animación ---
    # Timing: estos valores controlan directamente los fps y pausas del vídeo MP4.
    # fps del vídeo = 1000 / FRAME_INTERVAL_MS
    FRAME_INTERVAL_MS = 400    # ms por frame de datos  → 2.5 fps
    EVENT_PAUSE_FRAMES = 5    # frames repetidos al aparecer un evento → 10 × 400 ms = 2 s de pausa
    END_PAUSE_FRAMES = 22      # frames de pausa al final con la línea completa → 20 × 400 ms = 8 s

    # Insertamos frames de evento cuando la serie alcanza cada fecha relevante.
    # Los frames de evento se repiten EVENT_PAUSE_FRAMES veces para que la pausa
    # sea visible en el vídeo embebido (repeat_delay no funciona en HTML5 video).
    frames = []
    pending_events = EVENTS.copy()

    for i in range(len(df)):
        current_date = df.iloc[i]['fecha']
        while pending_events and current_date >= pending_events[0][0]:
            pending_events.pop(0)
            event_count = len(EVENTS) - len(pending_events)
            for _ in range(EVENT_PAUSE_FRAMES):
                frames.append(('event', i, event_count))
        frames.append(('point', i))

    # Pausa al final: repetir el último frame para que la línea completa quede visible.
    last_idx = len(df) - 1
    for _ in range(END_PAUSE_FRAMES):
        frames.append(('point', last_idx))

    def update(frame_info):
        f_type = frame_info[0]
        idx = frame_info[1]
        current_df = df.iloc[:idx+1]
        line.set_data(current_df['fecha'], current_df['Porcentaje'])
        
        if f_type == 'event':
            visible_events = frame_info[2]
            for event_v_line, event_text, label_height in event_artists[:visible_events]:
                event_v_line.set_alpha(0.2)
                event_text.set_alpha(0.7)
                event_text.set_position((event_v_line.get_xdata()[0], ax.get_ylim()[1] * label_height))
        
        artists = [line]
        for event_v_line, event_text, _ in event_artists:
            artists.extend((event_v_line, event_text))
        return tuple(artists)

    # repeat_delay no tiene efecto en vídeo HTML5; el loop lo maneja el atributo 'loop' del <video>.
    ani = animation.FuncAnimation(fig, update, frames=frames, interval=FRAME_INTERVAL_MS, blit=True, repeat=False)

    # --- GUARDAR COMO HTML SIN CONTROLES Y EN LOOP ---
    print("Generando archivo HTML limpio...")
    print(f"  Timing: {FRAME_INTERVAL_MS} ms/frame ({1000/FRAME_INTERVAL_MS:.1f} fps), pausa en eventos: {EVENT_PAUSE_FRAMES * FRAME_INTERVAL_MS / 1000:.1f} s")

    # Convertimos la animación a una etiqueta de video HTML5
    html_video = ani.to_html5_video()
    
    # Modificamos la etiqueta para que sea autoplay y loop infinito
    html_limpio = html_video.replace('controls', 'autoplay loop muted playsinline')

    # Guardamos el archivo
    with open("docs/interactive/prioridades_corrupcion.html", "w") as f:
        f.write(f"<html><body style='background-color:#ffffff; display:flex; justify-content:center;'>{html_limpio}</body></html>")
    
    print("Archivo 'prioridades_corrupcion.html' guardado (sin controles).")

if __name__ == "__main__":
    data = load_data()
    data_limpio = clean_data(data)
    
    if data_limpio is not None:
        print("Iniciando visualización...")
        grafico_animado_matplotlib(data_limpio)


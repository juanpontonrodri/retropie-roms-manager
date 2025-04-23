# -*- coding: utf-8 -*- # Añadido para mejor compatibilidad con caracteres
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, font, filedialog, simpledialog
import requests
from bs4 import BeautifulSoup
import os
import threading
import urllib.parse
import re # Para expresiones regulares en el filtrado
import time # Para posible pausa corta en bucle de descarga
import paramiko # <--- Añadido para soporte SCP
import stat # Para comprobar tipos de archivo SFTP

# --- Configuración ---

# FUENTES DE CONSOLAS AMPLIADO
# Basado en inspección manual de R-Roms (hacia ~Abril 2025) y usando fuentes Myrient
# NOTA: Colecciones Redump (PS1, PS2, Saturn, etc.) en Myrient usualmente NO están en .zip/.7z
#       por lo que el script actual probablemente NO encontrará archivos en esas URLs.
CONSOLE_SOURCES = {
    # --- Nintendo ---
    "NES": {
        "subfolder": "nes",
        "urls": ["https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20Entertainment%20System%20(Headered)/",
                 "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20Entertainment%20System%20(Headerless)/"]
    },
    "Game Boy": {
        "subfolder": "gb",
        "urls": ["https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Game%20Boy/"]
    },
    "SNES": {
        "subfolder": "snes",
        "urls": ["https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Super%20Nintendo%20Entertainment%20System/"]
    },
     "Nintendo 64": {
        "subfolder": "n64",
        "urls": ["https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%2064%20(BigEndian)/"]
    },
    "Game Boy Color": {
        "subfolder": "gbc",
        "urls": ["https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Game%20Boy%20Color/"]
    },
    "Game Boy Advance": {
        "subfolder": "gba",
        "urls": ["https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Game%20Boy%20Advance/"]
    },
     "Nintendo DS": {
        "subfolder": "nds",
        "urls": ["https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20DS%20(Decrypted)/",
                 "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20DS%20(Encrypted)/"]
    },
    # --- Sega ---
    "Sega Master System": {
        "subfolder": "mastersystem",
        "urls": ["https://myrient.erista.me/files/No-Intro/Sega%20-%20Master%20System%20-%20Mark%20III/"]
    },
    "Sega Mega Drive / Genesis": {
        "subfolder": "megadrive", # o genesis
        "urls": ["https://myrient.erista.me/files/No-Intro/Sega%20-%20Mega%20Drive%20-%20Genesis/"]
    },
    "Sega Game Gear": {
        "subfolder": "gamegear",
        "urls": ["https://myrient.erista.me/files/No-Intro/Sega%20-%20Game%20Gear/"]
    },
    "Sega Saturn": {
        "subfolder": "saturn",
        "urls": ["https://myrient.erista.me/files/Redump/Sega%20-%20Saturn/"] # Probablemente no encuentre .zip/.7z
    },
    "Sega Dreamcast": {
        "subfolder": "dreamcast",
        "urls": ["https://myrient.erista.me/files/Redump/Sega%20-%20Dreamcast/"] # Probablemente no encuentre .zip/.7z
    },
    # --- Sony ---
    "PlayStation": {
        "subfolder": "psx",
        "urls": ["https://myrient.erista.me/files/No-Intro/Sony%20-%20PlayStation/", # Set No-Intro (puede tener .zip/.7z?)
                 "https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation/"] # Set Redump (no .zip/.7z)
    },
    "PlayStation 2": {
        "subfolder": "ps2",
        "urls": ["https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%202/"] # Probablemente no encuentre .zip/.7z
    },
    "PSP": {
        "subfolder": "psp",
        "urls": ["https://myrient.erista.me/files/No-Intro/Sony%20-%20PlayStation%20Portable%20(PSN)/", # No-Intro (PSN)
                 "https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation%20Portable/"] # Redump (no .zip/.7z)
    },
    # --- Microsoft ---
     "Xbox": {
        "subfolder": "xbox",
        "urls": ["https://myrient.erista.me/files/Redump/Microsoft%20-%20Xbox/"] # Probablemente no encuentre .zip/.7z
    },
    "Xbox 360": {
        "subfolder": "xbox360",
        "urls": ["https://myrient.erista.me/files/Redump/Microsoft%20-%20Xbox%20360/"] # Probablemente no encuentre .zip/.7z
    },
    # --- Retro / Otros ---
    "Atari 2600": {
        "subfolder": "atari2600",
        "urls": ["https://myrient.erista.me/files/No-Intro/Atari%20-%202600/"]
    },
     "Atari 5200": {
        "subfolder": "atari5200",
        "urls": ["https://myrient.erista.me/files/No-Intro/Atari%20-%205200/"]
     },
    "Atari 7800": {
        "subfolder": "atari7800",
        "urls": ["https://myrient.erista.me/files/No-Intro/Atari%20-%207800/"]
    },
    "Atari Lynx": {
        "subfolder": "lynx",
        "urls": ["https://myrient.erista.me/files/No-Intro/Atari%20-%20Lynx/"]
    },
    "ColecoVision": {
        "subfolder": "coleco",
        "urls": ["https://myrient.erista.me/files/No-Intro/Coleco%20-%20ColecoVision/"]
    },
    "Intellivision": {
        "subfolder": "intellivision",
        "urls": ["https://myrient.erista.me/files/No-Intro/Mattel%20-%20Intellivision/"]
    },
     "Neo Geo Pocket Color": {
        "subfolder": "ngpc",
        "urls": ["https://myrient.erista.me/files/No-Intro/SNK%20-%20Neo%20Geo%20Pocket%20Color/"]
    },
    "TurboGrafx-16 / PC Engine": {
        "subfolder": "tg16", # o pce
        "urls": ["https://myrient.erista.me/files/No-Intro/NEC%20-%20PC%20Engine%20-%20TurboGrafx%2016/"]
    },
    "WonderSwan Color": {
        "subfolder": "wsc",
        "urls": ["https://myrient.erista.me/files/No-Intro/Bandai%20-%20WonderSwan%20Color/"]
    },
    # Añadir más aquí si se encuentran fuentes Myrient/compatibles para ellas
}


DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Documents", "roms") # Carpeta por defecto en Documentos/roms
selected_base_folder = DEFAULT_DOWNLOAD_FOLDER # Variable global para la carpeta base

USER_AGENT = "SimplePythonDownloader/2.1" # Incrementar versión

# --- Colores para destacar ---
COLOR_DECRYPTED_SPAIN = '#32CD32' # Verde Lima Intenso
COLOR_DECRYPTED_EUROPE_ES = '#90EE90' # Verde Claro
COLOR_DECRYPTED_EUROPE_GENERIC = '#98FB98' # Verde Pálido (Nuevo)
COLOR_ENCRYPTED_SPAIN = '#FFFFE0' # Amarillo Claro

# --- Funciones Lógicas (fetch_rom_list, parse_rom_list, filter_roms sin cambios necesarios aquí) ---
# (El código de estas funciones es el mismo que en la respuesta anterior)
def fetch_rom_list(url):
    """Obtiene la lista de archivos de la URL dada."""
    try:
        headers = {'User-Agent': USER_AGENT}
        # Aumentar un poco el timeout inicial
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        # Intentar decodificar con utf-8, ignorando errores
        return response.content.decode('utf-8', errors='ignore'), None # Devuelve texto y ningún error
    except requests.exceptions.Timeout:
        error_msg = f"Timeout al conectar a: {url}"
        print(error_msg)
        return None, error_msg
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de Red ({e.__class__.__name__}) en {url}"
        print(f"{error_msg}: {e}")
        return None, error_msg
    except Exception as e:
        error_msg = f"Error inesperado conectando a {url}: {e}"
        print(error_msg)
        return None, error_msg


def parse_rom_list(html_content, base_url):
    """Parsea el HTML y extrae los nombres y URLs de los archivos .zip o .7z."""
    # LIMITACIÓN: No busca .iso, .chd, .cue, etc.
    roms = []
    if not html_content:
        return roms
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Buscar enlaces que terminen en .zip o .7z (insensible a mayúsculas)
        links = soup.find_all('a', href=lambda href: href and (href.lower().endswith('.zip') or href.lower().endswith('.7z')))

        for link in links:
            filename = link.text.strip()
            if filename == "../" or "Parent Directory" in filename:
                continue
            relative_url = link['href']
            if urllib.parse.urlparse(relative_url).scheme in ['http', 'https']:
                 full_url = relative_url
            else:
                 # Asegurarse que la URL base termina en / para la unión correcta
                 if not base_url.endswith('/'):
                     base_url += '/'
                 full_url = urllib.parse.urljoin(base_url, relative_url)

            roms.append({'name': filename, 'url': full_url})
    except Exception as e:
        print(f"Error parseando HTML de {base_url}: {e}")
    return roms


def filter_roms(rom_list, keyword):
    """
    Filtra la lista de ROMs según el keyword y región/idioma.
    Incluye si: keyword coincide (o no hay keyword) Y (contiene (Europe) O indicador Español/España)
    """
    filtered_roms = []
    keyword_lower = keyword.lower() if keyword else ""

    # Patrones (compilados una sola vez)
    try:
        spanish_indicators = [r'\(spain\)', r'\(es\)', r'\(es-es\)', r'\(spa\)', r'español']
        spanish_pattern = re.compile('|'.join(spanish_indicators), re.IGNORECASE)
        europe_pattern = re.compile(r'\(europe\)', re.IGNORECASE)
    except re.error as e:
        print(f"Error compilando regex: {e}")
        # Fallback: no filtrar por región/idioma si hay error de regex
        spanish_pattern = None
        europe_pattern = None


    for rom in rom_list:
        # Keyword check
        if keyword_lower and keyword_lower not in rom['name'].lower():
            continue # Saltar si no coincide la keyword (y se proporcionó una)

        # Region/Language check (solo si los patrones se compilaron bien)
        if europe_pattern and spanish_pattern:
             is_europe = europe_pattern.search(rom['name'])
             is_spanish_related = spanish_pattern.search(rom['name'])
             if not (is_europe or is_spanish_related):
                 continue # Saltar si no es Europe ni Spanish related

        # Si pasa todos los filtros, añadir
        filtered_roms.append(rom)

    return filtered_roms

# --- Funciones de Descarga (download_file, try_remove_partial, start_download_thread, run_downloads) ---
# (El código de estas funciones es el mismo que en la respuesta anterior)
def download_file(rom_info, base_download_folder, progress_var, status_label):
    """Descarga un archivo desde la URL a la subcarpeta especificada."""
    url = rom_info['url']
    console_subfolder = rom_info['console_subfolder']
    # Crear nombre de subcarpeta seguro (ej. reemplazar '/')
    safe_subfolder_name = console_subfolder.replace('/', '_').replace('\\', '_')
    save_path = os.path.join(base_download_folder, safe_subfolder_name)

    try:
        os.makedirs(save_path, exist_ok=True)

        # Decodificar nombre de archivo de URL
        filename_encoded = os.path.basename(url)
        try:
            filename = urllib.parse.unquote(filename_encoded, encoding='utf-8', errors='replace')
        except Exception: # Fallback por si acaso
             filename = filename_encoded # Usar nombre codificado si falla decodificación

        full_save_path = os.path.join(save_path, filename)

        if os.path.exists(full_save_path):
           status_label.config(text=f"Ya existe [{safe_subfolder_name}]: {filename[:50]}...") # Acortar nombre largo
           progress_var.set(100)
           return True, None, f"Ya existe: {filename}"

        status_label.config(text=f"Descargando [{safe_subfolder_name}]: {filename[:50]}...")
        progress_var.set(0)

        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, stream=True, timeout=(10, 120))
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        bytes_downloaded = 0
        chunk_size = 8192 * 4
        last_update_kb = 0
        update_interval_kb = 1024

        with open(full_save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if total_size > 0:
                        percentage = int((bytes_downloaded / total_size) * 100)
                        progress_var.set(percentage)
                        current_kb = bytes_downloaded // 1024
                        if current_kb > last_update_kb + update_interval_kb :
                             status_label.config(text=f"Descargando [{safe_subfolder_name}]: {filename[:40]}... ({percentage}%)")
                             last_update_kb = current_kb
                    else:
                        current_mb = bytes_downloaded / (1024*1024)
                        status_label.config(text=f"Descargando [{safe_subfolder_name}]: {filename[:40]}... ({current_mb:.1f} MB)")
                        progress_var.set(50)

        progress_var.set(100)
        final_status = f"Descargado [{safe_subfolder_name}]: {filename}"
        status_label.config(text=final_status)
        return True, None, final_status

    except requests.exceptions.Timeout:
        error_msg = f"Timeout descargando {filename}"
        status_label.config(text=f"Error Timeout: {filename[:50]}...")
        print(error_msg)
        if 'full_save_path' in locals() and os.path.exists(full_save_path): try_remove_partial(full_save_path)
        return False, error_msg, None
    except requests.exceptions.RequestException as e:
        error_msg = f"Error red descargando {filename}: {e}"
        status_label.config(text=f"Error Red: {filename[:50]}...")
        print(error_msg)
        if 'full_save_path' in locals() and os.path.exists(full_save_path): try_remove_partial(full_save_path)
        return False, error_msg, None
    except IOError as e:
        error_msg = f"Error archivo guardando {filename}: {e}"
        status_label.config(text=f"Error Archivo: {filename[:50]}...")
        print(error_msg)
        return False, error_msg, None
    except Exception as e:
        error_msg = f"Error inesperado descargando {filename}: {e}"
        status_label.config(text=f"Error Inesperado: {filename[:50]}...")
        print(error_msg)
        if 'full_save_path' in locals() and os.path.exists(full_save_path): try_remove_partial(full_save_path)
        return False, error_msg, None

def try_remove_partial(filepath):
    """Intenta eliminar un archivo parcial, ignorando errores."""
    try:
        os.remove(filepath)
        print(f"Archivo parcial eliminado: {filepath}")
    except OSError as e:
        print(f"No se pudo eliminar el archivo parcial {filepath}: {e}")
        pass

def start_download_thread(selected_roms, status_label, progress_bar, download_button):
    """Inicia el proceso de descarga en un hilo separado."""
    if not selected_base_folder or not os.path.isdir(selected_base_folder):
         messagebox.showerror("Carpeta Inválida", f"La carpeta de descarga base no es válida:\n{selected_base_folder}\nPor favor, selecciona una carpeta válida.")
         return

    download_button.config(state=tk.DISABLED)
    status_label.config(text=f"Preparando descargas a: {selected_base_folder}...")

    try:
        os.makedirs(selected_base_folder, exist_ok=True)
    except OSError as e:
        messagebox.showerror("Error de Carpeta", f"No se pudo crear la carpeta base:\n{selected_base_folder}\nError: {e}")
        status_label.config(text="Error al crear carpeta base.")
        download_button.config(state=tk.NORMAL)
        return

    thread = threading.Thread(target=run_downloads, args=(selected_roms, status_label, progress_bar, download_button), daemon=True)
    thread.start()

def run_downloads(selected_roms, status_label, progress_bar, download_button):
    """Función que se ejecuta en el hilo para descargar los archivos."""
    total_files = len(selected_roms)
    success_count = 0
    skipped_count = 0
    error_count = 0
    errors_list = []
    # No almacenar todos los mensajes de éxito para evitar consumo memoria
    # success_messages = []

    current_file_progress = tk.IntVar()
    progress_bar['variable'] = current_file_progress

    for i, rom_info in enumerate(selected_roms):
        if 'url' not in rom_info or 'console_subfolder' not in rom_info:
            error_msg = f"ROM {i+1}: Información incompleta"
            print(f"Error: {error_msg}. Saltando.")
            error_count += 1
            errors_list.append(error_msg)
            continue

        success, error_msg, status_msg = download_file(rom_info, selected_base_folder, current_file_progress, status_label)

        if success:
            if "Ya existe" in (status_msg or ""):
                skipped_count += 1
            else:
                 success_count += 1
            # if status_msg: success_messages.append(status_msg) # Evitar guardar todos
        else:
            error_count += 1
            rom_name = rom_info.get('name', 'Desconocido')[:60] # Acortar nombre en error
            if error_msg: errors_list.append(f"{rom_name}...: {error_msg}")

        # Pausa corta opcional para permitir que la GUI respire
        time.sleep(0.01)


    progress_bar['variable'] = None
    progress_bar['value'] = 0

    final_message = f"Completado. Descargados: {success_count}, Ya existentes: {skipped_count}, Errores: {error_count}."
    if errors_list:
        error_details = "\n - ".join(errors_list[:5]) # Mostrar primeros 5 errores
        final_message += f"\nErrores:\n - {error_details}"
        if len(errors_list) > 5:
            final_message += "\n  (Ver consola para más detalles)"
        messagebox.showwarning("Descarga Finalizada con Errores", final_message)

    status_label.config(text=final_message)
    download_button.config(state=tk.NORMAL)


# --- Funciones de la GUI ---

# ++ NUEVA CLASE Tooltip ++
class Tooltip:
    """
    Crea un Tooltip (ventana emergente) para un widget de tkinter.
    """
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave) # Ocultar si se hace clic
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip) # Espera 500ms

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert") # Obtener coords relativas al widget
        x += self.widget.winfo_rootx() + 25 # Posición X global + offset
        y += self.widget.winfo_rooty() + 20 # Posición Y global + offset
        # Crear ventana Toplevel
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True) # Sin decoración de ventana
        self.tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()
# ++ FIN NUEVA CLASE Tooltip ++


def _on_mousewheel(event, target_canvas):
    """Manejador genérico de la rueda del ratón para desplazar un canvas."""
    # Linux usa event.num (Button-4 para arriba, Button-5 para abajo)
    if event.num == 4:
        target_canvas.yview_scroll(-1, "units")
    elif event.num == 5:
        target_canvas.yview_scroll(1, "units")
    # Windows/macOS usan event.delta (normalmente +/- 120)
    elif event.delta:
        target_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def select_download_folder():
    """Abre diálogo para seleccionar la carpeta base de descarga."""
    global selected_base_folder
    initial_dir = selected_base_folder if os.path.isdir(selected_base_folder) else os.path.expanduser("~")
    folder_selected = filedialog.askdirectory(initialdir=initial_dir, title="Selecciona la carpeta base para ROMs")
    if folder_selected:
        selected_base_folder = os.path.normpath(folder_selected)
        folder_label.config(text=f"Descargar en: {selected_base_folder}")
    else:
        if not selected_base_folder:
            selected_base_folder = DEFAULT_DOWNLOAD_FOLDER
        folder_label.config(text=f"Descargar en: {selected_base_folder}")


def get_selected_consoles():
    """Devuelve una lista con los nombres de las consolas seleccionadas."""
    selected = []
    # Acceder a console_vars que está en el scope global/módulo
    for name, var in console_vars.items():
        if var.get():
            selected.append(name)
    return selected

def search_roms():
    """Función llamada al pulsar el botón de buscar."""
    keyword = keyword_entry.get().strip()
    selected_consoles = get_selected_consoles()

    if not selected_consoles:
        messagebox.showwarning("Sin Selección", "Por favor, selecciona al menos una consola para buscar.")
        return

    if not selected_base_folder or not os.path.isdir(selected_base_folder):
         messagebox.showerror("Carpeta Inválida", f"La carpeta de descarga base no es válida:\n{selected_base_folder}\nPor favor, selecciona una carpeta válida antes de buscar.")
         return

    status_label.config(text="Buscando en fuentes seleccionadas...")
    search_button.config(state=tk.DISABLED)
    download_button.config(state=tk.DISABLED)

    for widget in results_frame.winfo_children():
            widget.destroy()
    results_list.clear()
    results_vars.clear()

    thread = threading.Thread(target=perform_search, args=(keyword, selected_consoles), daemon=True)
    thread.start()

def perform_search(keyword, selected_consoles):
    """Realiza la búsqueda en las fuentes de las consolas seleccionadas."""
    all_filtered_roms = []
    fetch_errors = []

    # Calcular total de URLs a revisar para mejor feedback (opcional)
    total_sources_to_check = 0
    try:
        total_sources_to_check = sum(len(CONSOLE_SOURCES[name]["urls"]) for name in selected_consoles if name in CONSOLE_SOURCES)
    except KeyError as e:
        print(f"Error: Consola '{e}' seleccionada pero no encontrada en CONSOLE_SOURCES.")
        # Continuar sin el conteo total preciso o manejar el error de otra forma

    sources_checked = 0

    for console_name in selected_consoles:
         if console_name not in CONSOLE_SOURCES:
             print(f"Advertencia: Consola '{console_name}' seleccionada pero no definida en CONSOLE_SOURCES. Saltando.")
             continue

         console_info = CONSOLE_SOURCES[console_name]
         console_subfolder = console_info["subfolder"]
         urls_to_check = console_info.get("urls", []) # Usar .get para evitar error si falta 'urls'

         if not urls_to_check:
              print(f"Advertencia: No hay URLs definidas para '{console_name}'. Saltando.")
              continue

         for url in urls_to_check:
            sources_checked += 1
            # Actualizar estado con menos frecuencia si hay muchas fuentes
            if sources_checked % 5 == 0 or sources_checked == total_sources_to_check:
                 app.after(0, lambda current=sources_checked, total=total_sources_to_check, name=console_name: status_label.config(text=f"Buscando {name} ({current}/{total})..."))

            html, error = fetch_rom_list(url)
            if error:
                # Limitar longitud del error mostrado
                fetch_errors.append(f"{console_name} ({url[:50]}...): {error[:100]}")
                continue

            if html:
                parsed_list = parse_rom_list(html, url)
                # Aplicar filtro de keyword Y region/idioma
                filtered_list = filter_roms(parsed_list, keyword)

                # Determinar tipo de fuente y estado de cifrado desde la URL
                source_type = "Desconocido"
                if "/No-Intro/" in url:
                    source_type = "No-Intro"
                elif "/Redump/" in url:
                    source_type = "Redump"

                encryption_status = ""
                if "(Decrypted)/" in url:
                    encryption_status = "Decrypted"
                elif "(Encrypted)/" in url:
                    encryption_status = "Encrypted"
                elif "(Headered)/" in url:
                    encryption_status = "Headered"
                elif "(Headerless)/" in url:
                    encryption_status = "Headerless"

                # Añadir info a cada ROM filtrada
                for rom in filtered_list:
                    rom['console_subfolder'] = console_subfolder
                    rom['console_display_name'] = console_name.split('/')[0].strip()
                    rom['source_type'] = source_type # ++ Guardar tipo
                    rom['encryption_status'] = encryption_status # ++ Guardar estado
                all_filtered_roms.extend(filtered_list)
            time.sleep(0.05)


    app.after(0, update_results_gui, all_filtered_roms, keyword, fetch_errors)


def update_results_gui(filtered_roms, keyword, fetch_errors):
    """Actualiza la lista de resultados en la GUI."""
    for widget in results_frame.winfo_children():
        widget.destroy()
    results_list.clear()
    results_vars.clear()

    # Ordenar resultados alfabéticamente por nombre completo (incluyendo consola)
    filtered_roms.sort(key=lambda x: f"[{x.get('console_display_name', 'N/A')}] {x.get('name', '')}")


    search_term_msg = f"para '{keyword}'" if keyword else ""
    if not filtered_roms:
        error_msg = "\nErrores al buscar:\n - " + "\n - ".join(fetch_errors) if fetch_errors else ""
        status_label.config(text=f"No se encontraron ROMs (.zip/.7z) {search_term_msg} en las consolas seleccionadas.{error_msg}")
    else:
        status_label.config(text=f"Se encontraron {len(filtered_roms)} ROMs {search_term_msg}. Selecciona cuáles descargar.")
        if fetch_errors:
             status_label.config(text=status_label.cget("text") + f" (Hubo {len(fetch_errors)} errores al buscar en algunas fuentes)")

    # Crear Checkbuttons
    for rom in filtered_roms:
        var = tk.BooleanVar()
        display_name = f"[{rom.get('console_display_name', '?')}] {rom['name']}"
        cb = ttk.Checkbutton(results_frame, text=display_name, variable=var, padding=(5, 1))

        # ++ Lógica de resaltado ++
        bg_color = None # Color de fondo por defecto (ninguno)
        rom_name = rom.get('name', '')
        enc_status = rom.get('encryption_status', '')

        is_decrypted = enc_status == 'Decrypted'
        is_encrypted = enc_status == 'Encrypted'
        # Usar re.IGNORECASE para búsquedas insensibles a mayúsculas/minúsculas
        is_spain = re.search(r'\(spain\)', rom_name, re.IGNORECASE)
        is_europe = re.search(r'\(europe\)', rom_name, re.IGNORECASE)
        # Buscar indicadores de idioma español
        is_spanish_lang = re.search(r'\(es\)|\bespañol\b|\(spa\)', rom_name, re.IGNORECASE) # \b para palabra completa "español"

        # Prioridad de reglas:
        if is_decrypted and is_spain:
            bg_color = COLOR_DECRYPTED_SPAIN
        elif is_decrypted and is_europe and is_spanish_lang:
            bg_color = COLOR_DECRYPTED_EUROPE_ES
        elif is_decrypted and is_europe: # NUEVA REGLA: Decrypted + Europe (genérico)
            bg_color = COLOR_DECRYPTED_EUROPE_GENERIC
        elif is_encrypted and is_spain:
            bg_color = COLOR_ENCRYPTED_SPAIN

        if bg_color:
            # Aplicar color de fondo. NOTA: ttk puede ignorar esto dependiendo del tema.
            # Una alternativa más robusta sería usar styles específicos.
            try:
                cb.configure(style=f"Highlight.{bg_color}.TCheckbutton")
                # Crear el estilo si no existe (esto puede necesitar hacerse una sola vez)
                # O configurar directamente el fondo (menos fiable con ttk)
                # cb.config(background=bg_color) # Menos fiable
            except tk.TclError: # Si el estilo no existe, intentar crearlo o usar config
                 try:
                     # Intentar configurar directamente (puede no funcionar bien con temas)
                     cb.config(background=bg_color)
                 except Exception as e_cfg:
                     print(f"Advertencia: No se pudo aplicar color {bg_color} a {rom_name[:30]}...: {e_cfg}")


        cb.pack(anchor='w', fill='x')
        results_list.append(rom)
        results_vars.append(var)

        # ++ Crear Tooltip ++
        tooltip_text = f"Fuente: {rom.get('source_type', 'N/A')}"
        if enc_status:
            tooltip_text += f" ({enc_status})"
        Tooltip(cb, text=tooltip_text)
        # ++ Fin Crear Tooltip ++

    search_button.config(state=tk.NORMAL)
    download_button.config(state=tk.NORMAL if filtered_roms else tk.DISABLED)

    # Forzar actualización de tamaño antes de configurar scrollregion
    app.update_idletasks()
    results_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))


def start_download():
    """Función llamada al pulsar el botón de descargar."""
    selected_roms_to_download = []
    for i, var in enumerate(results_vars):
        if var.get():
            selected_roms_to_download.append(results_list[i])

    if not selected_roms_to_download:
        messagebox.showwarning("Nada Seleccionado", "Por favor, marca las casillas de los juegos que quieres descargar.")
        return

    if not selected_base_folder or not os.path.isdir(selected_base_folder):
         messagebox.showerror("Carpeta Inválida", f"La carpeta de descarga base no es válida:\n{selected_base_folder}\nPor favor, selecciona una carpeta válida.")
         return

    confirm = messagebox.askyesno("Confirmar Descarga",
                                  f"Se descargarán {len(selected_roms_to_download)} archivos a subcarpetas dentro de:\n{selected_base_folder}\n\n¿Continuar?")

    if confirm:
        start_download_thread(selected_roms_to_download, status_label, progress_bar, download_button)


# --- NUEVAS FUNCIONES PARA COPIA SCP A RETROPIE ---

def prompt_retropie_credentials(parent_window):
    """Muestra un diálogo para pedir las credenciales de RetroPie."""
    dialog = tk.Toplevel(parent_window)
    dialog.title("Credenciales RetroPie SCP")
    dialog.transient(parent_window) # Hacerla modal sobre la ventana principal
    dialog.grab_set() # Capturar eventos
    dialog.resizable(False, False)

    # Centrar diálogo (aproximado)
    parent_window.update_idletasks()
    x = parent_window.winfo_x() + (parent_window.winfo_width() // 2) - 150 # Ajustar ancho estimado
    y = parent_window.winfo_y() + (parent_window.winfo_height() // 2) - 100 # Ajustar alto estimado
    dialog.geometry(f"300x180+{x}+{y}")

    frame = ttk.Frame(dialog, padding="10")
    frame.pack(expand=True, fill="both")

    ttk.Label(frame, text="IP RetroPie:").grid(row=0, column=0, sticky="w", pady=2)
    ip_entry = ttk.Entry(frame, width=25)
    ip_entry.insert(0, "retropie") # <--- Establecer IP por defecto
    ip_entry.grid(row=0, column=1, pady=2)
    ip_entry.focus_set() # Foco inicial

    ttk.Label(frame, text="Usuario:").grid(row=1, column=0, sticky="w", pady=2)
    user_entry = ttk.Entry(frame, width=25)
    user_entry.insert(0, "pi") # <--- Establecer usuario por defecto
    user_entry.grid(row=1, column=1, pady=2)


    ttk.Label(frame, text="Contraseña:").grid(row=2, column=0, sticky="w", pady=2)
    password_entry = ttk.Entry(frame, width=25, show="*") # Ocultar contraseña
    password_entry.grid(row=2, column=1, pady=2)

    results = {} # Diccionario para guardar los resultados

    def on_ok():
        results['ip'] = ip_entry.get().strip()
        results['user'] = user_entry.get().strip()
        results['password'] = password_entry.get() # No quitar strip aquí
        if not results['ip'] or not results['user']:
             messagebox.showwarning("Faltan Datos", "IP y Usuario son requeridos.", parent=dialog)
             return
        dialog.destroy()

    def on_cancel():
        results['cancelled'] = True
        dialog.destroy()

    button_frame = ttk.Frame(frame)
    button_frame.grid(row=3, column=0, columnspan=2, pady=15)

    ok_button = ttk.Button(button_frame, text="Aceptar", command=on_ok, width=10)
    ok_button.pack(side="left", padx=5)
    cancel_button = ttk.Button(button_frame, text="Cancelar", command=on_cancel, width=10)
    cancel_button.pack(side="left", padx=5)

    # Bind Enter a OK y Escape a Cancelar
    dialog.bind("<Return>", lambda event: on_ok())
    dialog.bind("<Escape>", lambda event: on_cancel())

    # Esperar a que el diálogo se cierre
    parent_window.wait_window(dialog)
    return results


def start_scp_copy_thread():
    """Pide credenciales e inicia el hilo de copia SCP si son válidas."""
    if not selected_base_folder or not os.path.isdir(selected_base_folder):
        messagebox.showerror("Carpeta Local Inválida",
                             f"La carpeta local de ROMs no es válida:\n{selected_base_folder}\n"
                             "Asegúrate de haber descargado o seleccionado una carpeta válida.")
        return

    # Verificar si hay subcarpetas de consolas en la carpeta local
    try:
        console_subdirs = [d for d in os.listdir(selected_base_folder)
                           if os.path.isdir(os.path.join(selected_base_folder, d))]
        if not console_subdirs:
             messagebox.showinfo("Carpeta Local Vacía",
                                f"La carpeta local:\n{selected_base_folder}\n"
                                "No contiene subcarpetas de consolas con ROMs para copiar.")
             return
    except Exception as e:
         messagebox.showerror("Error Carpeta Local", f"Error al leer la carpeta local:\n{e}")
         return


    credentials = prompt_retropie_credentials(app)

    if credentials.get('cancelled') or not credentials.get('ip') or not credentials.get('user'):
        status_label.config(text="Copia a RetroPie cancelada.")
        return

    # Deshabilitar botones mientras se copia
    scp_button.config(state=tk.DISABLED)
    download_button.config(state=tk.DISABLED) # Quizás también deshabilitar descarga
    search_button.config(state=tk.DISABLED) # Y búsqueda

    status_label.config(text=f"Iniciando conexión SCP a {credentials['ip']}...")

    thread = threading.Thread(target=run_scp_transfer,
                              args=(credentials['ip'], credentials['user'], credentials['password'],
                                    selected_base_folder, console_subdirs),
                              daemon=True)
    thread.start()


def run_scp_transfer(ip, user, password, local_base_path, local_console_dirs):
    """Se conecta por SSH/SCP y copia los archivos ROM faltantes."""
    remote_base_path = "~/RetroPie/roms" # Ruta estándar en RetroPie
    ssh = None
    sftp = None
    copied_count = 0
    skipped_count = 0
    extracted_count = 0
    error_count = 0
    errors_list = []
    
    # Lista de consolas que necesitan extracción de archivos comprimidos
    consolas_extraer = [
        'psp', 'psx', 'dreamcast', 'n64', 'saturn', 
        'gamecube', 'gc', 'wii', 'ps2'
    ]

    def update_status(message):
        # Función segura para actualizar la GUI desde el hilo
        app.after(0, status_label.config, {'text': message})

    def show_final_message(title, message, icon='info'):
        # Función segura para mostrar messagebox desde el hilo
        if icon == 'error':
            app.after(0, messagebox.showerror, title, message)
        elif icon == 'warning':
            app.after(0, messagebox.showwarning, title, message)
        else:
            app.after(0, messagebox.showinfo, title, message)
    
    def get_base_filename(filename):
        """Obtiene el nombre base del archivo sin la extensión"""
        return os.path.splitext(filename)[0]
    
    def extract_zip_on_remote(remote_file_path, remote_dir_path):
        """Extrae el archivo zip en el servidor remoto y elimina el zip original"""
        try:
            # Usar comandos de línea de comando en el servidor remoto para extraer
            update_status(f"Extrayendo en RetroPie: {os.path.basename(remote_file_path)}...")
            
            # Primero verificar qué utilidad de descompresión está disponible
            stdin, stdout, stderr = ssh.exec_command('which unzip 7z')
            available_tools = stdout.read().decode().strip().split('\n')
            
            extract_cmd = ""
            if any('unzip' in tool for tool in available_tools):
                # Usar unzip si está disponible (más común)
                extract_cmd = f'unzip -o "{remote_file_path}" -d "{remote_dir_path}" && rm "{remote_file_path}"'
            elif any('7z' in tool for tool in available_tools):
                # Usar 7z como alternativa
                extract_cmd = f'7z x "{remote_file_path}" -o"{remote_dir_path}" && rm "{remote_file_path}"'
            else:
                # Intentar instalar unzip si no está disponible
                update_status("Instalando herramienta de extracción en RetroPie...")
                ssh.exec_command('sudo apt-get update && sudo apt-get install -y unzip')
                extract_cmd = f'unzip -o "{remote_file_path}" -d "{remote_dir_path}" && rm "{remote_file_path}"'
            
            # Ejecutar el comando de extracción
            stdin, stdout, stderr = ssh.exec_command(extract_cmd)
            
            # Esperar a que termine la extracción
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code != 0:
                error_msg = stderr.read().decode().strip()
                raise Exception(f"Error en extracción (código {exit_code}): {error_msg}")
                
            return True
            
        except Exception as e:
            error_msg = f"Error extrayendo {os.path.basename(remote_file_path)}: {e}"
            errors_list.append(error_msg)
            update_status(f"Error de extracción: {os.path.basename(remote_file_path)}")
            return False

    try:
        update_status(f"Conectando a {ip} como {user}...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Aceptar clave automáticamente (menos seguro)
        # Considerar añadir un timeout más largo para conexiones lentas
        ssh.connect(hostname=ip, username=user, password=password, timeout=20)
        update_status("Conexión SSH establecida. Abriendo SFTP...")

        sftp = ssh.open_sftp()
        update_status("Canal SFTP abierto. Verificando ruta remota...")

        # Verificar si existe la carpeta base remota
        try:
            # Necesitamos expandir '~' manualmente o usar un comando
            stdin, stdout, stderr = ssh.exec_command(f'cd {remote_base_path} && pwd')
            expanded_remote_path = stdout.read().decode().strip()
            if not expanded_remote_path:
                 raise FileNotFoundError(f"No se pudo resolver o acceder a {remote_base_path}")

            sftp.stat(expanded_remote_path) # Verifica si existe y es accesible
            update_status(f"Ruta remota encontrada: {expanded_remote_path}")
            remote_base_path = expanded_remote_path # Usar la ruta expandida

        except (FileNotFoundError, paramiko.SFTPError, IOError) as e:
            error_msg = f"Error: La carpeta base remota '{remote_base_path}' no existe o no es accesible en {ip}.\nDetalle: {e}"
            errors_list.append(error_msg)
            update_status(f"Error: No se encontró {remote_base_path} en RetroPie.")
            show_final_message("Error de Ruta Remota", error_msg, icon='error')
            error_count += 1
            return # No podemos continuar

        # Iterar sobre las carpetas de consolas locales
        total_local_files = 0
        files_processed = 0
        for console_dir in local_console_dirs:
            local_console_path = os.path.join(local_base_path, console_dir)
            remote_console_path = f"{remote_base_path}/{console_dir}" # Usar / para rutas remotas
            
            # Identificar si esta consola necesita extracción
            needs_extraction = console_dir.lower() in consolas_extraer

            update_status(f"Procesando consola: {console_dir}...")

            # Crear carpeta de consola remota si no existe
            try:
                sftp.stat(remote_console_path)
            except FileNotFoundError:
                try:
                    update_status(f"Creando carpeta remota: {remote_console_path}")
                    sftp.mkdir(remote_console_path)
                except (paramiko.SFTPError, IOError) as e:
                    error_msg = f"No se pudo crear la carpeta remota {remote_console_path}: {e}"
                    errors_list.append(error_msg)
                    update_status(f"Error creando carpeta remota para {console_dir}. Saltando.")
                    error_count += 1
                    continue # Saltar esta consola si no se puede crear la carpeta

            # Listar archivos locales en la carpeta de la consola
            local_files = []
            try:
                local_files = [f for f in os.listdir(local_console_path)
                               if os.path.isfile(os.path.join(local_console_path, f))
                               and (f.lower().endswith('.zip') or f.lower().endswith('.7z'))] # Solo ROMs comprimidas
                total_local_files += len(local_files)
            except Exception as e:
                 error_msg = f"Error leyendo archivos locales en {local_console_path}: {e}"
                 errors_list.append(error_msg)
                 update_status(f"Error leyendo ROMs locales para {console_dir}. Saltando.")
                 error_count += 1
                 continue

            if not local_files:
                continue # No hay ROMs locales para esta consola

            # Listar archivos remotos y almacenar en un conjunto (más eficiente para búsquedas)
            remote_files_info = {} # {filename: size}
            remote_base_names = set() # Conjunto de nombres base sin extensión
            try:
                # Listdir puede ser lento en directorios grandes, pero necesario
                remote_listing = sftp.listdir_attr(remote_console_path)
                
                # Almacenar tanto los nombres con extensión como los nombres base
                for item in remote_listing:
                    if stat.S_ISREG(item.st_mode):  # Solo archivos regulares
                        remote_files_info[item.filename] = item.st_size
                        # Añadir nombre base (sin extensión) al conjunto
                        remote_base_names.add(get_base_filename(item.filename))
                        
            except (paramiko.SFTPError, IOError) as e:
                 error_msg = f"Error listando archivos remotos en {remote_console_path}: {e}"
                 errors_list.append(error_msg)
                 update_status(f"Error listando ROMs remotas para {console_dir}. Saltando copia para esta consola.")
                 error_count += len(local_files) # Contar como error si no podemos comparar
                 continue


            # Comparar y copiar
            for filename in local_files:
                files_processed += 1
                local_file_path = os.path.join(local_console_path, filename)
                remote_file_path = f"{remote_console_path}/{filename}"
                local_file_size = 0
                
                # Obtener nombre base para comparación
                base_filename = get_base_filename(filename)
                
                try:
                    local_file_size = os.path.getsize(local_file_path)
                except OSError as e:
                    error_msg = f"Error obteniendo tamaño local de {filename}: {e}"
                    errors_list.append(error_msg)
                    update_status(f"Error tamaño local {filename[:30]}... Saltando.")
                    error_count += 1
                    continue # Saltar este archivo si no podemos obtener su tamaño

                # Mostrar progreso más detallado
                progress_perc = int((files_processed / total_local_files) * 100) if total_local_files > 0 else 0
                update_status(f"[{progress_perc}%] Comprobando {console_dir}/{filename[:30]}...")

                copy_file = False
                reason = ""

                # NUEVO: Comprobar si el nombre base ya existe en el destino
                if base_filename in remote_base_names:
                    # El archivo ya existe con otra extensión, no copiamos
                    skipped_count += 1
                    continue
                elif filename in remote_files_info:
                    remote_file_size = remote_files_info[filename]
                    if local_file_size != remote_file_size:
                        copy_file = True
                        reason = f"Tamaño difiere (Local: {local_file_size}, Remoto: {remote_file_size})"
                    else:
                        skipped_count += 1
                else:
                    copy_file = True
                    reason = "No existe remotamente"

                if copy_file:
                    try:
                        update_status(f"[{progress_perc}%] Copiando {console_dir}/{filename[:30]}... ({reason})")
                        sftp.put(local_file_path, remote_file_path)
                        copied_count += 1
                        
                        # Si la consola requiere extracción, extraer el archivo
                        if needs_extraction and (filename.lower().endswith('.zip') or filename.lower().endswith('.7z')):
                            if extract_zip_on_remote(remote_file_path, remote_console_path):
                                extracted_count += 1
                                
                    except (paramiko.SFTPError, IOError, OSError) as e:
                        error_msg = f"Error copiando {filename} a {remote_console_path}: {e}"
                        errors_list.append(error_msg)
                        update_status(f"Error al copiar {filename[:40]}...")
                        error_count += 1

        # Fin del bucle de consolas
        update_status("Proceso de copia finalizado.")

    except paramiko.AuthenticationException:
        error_msg = f"Error de autenticación para {user}@{ip}. Verifica usuario/contraseña."
        errors_list.append(error_msg)
        update_status("Error: Autenticación fallida.")
        show_final_message("Error de Autenticación", error_msg, icon='error')
        error_count += 1
    except paramiko.SSHException as e:
        error_msg = f"Error de conexión SSH a {ip}: {e}"
        errors_list.append(error_msg)
        update_status(f"Error SSH: {e}")
        show_final_message("Error SSH", error_msg, icon='error')
        error_count += 1
    except TimeoutError: # Puede venir de socket.timeout dentro de paramiko
         error_msg = f"Timeout al conectar o transferir a {ip}."
         errors_list.append(error_msg)
         update_status("Error: Timeout en la conexión.")
         show_final_message("Error de Timeout", error_msg, icon='error')
         error_count += 1
    except Exception as e:
        error_msg = f"Error inesperado durante la copia SCP: {type(e).__name__}: {e}"
        errors_list.append(error_msg)
        update_status(f"Error inesperado: {e}")
        show_final_message("Error Inesperado", error_msg, icon='error')
        error_count += 1
    finally:
        # Asegurarse de cerrar conexiones
        if sftp:
            try: sftp.close()
            except Exception: pass
        if ssh:
            try: ssh.close()
            except Exception: pass

        # Mostrar resumen final
        summary_message = f"Copia a RetroPie finalizada.\n\n" \
                          f"Copiados/Sobrescritos: {copied_count}\n" \
                          f"Extraídos: {extracted_count}\n" \
                          f"Omitidos (ya existen): {skipped_count}\n" \
                          f"Errores: {error_count}"

        if errors_list:
            summary_message += "\n\nErrores encontrados:"
            # Mostrar solo los primeros N errores en el messagebox
            for i, err in enumerate(errors_list[:5]):
                summary_message += f"\n- {err[:150]}" # Acortar errores largos
            if len(errors_list) > 5:
                summary_message += f"\n- ... ({len(errors_list) - 5} más, ver consola)"
            # Imprimir todos los errores en consola
            print("\n--- Errores detallados de la copia SCP ---")
            for err in errors_list:
                print(f"- {err}")
            print("-----------------------------------------\n")
            show_final_message("Copia Finalizada con Errores", summary_message, icon='warning')
        else:
            show_final_message("Copia Finalizada", summary_message, icon='info')

        # Reactivar botones en la GUI (siempre desde el hilo principal)
        def reactivate_buttons():
            scp_button.config(state=tk.NORMAL)
            download_button.config(state=tk.NORMAL if results_list else tk.DISABLED) # Estado según si hay resultados
            search_button.config(state=tk.NORMAL)
            # Restaurar estado inicial si no hay errores graves
            if error_count == 0 and copied_count == 0 and skipped_count == 0 and not errors_list:
                 status_label.config(text="Selecciona carpeta base, consolas y pulsa 'Buscar'.")
            elif error_count > 0 :
                 status_label.config(text=f"Copia finalizada con {error_count} errores.")
            else:
                 final_success_msg = f"Copia a RetroPie completada. Copiados: {copied_count}, Extraídos: {extracted_count}, Omitidos: {skipped_count}."
                 final_success_msg += "\n\nRecuerda reiniciar EmulationStation (Start > Quit > Restart EmulationStation) para ver los nuevos juegos."
                 final_success_msg += "\nPuedes buscar carátulas desde el menú (Start > Scraper)."
                 status_label.config(text=final_success_msg)


        app.after(0, reactivate_buttons)

# --- FIN NUEVAS FUNCIONES ---


# --- Creación de la GUI ---
# (El código de creación de Widgets y layout es el mismo que en la respuesta anterior,
#  solo se ajusta el título y quizás el tamaño inicial si se desea)

app = tk.Tk()
app.title("Descargador Multi-Consola v2.1 (Fuentes Myrient)")
app.geometry("950x750") # Un poco más ancho para la lista de consolas

# --- Estilo y Fuente ---
style = ttk.Style(app)
try:
    # Intentar aplicar tema (ej. 'clam', 'alt', etc.)
    themes = style.theme_names()
    preferred_themes = ['clam', 'alt', 'default', 'vista', 'xpnative']
    for t in preferred_themes:
        if t in themes:
            style.theme_use(t)
            break
except Exception:
    print("No se pudo aplicar tema ttk.")

# ++ Definir estilos para resaltado (más robusto que config(background=...)) ++
# Se definen aquí para que estén disponibles globalmente
try:
    style.configure(f"Highlight.{COLOR_DECRYPTED_SPAIN}.TCheckbutton", background=COLOR_DECRYPTED_SPAIN)
    style.map(f"Highlight.{COLOR_DECRYPTED_SPAIN}.TCheckbutton",
              background=[('active', COLOR_DECRYPTED_SPAIN), ('selected', COLOR_DECRYPTED_SPAIN)]) # Mantener color al interactuar

    style.configure(f"Highlight.{COLOR_DECRYPTED_EUROPE_ES}.TCheckbutton", background=COLOR_DECRYPTED_EUROPE_ES)
    style.map(f"Highlight.{COLOR_DECRYPTED_EUROPE_ES}.TCheckbutton",
              background=[('active', COLOR_DECRYPTED_EUROPE_ES), ('selected', COLOR_DECRYPTED_EUROPE_ES)])

    # ++ NUEVO ESTILO para Decrypted Europe Genérico ++
    style.configure(f"Highlight.{COLOR_DECRYPTED_EUROPE_GENERIC}.TCheckbutton", background=COLOR_DECRYPTED_EUROPE_GENERIC)
    style.map(f"Highlight.{COLOR_DECRYPTED_EUROPE_GENERIC}.TCheckbutton",
              background=[('active', COLOR_DECRYPTED_EUROPE_GENERIC), ('selected', COLOR_DECRYPTED_EUROPE_GENERIC)])
    # ++ FIN NUEVO ESTILO ++

    style.configure(f"Highlight.{COLOR_ENCRYPTED_SPAIN}.TCheckbutton", background=COLOR_ENCRYPTED_SPAIN)
    style.map(f"Highlight.{COLOR_ENCRYPTED_SPAIN}.TCheckbutton",
              background=[('active', COLOR_ENCRYPTED_SPAIN), ('selected', COLOR_ENCRYPTED_SPAIN)])
except Exception as e_style:
    print(f"Advertencia: No se pudieron definir estilos de resaltado ttk: {e_style}")
    print("El resaltado de ROMs podría no funcionar correctamente con el tema actual.")

try:
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(size=10)
    app.option_add("*Font", default_font)
    small_font = default_font.copy()
    small_font.configure(size=9)
    # Aplicar fuente pequeña a los checkbuttons de la lista de consolas
    style.configure("Mini.TCheckbutton", font=small_font, padding=(2,1)) # Añadir padding
    # Aplicar fuente estándar a los checkbuttons de resultados
    style.configure("TCheckbutton", font=default_font, padding=(5,1))
except Exception as e:
    print(f"No se pudo configurar la fuente por defecto: {e}")


# --- Widgets ---

# Frame Superior: Carpeta y Búsqueda
top_frame = ttk.Frame(app, padding="10")
top_frame.pack(fill='x', side='top')

folder_button = ttk.Button(top_frame, text="Carpeta ROM...", command=select_download_folder) # Cambiado el texto aquí
folder_button.pack(side='left', padx=(0, 10))

folder_label = ttk.Label(top_frame, text=f"Descargar en: {selected_base_folder}", relief="sunken", padding=3, anchor='w')
folder_label.pack(side='left', fill='x', expand=True, padx=(0,10))

# Etiqueta para Keyword un poco separada
kw_label = ttk.Label(top_frame, text=" Palabra Clave:")
kw_label.pack(side='left', padx=(10, 5))

keyword_entry = ttk.Entry(top_frame, width=30)
keyword_entry.pack(side='left', padx=(0, 10))
keyword_entry.bind("<Return>", lambda event=None: search_button.invoke())
keyword_entry.focus() # Foco inicial aquí

search_button = ttk.Button(top_frame, text="Buscar Juegos", command=search_roms)
search_button.pack(side='left')
search_button.bind("<Return>", lambda event=None: search_button.invoke())

# --- Frame Central: Selección Consolas y Resultados ---
center_frame = ttk.Frame(app, padding=(5,0,5,5))
center_frame.pack(fill='both', expand=True, side='top')

# Frame Izquierdo: Selección de Consolas (con Scrollbar si es necesario)
console_select_outer_frame = ttk.LabelFrame(center_frame, text="Consolas a Buscar", padding=5)
console_select_outer_frame.pack(side='left', fill='y', padx=(5,5), pady=(0,5))

console_canvas = tk.Canvas(console_select_outer_frame, borderwidth=0, highlightthickness=0)
console_scrollbar = ttk.Scrollbar(console_select_outer_frame, orient="vertical", command=console_canvas.yview)
console_canvas.configure(yscrollcommand=console_scrollbar.set)
# Frame interior para los checkboxes de consola
console_frame = tk.Frame(console_canvas)

console_scrollbar.pack(side="right", fill="y")
console_canvas.pack(side="left", fill="both", expand=True)
console_canvas_window = console_canvas.create_window((0, 0), window=console_frame, anchor="nw")

console_vars = {}
for name in sorted(CONSOLE_SOURCES.keys()):
    var = tk.BooleanVar()
    cb = ttk.Checkbutton(console_frame, text=name, variable=var, style="Mini.TCheckbutton")
    cb.pack(anchor='w', pady=0, padx=2, fill='x') # Rellenar horizontalmente
    console_vars[name] = var

# Bindings para scroll en la lista de consolas
console_canvas.bind("<MouseWheel>", lambda e: _on_mousewheel(e, console_canvas))
console_frame.bind("<MouseWheel>", lambda e: _on_mousewheel(e, console_canvas))
console_canvas.bind("<Button-4>", lambda e: _on_mousewheel(e, console_canvas)) # Linux scroll up
console_canvas.bind("<Button-5>", lambda e: _on_mousewheel(e, console_canvas)) # Linux scroll down
console_frame.bind("<Button-4>", lambda e: _on_mousewheel(e, console_canvas)) # Linux scroll up
console_frame.bind("<Button-5>", lambda e: _on_mousewheel(e, console_canvas)) # Linux scroll down

# Función para ajustar el scroll de la lista de consolas
def _on_console_frame_configure(event=None):
    console_canvas.itemconfig(console_canvas_window, width=console_canvas.winfo_width())
    console_canvas.configure(scrollregion=console_canvas.bbox("all"))

console_frame.bind("<Configure>", _on_console_frame_configure)
console_canvas.bind("<Configure>", _on_console_frame_configure)


# Frame Derecho: Resultados con Scrollbar
results_outer_frame = ttk.LabelFrame(center_frame, text="Resultados", padding=(10, 5, 10, 5))
results_outer_frame.pack(side='left', fill='both', expand=True, padx=(5, 5), pady=(0,5))

canvas = tk.Canvas(results_outer_frame, borderwidth=0, highlightthickness=0)
results_frame = tk.Frame(canvas)
scrollbar = ttk.Scrollbar(results_outer_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True)
canvas_window = canvas.create_window((0, 0), window=results_frame, anchor="nw")

# Bindings scroll resultados
canvas.bind("<MouseWheel>", lambda e: _on_mousewheel(e, canvas))
results_frame.bind("<MouseWheel>", lambda e: _on_mousewheel(e, canvas))
canvas.bind("<Button-4>", lambda e: _on_mousewheel(e, canvas)) # Linux scroll up
canvas.bind("<Button-5>", lambda e: _on_mousewheel(e, canvas)) # Linux scroll down
results_frame.bind("<Button-4>", lambda e: _on_mousewheel(e, canvas)) # Linux scroll up
results_frame.bind("<Button-5>", lambda e: _on_mousewheel(e, canvas)) # Linux scroll down

results_list = []
results_vars = []


# --- Frame inferior para descarga, COPIA SCP y estado --- # <--- Modificar comentario
bottom_frame = ttk.Frame(app, padding=(10, 5))
bottom_frame.pack(fill='x', side='bottom')

# ++ NUEVO BOTÓN SCP ++
scp_button = ttk.Button(bottom_frame, text="Copiar a RetroPie", command=start_scp_copy_thread)
scp_button.pack(side='right', padx=(10, 0))
# --------------------

download_button = ttk.Button(bottom_frame, text="Descargar Seleccionados", command=start_download, state=tk.DISABLED)
# Ajustar posición del botón de descarga si se añade el de SCP a la derecha
# download_button.pack(side='right', padx=(10,0))
download_button.pack(side='right', padx=(5, 0)) # Menos padding si hay otro botón
download_button.bind("<Return>", lambda event=None: download_button.invoke())

progress_bar = ttk.Progressbar(bottom_frame, orient='horizontal', length=250, mode='determinate') # Quizás un poco más corto
progress_bar.pack(side='left', fill='x', expand=True, padx=(0,5))


# Etiqueta de estado
status_label = ttk.Label(app, text="Selecciona carpeta base, consolas y pulsa 'Buscar'.", padding=(10, 5), anchor='w', relief="sunken", wraplength=app.winfo_screenwidth()-40)
status_label.pack(side='bottom', fill='x')

# --- Iniciar la aplicación ---
folder_label.config(text=f"Descargar en: {selected_base_folder}")
# Ajustar tamaño inicial de la lista de consolas
app.update_idletasks()
_on_console_frame_configure()

app.mainloop()
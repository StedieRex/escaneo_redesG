import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import time
import os
import glob
import shutil
from datetime import datetime

class NetworkScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Escáner de Red Inalámbrica")
        self.root.geometry("650x750")
        
        self.interface = tk.StringVar(value="wlan0")
        self.duration = tk.IntVar(value=120)
        self.target_mtr = tk.StringVar(value="8.8.8.8")
        
        self.use_kismet = tk.BooleanVar(value=True)
        self.use_netdiscover = tk.BooleanVar(value=True)
        self.use_ipcalc = tk.BooleanVar(value=True)
        self.use_wavemon = tk.BooleanVar(value=True)
        self.use_mtr = tk.BooleanVar(value=True)
        
        self.report_prefix = "reporte_red"
        self.output_name = "kismet_captura"
        self.destino = "Historial"
        
        self.current_scan_folder = "" 
        self.continue_event = threading.Event()
        
        self._build_gui()

    def _build_gui(self):
        config_frame = ttk.LabelFrame(self.root, text="Configuración del Escaneo")
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="Interfaz:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(config_frame, textvariable=self.interface, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(config_frame, text="Duración (seg):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        ttk.Entry(config_frame, textvariable=self.duration, width=10).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Label(config_frame, text="Objetivo MTR:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(config_frame, textvariable=self.target_mtr, width=15).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tools_frame = ttk.LabelFrame(self.root, text="Herramientas a Utilizar")
        tools_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Checkbutton(tools_frame, text="Kismet (Modo Monitor)", variable=self.use_kismet).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ttk.Checkbutton(tools_frame, text="Netdiscover", variable=self.use_netdiscover).grid(row=0, column=1, padx=10, pady=5, sticky="w")
        ttk.Checkbutton(tools_frame, text="Ipcalc", variable=self.use_ipcalc).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ttk.Checkbutton(tools_frame, text="Wavemon (iw)", variable=self.use_wavemon).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        ttk.Checkbutton(tools_frame, text="MTR", variable=self.use_mtr).grid(row=2, column=0, padx=10, pady=5, sticky="w")

        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="Iniciar Escaneo", command=self.start_scan)
        self.start_btn.pack(side="left", padx=5)
        
        self.continue_btn = ttk.Button(control_frame, text="Continuar (Red Restaurada)", command=self.resume_scan, state="disabled")
        self.continue_btn.pack(side="left", padx=5)

        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.time_label = ttk.Label(status_frame, text="Tiempo Restante: 00:00", font=("Helvetica", 12, "bold"))
        self.time_label.pack(side="left")
        
        self.progress = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate")
        self.progress.pack(side="right", fill="x", expand=True, padx=(10, 0))

        self.log_area = scrolledtext.ScrolledText(self.root, height=20, state='disabled', bg="black", fg="lightgreen", font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def start_scan(self):
        self.start_btn.config(state="disabled")
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        self.current_scan_folder = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log(f"[*] ID de Escaneo Generado: {self.current_scan_folder}")
        
        scan_config = {
            'interf': self.interface.get(),
            'dur': self.duration.get(),
            'target': self.target_mtr.get(),
            'use_kismet': self.use_kismet.get(),
            'use_netdiscover': self.use_netdiscover.get(),
            'use_ipcalc': self.use_ipcalc.get(),
            'use_wavemon': self.use_wavemon.get(),
            'use_mtr': self.use_mtr.get()
        }
        
        threading.Thread(target=self._scan_process, kwargs=scan_config, daemon=True).start()

    def resume_scan(self):
        self.continue_btn.config(state="disabled")
        self.continue_event.set()

    def _run_with_timer(self, tool_name, command_list, duration, output_file=None):
        self.log(f"[*] Iniciando {tool_name} por {duration} segundos...")
        self.root.after(0, lambda: self.progress.config(maximum=duration, value=0))
        
        out_f = open(output_file, "w") if output_file else subprocess.DEVNULL
        try:
            full_cmd = ["sudo", "timeout", f"{duration}s"] + command_list
            process = subprocess.Popen(full_cmd, stdout=out_f, stderr=subprocess.STDOUT)
            for i in range(duration):
                if process.poll() is not None: break
                mins, secs = divmod(duration - i, 60)
                time_str = f"Tiempo Restante: {mins:02d}:{secs:02d}"
                self.root.after(0, lambda t=time_str, v=i+1: self._update_timer(t, v))
                time.sleep(1)
            process.wait()
        except Exception as e:
            self.log(f"[!] Error en {tool_name}: {e}")
        finally:
            if output_file: out_f.close()
            self.root.after(0, lambda: self._update_timer("Tiempo Restante: 00:00", duration))
            self.log(f"[+] {tool_name} finalizado.")

    def _update_timer(self, text, value):
        self.time_label.config(text=text)
        self.progress['value'] = value

    def _scan_process(self, interf, dur, target, use_kismet, use_netdiscover, use_ipcalc, use_wavemon, use_mtr):
        
        # --- 1. BLOQUE KISMET (CON ESPERA DE 20S) ---
        if use_kismet:
            kismet_done = False
            while not kismet_done:
            	# --- Eliminacion de .kismet residuales en caso de que la interfaz no entre en modo escaneo ---
                self.log("[*] Limpiando archivos .kismet residuales...")
                for f_old in glob.glob("*.kismet"):
                    try:
                        os.remove(f_old)
                    except:
                        pass
            
                self.log("[*] Iniciando Kismet. Esperando 20 segundos de estabilización...")
                subprocess.run(["sudo", "pkill", "-f", "kismet"], stderr=subprocess.DEVNULL)
                time.sleep(2)
                
                full_cmd = ["sudo", "kismet", "-c", interf, "--no-ncurses-wrapper"]
                process = subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                
                time.sleep(20) # Pausa de 20 segundos según tu requerimiento
                
                self.root.answer = None
                self.root.after(0, lambda: setattr(self.root, 'answer', messagebox.askyesno("Verificación", "¿Ha entrado al modo escaneo de kismet de forma correcta?")))
                while self.root.answer is None: time.sleep(0.5)
                
                if self.root.answer:
                    self.log("[+] Conexión confirmada. Ejecutando escaneo principal...")
                    self.root.after(0, lambda: self.progress.config(maximum=dur, value=0))
                    for i in range(dur):
                        if process.poll() is not None: break
                        mins, secs = divmod(dur - i, 60)
                        self.root.after(0, lambda t=f"Tiempo: {mins:02d}:{secs:02d}", v=i+1: self._update_timer(t, v))
                        time.sleep(1)
                    
                    subprocess.run(["sudo", "pkill", "-f", "kismet"], stderr=subprocess.DEVNULL)
                    process.wait()
                    kismet_done = True
                else:
                    self.log("[!] No se puedo inciar el modo escaneo. Reiniciando Kismet...")
                    subprocess.run(["sudo", "pkill", "-f", "kismet"], stderr=subprocess.DEVNULL)
                    process.wait()

            # Conversión de archivos Kismet
            kismet_files = glob.glob("*.kismet")
            if kismet_files:
                db_file = sorted(kismet_files, key=os.path.getmtime)[-1]
                self.log(f"[*] Generando JSON desde {db_file}...")
                subprocess.run(["sudo", "kismetdb_dump_devices", "--in", db_file, "--out", f"{self.output_name}.json", "--force"])
            
            # Restauración de Red Obligatoria
            self.log("[*] Restaurando servicios de red...")
            comandos = [
            	["sudo", "airmon-ng", "stop", f"{interf}mon"], 
            	["sudo", "airmon-ng", "stop", interf],
            	["sudo", "systemctl", "start", "NetworkManager"], 
            	["sudo", "ip", "link", "set", interf, "up"],
            	["sudo", "systemctl", "restart", "NetworkManager"],
            	["nmcli", "radio", "wifi", "on"],
            	["sudo", "airmon-ng", "start", interf],
            	["sudo", "airmon-ng", "stop", interf],
            	["sudo", "airmon-ng", "stop", f"{interf}mon"]
            ]
            for cmd in comandos:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.log("-" * 50)
            self.log("[!] KISMET FINALIZADO. Conéctate al Wi-Fi y pulsa 'Continuar'.")
            self.log("-" * 50)
            self.root.after(0, lambda: self.continue_btn.config(state="normal"))
            self.continue_event.clear()
            self.continue_event.wait()
        else:
            self.log("[!] BLOQUE KISMET OMITIDO.")

        # --- 2. BLOQUE DE HERRAMIENTAS ACTIVAS ---
        if use_netdiscover:
            self._run_with_timer("Netdiscover", ["netdiscover", "-P", "-N"], dur, f"{self.report_prefix}_netdiscover.txt")

        if use_ipcalc:
            self.log("[*] Ejecutando Ipcalc...")
            ip_cidr = subprocess.getoutput(f"ip -4 addr show {interf} | grep inet | awk '{{print $2}}'").strip()
            with open(f"{self.report_prefix}_ipcalc.txt", "w") as f:
                if shutil.which("ipcalc") and ip_cidr: subprocess.run(["ipcalc", ip_cidr], stdout=f)
            self.log("[+] Ipcalc finalizado.")

        if use_wavemon:
            self.log("[*] Capturando enlace Wi-Fi...")
            with open(f"{self.report_prefix}_wavemon.txt", "w") as f:
                subprocess.run(["iw", "dev", interf, "link"], stdout=f)

        if use_mtr:
            self.log("[*] Ejecutando MTR...")
            gateway = subprocess.getoutput("ip route | grep default | awk '{print $3}'").strip()
            if gateway:
                with open(f"{self.report_prefix}_mtr.txt", "w") as f:
                    subprocess.run(["mtr", "-rw", gateway, "--report-cycles", "10"], stdout=f)

        # --- 3. BLOQUE DE REPORTE FINAL (SIEMPRE SE EJECUTA) ---
        self.log("-" * 50)
        self.log("[*] Generando reporte Excel con conversor_v3.py...")
        if os.path.exists("conversor_v3.py"):
            cmd_conv = ["python3", "conversor_v3.py"]
            if not use_kismet: cmd_conv.append("-s") # Bandera para omitir Kismet en el excel
            try:
                res = subprocess.run(cmd_conv, capture_output=True, text=True)
                for line in res.stdout.splitlines(): self.log(f"  [Excel] {line}")
            except Exception as e: self.log(f"[!] Error en conversor: {e}")

        # Movimiento de archivos al Historial
        dest_path = os.path.join(self.destino, self.current_scan_folder)
        if not os.path.exists(dest_path): os.makedirs(dest_path)
        
        files_to_move = []
        for ext in ("*.txt", "*.kismet", "*.json", "*.xlsx"):
            files_to_move.extend(glob.glob(ext))
        
        for f in files_to_move:
            try:
                shutil.move(f, os.path.join(dest_path, os.path.basename(f)))
                self.log(f"  -> Archivo guardado: {os.path.basename(f)}")
            except: pass

        self.log(f"[+++] PROCESO COMPLETADO. Carpeta: {self.current_scan_folder}")
        self.root.after(0, lambda: self.start_btn.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkScannerApp(root)
    root.mainloop()

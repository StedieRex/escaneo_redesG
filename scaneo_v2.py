import tkinter as tk
from tkinter import ttk, scrolledtext
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
        
        # --- SOLUCIÓN AL BUG ---
        # Leemos el estado de todas las variables gráficas AHORA (en el hilo principal)
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
        
        # Le pasamos las variables ya leídas al hilo secundario usando 'kwargs'
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
                if process.poll() is not None:
                    break
                mins, secs = divmod(duration - i, 60)
                time_str = f"Tiempo Restante: {mins:02d}:{secs:02d}"
                self.root.after(0, lambda t=time_str, v=i+1: self._update_timer(t, v))
                time.sleep(1)
                
            process.wait()
            
        except Exception as e:
            self.log(f"[!] Error ejecutando {tool_name}: {e}")
        finally:
            if output_file:
                out_f.close()
            self.root.after(0, lambda: self._update_timer("Tiempo Restante: 00:00", duration))
            self.log(f"[+] {tool_name} finalizado.")

    def _update_timer(self, text, value):
        self.time_label.config(text=text)
        self.progress['value'] = value

    # --- MODIFICADO: Recibe los parámetros en lugar de hacer '.get()' ---
    def _scan_process(self, interf, dur, target, use_kismet, use_netdiscover, use_ipcalc, use_wavemon, use_mtr):
        
        if use_kismet:
            #Este cierre y apertura de kismet, se hace pues soluciona un bug, que inpide a kismet arrancar
            #despues de haber deseleccionado de las herramientas, y vuelto a usar despues de hacer un escaneo
            #sin kismet.
            subprocess.run(["sudo", "pkill", "-f", "kismet"], stderr=subprocess.DEVNULL)
            time.sleep(2)
        
            self._run_with_timer("Kismet", ["kismet", "-c", interf, "--no-ncurses-wrapper"], dur)
            
            self.log("[*] Finalizando procesos remanentes de Kismet...")
            subprocess.run(["sudo", "pkill", "-f", "kismet"], stderr=subprocess.DEVNULL)
            time.sleep(2)
            
            kismet_files = glob.glob("*.kismet")
            if kismet_files:
                db_file = kismet_files[0]
                self.log(f"[*] Convirtiendo {db_file} a JSON...")
                subprocess.run(["sudo", "kismetdb_dump_devices", "--in", db_file, "--out", f"{self.output_name}.json", "--force"])
                self.log("[!] Archivo JSON generado con éxito.")
            else:
                self.log("[!] Error: No se encontró el archivo de base de datos de Kismet.")
            
            self.log("[*] Restaurando interfaz y servicios de red...")
            commands = [
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
            for cmd in commands:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            self.log("-" * 50)
            self.log("[!] ESCANEO PASIVO FINALIZADO.")
            self.log("[!] Por favor, conéctate a tu red Wi-Fi.")
            self.log("[!] Presiona 'Continuar (Red Restaurada)' cuando tengas conexión.")
            self.log("-" * 50)
            
            self.root.after(0, lambda: self.continue_btn.config(state="normal"))
            self.continue_event.clear()
            self.continue_event.wait() 
            self.log("[+] Iniciando herramientas de diagnóstico de red...")
        else:
            self.log("-" * 50)
            self.log("[!] SE SALTÓ EL ESCANEO DE KISMET.")
            self.log("-" * 50)

        if use_netdiscover:
            self._run_with_timer("Netdiscover", ["netdiscover", "-P", "-S", "-N"], dur, f"{self.report_prefix}_netdiscover.txt")

        if use_ipcalc:
            self.log("[*] Ejecutando Ipcalc...")
            ip_cmd = f"ip -4 addr show {interf} | grep inet | awk '{{print $2}}'"
            ip_cidr = subprocess.getoutput(ip_cmd).strip()
            
            with open(f"{self.report_prefix}_ipcalc.txt", "w") as f:
                if shutil.which("ipcalc"):
                    subprocess.run(["ipcalc", ip_cidr], stdout=f)
                else:
                    f.write(f"IP/Subnet: {ip_cidr}\n")
            self.log("[+] Ipcalc completado.")

        if use_wavemon:
            self.log("[*] Capturando estado del enlace con iw...")
            with open(f"{self.report_prefix}_wavemon.txt", "w") as f:
                subprocess.run(["iw", "dev", interf, "link"], stdout=f)
            self.log("[+] Estado capturado.")

        if use_mtr:
            self.log("[*] Ejecutando MTR...")
            gw_cmd = "ip route | grep default | awk '{print $3}'"
            gateway = subprocess.getoutput(gw_cmd).strip()
            
            if gateway:
                with open(f"{self.report_prefix}_mtr.txt", "w") as f:
                    subprocess.run(["mtr", "-rw", gateway, "--report-cycles", "10"], stdout=f)
                self.log("[+] MTR finalizado.")
            else:
                self.log("[!] No se detectó puerta de enlace para MTR.")

        self.log("-" * 50)
        self.log("[*] Ejecutando conversor_v3.py para procesar Excel...")
        
        if os.path.exists("conversor_v3.py"):
            cmd_conversor = ["python3", "conversor_v3.py"]
            if not use_kismet:
                cmd_conversor.append("-s")
                self.log("  -> (Pasando bandera -s para omitir Kismet en el reporte)")
                
            try:
                resultado = subprocess.run(cmd_conversor, capture_output=True, text=True)
                for linea in resultado.stdout.splitlines():
                    self.log(f"  [conversor] {linea}")
            except Exception as e:
                self.log(f"[!] Error al ejecutar conversor_v3.py: {e}")
        else:
            self.log("[!] Advertencia: conversor_v3.py no encontrado en el directorio.")

        ruta_directorio_final = os.path.join(self.destino, self.current_scan_folder)
        self.log(f"[*] Moviendo archivos a: {ruta_directorio_final}")
        
        if not os.path.exists(ruta_directorio_final):
            os.makedirs(ruta_directorio_final)

        extensions = ("*.txt", "*.kismet", "*.json", "*.xlsx")
        archivos_movidos = 0
        for ext in extensions:
            for archivo in glob.glob(ext):
                shutil.move(archivo, os.path.join(ruta_directorio_final, os.path.basename(archivo)))
                self.log(f"  -> Movido: {archivo}")
                archivos_movidos += 1
                
        self.log(f"[+] Total de archivos movidos: {archivos_movidos}")
        self.log("[!!!] ESCANEO GLOBAL COMPLETADO.")
        self.root.after(0, lambda: self.start_btn.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkScannerApp(root)
    root.mainloop()

import json
import pandas as pd
import re
import argparse
import os

# --- Configuración de Banderas ---
parser = argparse.ArgumentParser(description="Procesador de reportes de red adaptable")
parser.add_argument('-s', '--skip-kismet', action='store_true', help="Fuerza saltar Kismet aunque el archivo exista")
args = parser.parse_args()

# Inicializamos los DataFrames por separado para evitar referencias compartidas en memoria
df_aps = pd.DataFrame()
df_clients = pd.DataFrame()
df_mtr = pd.DataFrame()
df_wavemon = pd.DataFrame()
df_netdiscover = pd.DataFrame()
df_ipcalc = pd.DataFrame()

# --- 1. KISMET JSON ---
if not args.skip_kismet and os.path.exists('kismet_captura.json'):
    try:
        with open('kismet_captura.json', 'r') as f:
            kismet_data = json.load(f)
        
        aps, clients = [], []
        def get_band(freq_khz):
            freq = int(freq_khz or 0) / 1000
            if 2400 <= freq <= 2500: return "2.4 GHz"
            if 5000 <= freq <= 6000: return "5 GHz"
            if 6000 <= freq <= 7125: return "6 GHz"
            return "Otra"

        for device in kismet_data:
            device_type = device.get('kismet.device.base.type', '')
            mac = device.get('kismet.device.base.macaddr', '')
            signal_dbm = device.get('kismet.device.base.signal', {}).get('kismet.common.signal.last_signal_dbm', 'N/A')
            
            if 'Wi-Fi AP' in device_type:
                aps.append({
                    'SSID': device.get('kismet.device.base.commonname', '<Oculto>'),
                    'BSSID': mac,
                    'Canal': device.get('kismet.device.base.channel', 'N/A'),
                    'Banda': get_band(device.get('kismet.device.base.frequency', 0)),
                    'RSSI': signal_dbm
                })
            elif 'Wi-Fi Client' in device_type:
                clients.append({
                    'MAC Cliente': mac,
                    'AP Asociado': device.get('dot11.device', {}).get('dot11.device.last_bssid', 'None'),
                    'RSSI': signal_dbm
                })
        
        df_aps = pd.DataFrame(aps)
        df_clients = pd.DataFrame(clients)
        print("✅ Kismet procesado.")
    except Exception as e:
        print(f"❌ Error procesando Kismet: {e}")
else:
    print("⏭️ Kismet omitido (archivo no encontrado o bandera -s activa).")

# --- 2. MTR ---
if os.path.exists('reporte_red_mtr.txt'):
    mtr_rows = []
    with open('reporte_red_mtr.txt', 'r') as f:
        for line in f:
            match = re.search(r'^\s*(\d+)\.\|--\s+([^\s]+)\s+([\d.%]+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', line)
            if match: mtr_rows.append(match.groups())
    df_mtr = pd.DataFrame(mtr_rows, columns=['Hop', 'Host', 'Loss%', 'Snt', 'Last', 'Avg', 'Best', 'Wrst', 'StDev'])
    print("✅ MTR procesado.")

# --- 3. WAVEMON (iw) ---
if os.path.exists('reporte_red_wavemon.txt'):
    wavemon_data = []
    with open('reporte_red_wavemon.txt', 'r') as f:
        for line in f:
            if ':' in line.strip():
                key, val = line.strip().split(':', 1)
                wavemon_data.append({'Parametro': key.strip(), 'Valor': val.strip()})
    df_wavemon = pd.DataFrame(wavemon_data)
    print("✅ Wavemon (iw link) procesado.")

# --- 4. NETDISCOVER ---
if os.path.exists('reporte_red_netdiscover.txt'):
    net_rows = []
    with open('reporte_red_netdiscover.txt', 'r') as f:
        for line in f:
            parts = line.split()
            # Validamos que empiece con IP y manejamos si el Vendor viene vacío
            if len(parts) >= 4 and re.match(r'\d+\.\d+\.\d+\.\d+', parts[0]):
                vendor = " ".join(parts[4:]) if len(parts) >= 5 else "Unknown"
                net_rows.append([parts[0], parts[1], parts[2], parts[3], vendor])
    df_netdiscover = pd.DataFrame(net_rows, columns=['IP Address', 'MAC Address', 'Count', 'Len', 'Vendor'])
    print("✅ Netdiscover procesado.")

# --- 5. IPCALC ---
if os.path.exists('reporte_red_ipcalc.txt'):
    ipcalc_rows = []
    with open('reporte_red_ipcalc.txt', 'r') as f:
        for line in f:
            if ':' in line:
                parts = line.split(':', 1)
                propiedad = parts[0].strip()
                # Corta usando expresiones regulares si hay 2 o más espacios consecutivos
                valor_limpio = re.split(r'\s{2,}', parts[1].strip())[0]
                ipcalc_rows.append({'Propiedad': propiedad, 'Valor': valor_limpio})
    df_ipcalc = pd.DataFrame(ipcalc_rows)
    print("✅ Ipcalc procesado.")

# --- GUARDAR EXCEL (Solo pestañas con datos) ---
dataframes = [df_aps, df_clients, df_mtr, df_wavemon, df_netdiscover, df_ipcalc]

if any(not d.empty for d in dataframes):
    with pd.ExcelWriter('reporte_red_completo.xlsx') as writer:
        if not df_aps.empty: df_aps.to_excel(writer, sheet_name='Redes Inalambricas', index=False)
        if not df_clients.empty: df_clients.to_excel(writer, sheet_name='Clientes Wi-Fi', index=False)
        if not df_mtr.empty: df_mtr.to_excel(writer, sheet_name='MTR', index=False)
        if not df_wavemon.empty: df_wavemon.to_excel(writer, sheet_name='Wavemon', index=False)
        if not df_netdiscover.empty: df_netdiscover.to_excel(writer, sheet_name='Netdiscover', index=False)
        if not df_ipcalc.empty: df_ipcalc.to_excel(writer, sheet_name='Ipcalc', index=False)
    print("\n🚀 ¡Éxito! Reporte generado con los archivos disponibles.")
else:
    print("\n⚠️ No se encontró ningún archivo válido para procesar. No se generó el Excel.")

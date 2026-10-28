import os
import datetime
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__, template_folder='.', static_folder='.')

# --- CONFIGURACIÓN DE SEGURIDAD ---
USUARIO_FIJO = "demo"
CLAVE_FIJA = "Lab2026!"
BLOQUEO_ACTIVO = os.environ.get("BLOQUEO", "off").lower() == "on"
BLOQUEO_SEG = int(os.environ.get("BLOQUEO_SEG", 60))
MAX_INTENTOS = 3

# --- ESTADO EN MEMORIA (Sin Base de Datos) ---
intentos_fallidos = 0
bloqueado_hasta = None

@app.route('/login', methods=['GET', 'POST'])
def login():
    global intentos_fallidos, bloqueado_hasta
    
    if request.method == 'GET':
        return render_template('index.html')

    usuario = request.form.get('usuario', '')
    clave = request.form.get('clave', '')
    
    # Obtener IP (X-Real-IP si existe, si no la IP de la petición)
    ip = request.headers.get('X-Real-IP', request.remote_addr)
    fecha = datetime.datetime.now().isoformat()
    
    ahora = datetime.datetime.now().timestamp()
    estado_bloqueo = "Inactivo"
    
    # 1. Verificar si está bloqueado
    if BLOQUEO_ACTIVO and bloqueado_hasta and ahora < bloqueado_hasta:
        estado_bloqueo = "Bloqueado"
        loggear(fecha, usuario, "BLOQUEADO", ip, estado_bloqueo)
        return redirect(url_for('login', error="Cuenta bloqueada temporalmente. Intente más tarde."))

    # 2. Si el bloqueo expiró, reiniciar
    if BLOQUEO_ACTIVO and bloqueado_hasta and ahora >= bloqueado_hasta:
        bloqueado_hasta = None
        intentos_fallidos = 0
        estado_bloqueo = "Inactivo"
        loggear(fecha, "SISTEMA", "FIN_BLOQUEO", ip, estado_bloqueo)

    # 3. Validar credenciales
    if usuario == USUARIO_FIJO and clave == CLAVE_FIJA:
        intentos_fallidos = 0
        loggear(fecha, usuario, "EXITO", ip, "Inactivo")
        return render_template('bienvenida.html')
    else:
        intentos_fallidos += 1
        
        # 4. Bloqueo tras 3 intentos
        if BLOQUEO_ACTIVO and intentos_fallidos >= MAX_INTENTOS:
            bloqueado_hasta = ahora + BLOQUEO_SEG
            estado_bloqueo = "Bloqueado"
            loggear(fecha, usuario, "FALLO", ip, estado_bloqueo)
            loggear(fecha, "SISTEMA", "INICIO_BLOQUEO", ip, estado_bloqueo)
            return redirect(url_for('login', error=f"Cuenta bloqueada por {BLOQUEO_SEG} segundos tras {MAX_INTENTOS} fallos."))
        else:
            loggear(fecha, usuario, "FALLO", ip, "Inactivo")
            return redirect(url_for('login', error=f"Credenciales incorrectas. Intento {intentos_fallidos} de {MAX_INTENTOS}."))

# --- FUNCIÓN DE LOG (NUNCA registra la contraseña) ---
def loggear(fecha, usuario, resultado, ip, estado_bloqueo):
    os.makedirs('logs', exist_ok=True)
    linea = f"[{fecha}] | Usuario: {usuario} | IP: {ip} | Resultado: {resultado} | Bloqueo: {estado_bloqueo}\n"
    with open('logs/auth.log', 'a', encoding='utf-8') as f:
        f.write(linea)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
"""
Punto de entrada principal para el servidor Flask de PersonaAI.
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from app import create_app

# Crear instancia de la aplicación
app = create_app()

import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PersonaAI Flask Server")
    parser.add_argument("--port", type=int, default=3000, help="Puerto del servidor (default: 3000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host del servidor (default: 0.0.0.0)")
    parser.add_argument("--debug", action="store_true", default=False, help="Modo debug")
    args, _ = parser.parse_known_args()

    # Si se pasa --port usarlo; si no, buscar APP_PORT o usar 3000 (ignorando PORT=8080 del contenedor)
    port = args.port or int(os.environ.get("APP_PORT", 3000))
    host = args.host or "0.0.0.0"
    debug = args.debug or os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

    print(f"🚀 Iniciando servidor Flask en http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

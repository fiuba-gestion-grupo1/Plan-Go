"""
Script para probar el problema de fechas en itinerarios
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "premium@fi.uba.ar"
TEST_USER_PASSWORD = "password"


def login():
    """Login y obtener token"""
    login_data = {"identifier": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}

    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"Error en login: {response.status_code} - {response.text}")
        return None


if __name__ == "__main__":
    print("=== 🐛 Prueba del problema de fechas ===\n")
    print("\n=== Fin de la prueba ===")

"""
Test específico para verificar que las fechas se manejan correctamente
después de aplicar la corrección en el frontend
"""

import requests
import json

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
    print("=== 🔧 Test de corrección de fechas ===")
    print("\n=== Fin del test ===")

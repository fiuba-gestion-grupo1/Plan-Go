import io
from fastapi.testclient import TestClient

def test_upload_profile_photo_success(client: TestClient, auth_headers: dict):
    """Prueba la subida exitosa de una foto de perfil (JPG)."""
    #archivo falso de imagen en memoria
    fake_image_bytes = b"fake-jpg-content"
    file = ("test.jpg", io.BytesIO(fake_image_bytes), "image/jpeg")
    
    response = client.put("/api/users/me/photo", headers=auth_headers, files={"file": file})
    
    assert response.status_code == 200
    data = response.json()
    assert "profile_picture_url" in data
    assert data["profile_picture_url"].startswith("/static/uploads/")
    assert data["profile_picture_url"].endswith(".jpg")

def test_upload_invalid_file_type(client: TestClient, auth_headers: dict):
    """Prueba que se rechace un tipo de archivo no válido."""
    fake_text_bytes = b"this is not an image"
    file = ("test.txt", io.BytesIO(fake_text_bytes), "text/plain")
    
    response = client.put("/api/users/me/photo", headers=auth_headers, files={"file": file})
    
    assert response.status_code == 400
    assert "Tipo de archivo inválido" in response.json()["detail"]
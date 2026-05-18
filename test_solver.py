import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from solver import app, save_to_gcs

client = TestClient(app)

# Przykładowe dane z API NBP (żeby nie uderzać do prawdziwego serwera podczas testów)
mock_nbp_data = [
    {
        "table": "A",
        "no": "090/A/NBP/2026",
        "effectiveDate": "2026-05-12",
        "rates": [
            {"currency": "dolar amerykański", "code": "USD", "mid": 4.0},
            {"currency": "euro", "code": "EUR", "mid": 4.3}
        ]
    }
]

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "nbp-pipeline"}

@patch("solver.fetch_nbp_data")
def test_get_formatted_table(mock_fetch):
    mock_fetch.return_value = mock_nbp_data
    response = client.get("/table")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["code"] == "USD"
    assert data[0]["mid"] == 4.0

@patch("solver.save_to_gcs")
@patch("solver.fetch_nbp_data")
def test_get_and_save_data(mock_fetch, mock_save):
    mock_fetch.return_value = mock_nbp_data
    mock_save.return_value = "mocked_file.json"

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["file_saved"] == "mocked_file.json"
    assert len(data["data"]) == 2

@patch("solver.storage.Client")
@patch("solver.BUCKET_NAME", "test_bucket")
def test_save_to_gcs(mock_storage_client):
    mock_client_instance = MagicMock()
    mock_storage_client.return_value = mock_client_instance
    mock_bucket = MagicMock()
    mock_client_instance.get_bucket.return_value = mock_bucket
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    data_to_save = mock_nbp_data[0]

    filename = save_to_gcs(data_to_save)

    assert filename is not None
    assert filename.startswith("rates_")
    assert filename.endswith(".json")

    mock_storage_client.assert_called_once()
    mock_client_instance.get_bucket.assert_called_once_with("test_bucket")
    mock_bucket.blob.assert_called_once_with(filename)
    mock_blob.upload_from_string.assert_called_once()

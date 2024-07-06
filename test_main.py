import unittest

from fastapi.testclient import TestClient
from main import app, URLModel

client = TestClient(app)

def clear_table():
    for url in URLModel.scan():
        url.delete()
def test_create_short_url():
    response = client.post("/shorten_url", json={"url": "https://www.example.com"})
    assert response.status_code == 200
    assert "short_url" in response.json()

def test_create_custom_short_url():
    response = client.post("/shorten_url", json={"url": "https://www.eexample.com", "short_url": "exampleShort"})
    assert response.status_code == 200
    assert response.json()["short_url"] == "exampleShort"

def test_short_url_collision():
    # create a custom short URL
    client.post("/shorten_url", json={"url": "https://www.example.com", "short_url": "exampleShortUrl"})

    # Try to create the same custom short URL again
    response = client.post("/shorten_url", json={"url": "https://www.differentexample.com", "short_url": "exampleShortUrl"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Short URL 'exampleShortUrl' already exists."

def test_invalid_short_url():
    response = client.get("/exampleShortInvalid")
    assert response.status_code == 404

def test_list_urls():
    clear_table()
    # Add a few URLs
    client.post("/shorten_url", json={"url": "https://www.example1.com", "short_url": "exampleShort1"})
    client.post("/shorten_url", json={"url": "https://www.example2.com", "short_url": "exampleShort2"})

    response = client.get("/list_urls")
    assert response.status_code == 200
    urls = response.json()
    assert len(urls) == 2
    assert {"short_url": "exampleShort1", "original_url": "https://www.example1.com"} in urls
    assert {"short_url": "exampleShort2", "original_url": "https://www.example2.com"} in urls
    clear_table()

if __name__ == "__main__":
    unittest.main()
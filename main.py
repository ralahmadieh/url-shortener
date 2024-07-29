import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
import random
import string

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

class URLModel(Model):
    """
   URLModel represents the DynamoDB table for storing URL mappings.
   Attributes:
       short_url (str): The shortened URL (hash key).
       original_url (str): The original URL.
   """
    class Meta:
        table_name = "urls"
        region = "us-west-2"
    short_url = UnicodeAttribute(hash_key=True)
    original_url = UnicodeAttribute()

class URLRequest(BaseModel):
    """
    URLRequest represents the structure of the request for shortening a URL.
    Attributes:
        url (str): The original URL to be shortened.
        short_url (str): An optional custom short URL.
    """
    url: str
    short_url: str = None

def generate_random_short_url(length=6):
    """
    Generates a random short URL of a given length.
    Args:
        length (int): The length of the generated short URL. Default is 6.
    Returns:
        str: A randomly generated short URL.
    """
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for i in range(length))

@app.post("/shorten_url")
async def shorten_url(request: URLRequest):
    """
    Endpoint to shorten a given URL.
    Args:
        request (URLRequest): The request body containing the URL and an optional custom short URL.
    Returns:
        dict: The shortened URL and the original URL.
    """
    logging.debug(f"Received request: {request}")
    if request.short_url:
        try:
            URLModel.get(request.short_url)
            raise HTTPException(status_code=409, detail=f"Short URL '{request.short_url}' already exists.")
        except URLModel.DoesNotExist:
            logging.debug(f"Short URL '{request.short_url}' does not exist, proceeding.")
        short_url = request.short_url
    else:
        while True:
            short_url = generate_random_short_url()
            try:
                URLModel.get(short_url)
            except URLModel.DoesNotExist:
                logging.debug(f"Generated unique short URL: {short_url}")
                break

    url = URLModel(short_url=short_url, original_url=request.url)
    url.save()
    logging.debug(f"Saved URL mapping: {url}")
    return {"short_url": short_url, "original_url": request.url}

@app.get("/get_url/{short_url}")
async def get_url(short_url: str):
    """
    Endpoint to retrieve the original URL for a given short URL.
    Args:
        short_url (str): The short URL.
    Returns:
        dict: The original URL corresponding to the short URL.
    """
    logging.debug(f"Fetching original URL for short URL: {short_url}")
    try:
        url_entry = URLModel.get(short_url)
        return {"short_url": short_url, "original_url": url_entry.original_url}
    except URLModel.DoesNotExist:
        logging.error(f"Short URL '{short_url}' not found.")
        raise HTTPException(status_code=404, detail="Short URL not found")

@app.get("/list_urls")
async def list_urls():
    """
    Endpoint to list all URL mappings.
    Returns:
        list: A list of all URL mappings.
    """
    logging.debug("Listing all URL mappings.")
    try:
        urls = URLModel.scan()
        return [{"short_url": url.short_url, "original_url": url.original_url} for url in urls]
    except Exception as e:
        logging.error(f"Error listing URLs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute
import random
import string

app = FastAPI()

class URLModel(Model):
    #defines the structure of the DynamoDB table
    class Meta:
        table_name = "urls"
        region = "us-west-2"
    #attributes of the table
    short_url = UnicodeAttribute(hash_key=True)
    original_url = UnicodeAttribute()
# defines the expected structure of the request body for URL shortening
class URLRequest(BaseModel):
    url: str
    short_url: str = None

def generate_random_short_url(length=6):
    letters_and_digits = string.ascii_letters + string.digits
    str = ''.join(random.choice(letters_and_digits) for i in range(length))
    return str


@app.post("/shorten_url")
async def shorten_url(request: URLRequest):
    # check if the short URL already exists if provided

    if request.short_url:
        try:
            #attempt to return the URL entry with the provided short URL
            URLModel.get(request.short_url)
            #if it exists, raise an HTTP 404 conflict exception
            raise HTTPException(status_code=409, detail=f"Short URL '{request.short_url}' already exists.")
        except URLModel.DoesNotExist:
            pass
        short_url = request.short_url

    else:
        #generate a random short URL if non is provided
        while True:
            short_url = generate_random_short_url()
            try:
                URLModel.get(short_url)
            except URLModel.DoesNotExist:
                break

    url = URLModel(short_url=short_url, original_url=request.url)
    url.save()
    urls = URLModel.scan()
    return {"short_url": short_url, "original_url": request.url}

#Get endpoint is to retrieve the original URL
@app.get("/get_url/{short_url}")
async def get_url(short_url: str):
    try:
        url_entry = URLModel.get(short_url)
        return {"short_url": short_url, "original_url": url_entry.original_url}
    except URLModel.DoesNotExist:
        raise HTTPException(status_code=404, detail="Short URL not found")

#get endpoint to retrieve all shortened urls and their corresponding original urls
@app.get("/list_urls")
async def list_urls():
    try:
        urls = URLModel.scan()
        return [{"short_url": url.short_url, "original_url": url.original_url} for url in urls]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


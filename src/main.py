import asyncio
import aiohttp
import cv2
import numpy as np
import requests
from sanic import Sanic, response

app = Sanic(__name__)

API_URL = "https://api.slingacademy.com/v1/sample-data/photos"
TOTAL_IMAGES = 132
THUMBNAIL_SIZE = (32, 32)


async def get_image_url_list(limit, offset):
    # Send an HTTP GET request to the API endpoint
    response = requests.get(f"{API_URL}?limit={limit}&offset={offset}")
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        json_data_photos = response.json()["photos"]
        img_list = [d["url"] for d in json_data_photos]
    return img_list


async def fetch_image(session, url):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                return image_data
    except Exception as e:
        pass

    # Return a placeholder black tile if fetching failed
    return np.zeros((THUMBNAIL_SIZE[1], THUMBNAIL_SIZE[0], 3), dtype=np.uint8)


async def download_images(api_url, total_images):
    images = []

    async with aiohttp.ClientSession() as session:
        offset = 0
        limit = 10  # Adjust the limit as needed
        remaining_images = total_images

        while remaining_images > 0:
            current_limit = min(remaining_images, limit)
            image_url = await get_image_url_list(limit=current_limit, offset=offset)
            tasks = [fetch_image(session, image_url[i]) for i in range(current_limit)]
            batch_images = await asyncio.gather(*tasks)
            images.extend(batch_images)
            offset += current_limit
            remaining_images -= current_limit

    return images


async def create_composite_image():
    images = await download_images(API_URL, TOTAL_IMAGES)
    row, col = 0, 0
    img_count = 0
    composite_image = np.zeros(
        (THUMBNAIL_SIZE[1] * 12, THUMBNAIL_SIZE[0] * 11, 3), dtype=np.uint8
    )

    for image_data in images:
        try:
            if image_data is not None:
                # Decode the image and resize it
                img_array = np.frombuffer(image_data, dtype=np.uint8)
                image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                image = cv2.resize(image, THUMBNAIL_SIZE)

                # Calculate the position in the composite image grid
                row = img_count // 11
                col = img_count % 11
                # Paste the thumbnail into the composite image
                composite_image[
                    row * THUMBNAIL_SIZE[1] : (row + 1) * THUMBNAIL_SIZE[1],
                    col * THUMBNAIL_SIZE[0] : (col + 1) * THUMBNAIL_SIZE[0],
                ] = image
        except Exception as e:
            # Handle image decode errors here
            composite_image[
                row * THUMBNAIL_SIZE[1] : (row + 1) * THUMBNAIL_SIZE[1],
                col * THUMBNAIL_SIZE[0] : (col + 1) * THUMBNAIL_SIZE[0],
            ] = [
                255,
                0,
                0,
            ]  # Blue tile
        img_count += 1

    return composite_image


@app.route("/")
async def serve_composite_image(request):
    try:
        composite_image = await create_composite_image()

        # Encode the composite image to JPEG format
        _, image_data = cv2.imencode(".jpg", composite_image)

        # Return the image as a binary response
        return response.raw(image_data.tobytes(), content_type="image/jpeg")

    except Exception as e:
        return response.text(f"An error occurred: {e}", status=500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

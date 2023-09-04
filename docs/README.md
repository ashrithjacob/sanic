## Sanic server serving composite image of 132 images:
- All images retrieved concurrently
- renders sub-image black if fetching error
- renders sub-image blue if decode error

## Example output:
![alt text](../images/composite_image.png)

## How to run:
Run the following commands:
- `pip3 install -r requirements.txt` (install packages)
- `python3 src/main.py` (start sanic server - image rendered at root url)


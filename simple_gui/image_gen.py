import requests
from PIL import Image
from io import BytesIO

def generate_image(prompt):
    url = f"https://image.pollinations.ai/prompt/{prompt}"

    img_data = requests.get(url).content

    # 保存
    with open("generated.png", "wb") as f:
        f.write(img_data)

    # 显示
    image = Image.open(BytesIO(img_data))
    image.show()
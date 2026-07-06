from config import ROUTERAI_API_KEY


prompt = "логотип chatgp по середине, а вокруг него летают фейверки. Сверху написано 'как хорошо нихуя не делать'"


import requests
import base64

response = requests.post(
    "https://routerai.ru/api/v1/images",
    headers={
        "Authorization": f"Bearer {ROUTERAI_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "recraft/recraft-v4.1-utility",
        "prompt": prompt,
        "n": 1,
        "aspect_ratio": "9:16"
        #"size": "1080x1920",
    },
)

result = response.json()

# Изображения возвращаются в base64 (data[].b64_json)
for i, image in enumerate(result.get("data", [])):
    with open(f"generated_image_{i}.png", "wb") as f:
        f.write(base64.b64decode(image["b64_json"]))
    print(f"Image saved to generated_image_{i}.png")

# Стоимость запроса в рублях
print("Cost (RUB):", result.get("usage", {}).get("cost"))

import requests
import os

history = []
system_prompt = "Ты полезный AI-ассистент. Отвечай кратко и по делу."


def chat(message: str, api_key: str, history: list) -> str:
    #url = "https://routerai.ru/api/v1/chat/completions"
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    messages = [{"role": "system", "content": system_prompt}]
    messages += [
        {"role": "user", "content": msg["user"]} if "user" in msg else
        {"role": "assistant", "content": msg["assistant"]}
        for msg in history
    ]
    messages.append({"role": "user", "content": message})

    payload = {
        #"model": "deepseek/deepseek-v4-flash",
        "model": "openai/gpt-oss-20b:free",
        "messages": messages
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        return reply
    
    except requests.exceptions.RequestException as e:
        return f"Ошибка запроса: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Ошибка парсинга ответа: {str(e)}"


if __name__ == "__main__":
    api_key = os.getenv("API_KEY")
    while True:
        user_message = input("\nВы: ")
        response = chat(user_message, api_key, history)
        history.append({"user": user_message, "assistant": response})
        print(f"AI: {response}")

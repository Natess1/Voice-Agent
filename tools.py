import json
import os
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus

APPS = {
    "блокнот": ["notepad.exe"],
    "калькулятор": ["calc.exe"],
    "проводник": ["explorer.exe"],
}

BROWSER_NAME = "браузер"
SEARCH_URL = "https://duckduckgo.com/?q="
HOME_URL = "https://duckduckgo.com"

WORKSPACE = Path("D:/voice-agent/workspace")
ALLOWED_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv"}
MAX_FILE_CHARS = 20000

os.makedirs(WORKSPACE, exist_ok=True)


def available_apps():
    return list(APPS.keys()) + [BROWSER_NAME]


def open_app(name):
    key = str(name).strip().lower()
    if key == BROWSER_NAME:
        webbrowser.open(HOME_URL)
        return "Браузер открыт."
    command = APPS.get(key)
    if command is None:
        return "Неизвестное приложение. Доступны: " + ", ".join(available_apps())
    subprocess.Popen(command)
    return f"Приложение {key} запущено."


def search_web(query):
    text = str(query).strip()
    if not text:
        return "Пустой поисковый запрос."
    webbrowser.open(SEARCH_URL + quote_plus(text))
    return f"В браузере открыт поиск по запросу: {text}"


def create_file(filename, content):
    name = str(filename).strip()
    if not name:
        return "Не указано имя файла."
    text = str(content)
    if len(text) > MAX_FILE_CHARS:
        return "Содержимое слишком большое, файл не создан."
    try:
        root = WORKSPACE.resolve()
        target = (root / name).resolve()
    except (OSError, ValueError):
        return "Недопустимое имя файла."
    if root not in target.parents:
        return "Файл можно создавать только внутри рабочей папки."
    if target.suffix.lower() not in ALLOWED_EXTENSIONS:
        return "Недопустимое расширение. Разрешены: " + ", ".join(sorted(ALLOWED_EXTENSIONS))
    if target.exists():
        return "Файл с таким именем уже существует, перезаписывать его нельзя."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return f"Файл создан: {target}"


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Открыть программу на компьютере пользователя.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": available_apps(),
                        "description": "Название программы.",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Найти информацию в интернете: открывает поиск в браузере.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": (
                "Создать новый текстовый файл с заданным содержимым в рабочей папке. "
                "Имя файла должно включать расширение: .txt, .md, .py, .json или .csv."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Имя файла с расширением, например notes.txt.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Полный текст, который нужно записать в файл.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
]

TOOLS = {
    "open_app": lambda args: open_app(args.get("name", "")),
    "search_web": lambda args: search_web(args.get("query", "")),
    "create_file": lambda args: create_file(args.get("filename", ""), args.get("content", "")),
}


def run_tool(name, arguments):
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return "Не удалось разобрать аргументы инструмента."
    if not isinstance(arguments, dict):
        return "Некорректные аргументы инструмента."
    handler = TOOLS.get(name)
    if handler is None:
        return f"Неизвестный инструмент: {name}"
    try:
        return handler(arguments)
    except Exception as error:
        return f"Ошибка выполнения инструмента: {error}"
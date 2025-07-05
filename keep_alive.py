from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():
    try:
        with open("version", "r") as f:
            return f"Discord bot ok - version: {f.read().strip()}"
    except:
        return "Discord bot ok - version: unknown"


def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()

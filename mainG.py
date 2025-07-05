import os
import sys
import subprocess
import requests
import shutil
import zipfile
import asyncio

from keep_alive import keep_alive

VERSION_FILE = "version"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

REPO_RELEASE_URL = "https://api.github.com/repos/whiteout-project/bot/releases/latest"


def get_latest_release():
    try:
        print("🔍 Checking GitHub release...")
        res = requests.get(REPO_RELEASE_URL, timeout=30)
        res.raise_for_status()
        data = res.json()
        tag = data.get("tag_name", "")
        asset = data["assets"][0]["browser_download_url"] if data.get("assets") else None
        body = data.get("body", "")
        print(f"✅ Latest release: {tag}")
        return tag, asset, body
    except Exception as e:
        print(f"❌ Failed to get release: {e}")
        return None, None, None


def get_current_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return "v0.0.0"


def write_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(version)


def update_bot():
    latest_tag, asset_url, notes = get_latest_release()
    current_version = get_current_version()

    print(f"📦 Current version: {current_version}, Latest: {latest_tag}")
    if latest_tag and latest_tag != current_version and asset_url:
        print("⬇️ Downloading update...")
        r = requests.get(asset_url)
        with open("update.zip", "wb") as f:
            f.write(r.content)
        with zipfile.ZipFile("update.zip", 'r') as zip_ref:
            zip_ref.extractall("update")

        for root, _, files in os.walk("update"):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, "update")
                dst_path = os.path.join(".", rel_path)

                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)

        os.remove("update.zip")
        shutil.rmtree("update")
        write_version(latest_tag)
        print("✅ Update complete.")
        return True
    else:
        print("⏩ No update needed.")
    return False


def install_requirements():
    if os.path.exists("requirements.txt"):
        print("📦 Installing dependencies...")
        subprocess.call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("⚠️ No requirements.txt found.")


def restart_bot():
    print("♻️ Restarting bot...")
    os.execv(sys.executable, [sys.executable] + sys.argv)


def should_update():
    return "--autoupdate" in sys.argv


def run_bot():
    import discord
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        print(f"✅ Logged in as {bot.user}")
        try:
            await bot.tree.sync()
        except Exception as e:
            print(f"⚠️ Failed to sync commands: {e}")

    @bot.command()
    async def ping(ctx):
        await ctx.send("pong!")

    asyncio.run(bot.start(DISCORD_TOKEN))


def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not set in environment variables.")
        sys.exit(1)

    keep_alive()  # Start web server for Render health check

    if "--no-venv" not in sys.argv and sys.prefix == sys.base_prefix:
        print("⚠️ Detected outside virtualenv. Recommend using --no-venv for container.")
        sys.exit(1)

    install_requirements()

    if should_update():
        updated = update_bot()
        if updated:
            restart_bot()

    run_bot()


if __name__ == "__main__":
    main()
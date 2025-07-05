import os
import sys
import subprocess
import requests
import shutil
import zipfile
import asyncio
from keep_alive import keep_alive

VERSION_FILE = "version"
DISCORD_TOKEN = os.getenv("discordkey")  # 改為你的環境變數名稱
RELEASE_URL = "https://api.github.com/repos/whiteout-project/bot/releases/latest"

def get_latest_release():
    try:
        print("🔍 Checking GitHub release...")
        r = requests.get(RELEASE_URL)
        r.raise_for_status()
        data = r.json()
        tag = data.get("tag_name", "")
        asset = data["assets"][0]["browser_download_url"] if data.get("assets") else None
        print(f"✅ Latest release tag: {tag}")
        return tag, asset
    except Exception as e:
        print(f"❌ Failed to get latest release: {e}")
        return None, None

def get_current_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return "v0.0.0"

def write_version(tag):
    with open(VERSION_FILE, "w") as f:
        f.write(tag)

def install_requirements(path="requirements.txt"):
    if os.path.exists(path):
        print(f"📦 Installing dependencies from {path}...")
        subprocess.call([sys.executable, "-m", "pip", "install", "-r", path])
    else:
        print(f"⚠️ {path} not found.")

def update_bot():
    latest_tag, asset_url = get_latest_release()
    current_version = get_current_version()
    print(f"📌 Current version: {current_version}, Latest: {latest_tag}")

    if latest_tag and asset_url and latest_tag != current_version:
        print("⬇️ Downloading update...")
        r = requests.get(asset_url)
        with open("update.zip", "wb") as f:
            f.write(r.content)
        print("📂 Extracting update...")
        with zipfile.ZipFile("update.zip", "r") as zip_ref:
            zip_ref.extractall("update")

        print("🛠️ Applying update...")
        for root, _, files in os.walk("update"):
            for file in files:
                src = os.path.join(root, file)
                rel = os.path.relpath(src, "update")
                dst = os.path.join(".", rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

        if os.path.exists("update/requirements.txt"):
            install_requirements("update/requirements.txt")

        shutil.rmtree("update")
        os.remove("update.zip")
        write_version(latest_tag)
        print("✅ Update applied. Restarting bot...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print("⏩ No update needed.")

def should_update():
    return "--autoupdate" in sys.argv

def main():
    print("🚀 Starting Discord bot...")
    keep_alive()

    if not DISCORD_TOKEN:
        print("❌ Environment variable 'discordkey' not set.")
        sys.exit(1)
    else:
        print("✅ Token detected.")

    if should_update():
        update_bot()

    install_requirements()
    run_bot()

def run_bot():
    import discord
    from discord.ext import commands
    from discord import app_commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
        try:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands.")
        except Exception as e:
            print(f"⚠️ Slash command sync failed: {e}")

    @bot.tree.command(name="ping", description="Ping the bot")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message("🏓 Pong!", ephemeral=True)

    @bot.tree.command(name="status", description="Show bot status")
    async def status(interaction: discord.Interaction):
        version = get_current_version()
        await interaction.response.send_message(f"✅ Bot is online. Version: {version}", ephemeral=True)

    asyncio.run(bot.start(DISCORD_TOKEN))

if __name__ == "__main__":
    main()

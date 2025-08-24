import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1314934126897528876
PINNED_MESSAGE_ID = None

SCHEDULE_TZ = "America/Toronto"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

WEEKLY_SCHEDULE = [
    (0, 19, 0),  # Monday 19:00
    (2, 16, 0),  # Wednesday 16:00
    (4, 22, 0),  # Friday 22:00
    (6, 13, 0),  # Sunday 13:00
]

# ----------------- helper functions -----------------

def get_week_occurrence(weekday: int, hour: int, minute: int) -> int:
    tz = ZoneInfo(SCHEDULE_TZ)
    now_local = datetime.now(tz)
    start_of_week_local = (now_local - timedelta(days=now_local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    target_local = (start_of_week_local + timedelta(days=weekday)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if target_local < now_local:
        target_local += timedelta(days=7)
    target_utc = target_local.astimezone(timezone.utc)
    return int(target_utc.timestamp())

def build_schedule_message() -> str:
    lines = [f"📅 **Upcoming Schedule:** *(times shown in your local time)*"]
    for weekday, hour, minute in WEEKLY_SCHEDULE:
        ts = get_week_occurrence(weekday, hour, minute)
        lines.append(f"- <t:{ts}:F>")
    return "\n".join(lines)

# ----------------- bot events -----------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} | Using timezone: {SCHEDULE_TZ}")
    await update_schedule_once()
    update_schedule_loop.start()

@tasks.loop(hours=24)
async def update_schedule_loop():
    await update_schedule_once()

async def update_schedule_once():
    global PINNED_MESSAGE_ID
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Could not find the channel (check CHANNEL_ID and bot permissions).")
        return
    try:
        if PINNED_MESSAGE_ID:
            msg = await channel.fetch_message(PINNED_MESSAGE_ID)
            await msg.edit(content=build_schedule_message())
            print("📝 Schedule updated")
            return
    except discord.NotFound:
        PINNED_MESSAGE_ID = None
    msg = await channel.send(build_schedule_message())
    await msg.pin()
    PINNED_MESSAGE_ID = msg.id
    print("📌 New schedule posted & pinned")

if __name__ == "__main__":
    bot.run(TOKEN)

import os
from manage import ENVPATH
os.environ.setdefault('ENVPATH', ENVPATH)

from main.env import DISCORDBOTTOKEN
import discord

Discord = discord.Client()

@Discord.event
async def on_ready():
    print(f"{Discord.user} has connected to discord.")


Discord.run(DISCORDBOTTOKEN)
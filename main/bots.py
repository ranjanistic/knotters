import discord
from .env import GITHUBBOTTOKEN, DISCORDBOTTOKEN
from github import Github as GHub

Github = GHub(GITHUBBOTTOKEN)

# Discord = discord.Client()

# @Discord.event
# async def on_ready():
#     print(f"{Discord.user} has connected to discord.")

# Discord.run(DISCORDBOTTOKEN)
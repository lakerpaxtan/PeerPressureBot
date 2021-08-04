# For testing use only
# -------------------------------------------------------
import asyncio
import os
import sys

import discord
import logging
from dotenv import load_dotenv
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
# -------------------------------------------------------
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    for guild in client.guilds:
        LOGGER.info(f'{client.user} is connected to the guild...: {guild.name} with ID...: {guild.id}')
        tasks = [list_members(guild), list_channels(guild)]
        await asyncio.gather(*tasks)


@client.event
async def on_message(message):
    LOGGER.info(f'Message Received. Text: "{message.content}" Author: "{message.author.name}" Channel: "{message.channel.name}"') # NOQA
    if message.content.startswith('!pressure'):
        await message.channel.send("https://www.youtube.com/watch?v=VwIPqkbeZA4")

    if message.author.name == 'JoeJimBob':
        sent_message = await message.author.send("Go to bed")
        await asyncio.sleep(10)
        await sent_message.delete()


async def list_members(guild):
    for member in guild.members:
        LOGGER.info(f'member named: {member}')


async def list_channels(guild):
    for channel in guild.channels:
        LOGGER.info(f'Got channel: {channel.name} of type {channel.type}')


client.run(TOKEN)

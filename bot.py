# For testing use only
# -------------------------------------------------------
import asyncio
import os
import sys
import re
import discord
import logging
import datetime
from dotenv import load_dotenv
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
# -------------------------------------------------------
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)


class GoalThread:

    thread_to_object = {}

    def __init__(self, thread, name):
        self.name = name
        self.parent_channel = thread.parent
        self.thread = thread
        self.guild = thread.guild
        self.members = {}
        self.end_time = datetime.datetime.now() + datetime.timedelta(hours=23, minutes=50)

        GoalThread.thread_to_object[self.thread] = self

    def add_member(self, user):
        self.members[user.id] = {
            "object": user,
            "name": user.name,
            "submissions": [],
            "confirmed": False,
            "votes": 0.0
        }


@client.event
async def on_ready():
    for guild in client.guilds:
        LOGGER.info(f'{client.user} is connected to the guild...: {guild.name} with ID...: {guild.id}')
        tasks = [list_members(guild), list_channels(guild)]
        await asyncio.gather(*tasks)


@client.event
async def on_message(message):
    LOGGER.info(f'Message Received. Text: "{message.content}" Author: "{message.author}" Channel: "{message.channel}"') # NOQA
    if message.content.startswith('!pressure'):
        await message.channel.send("https://www.youtube.com/watch?v=VwIPqkbeZA4")

    if message.author.name == 'JoeJimBob':
        # await message.delete()
        # sent_message = await message.author.send("Go to bed")
        # await asyncio.sleep(5)
        # await sent_message.delete()
        LOGGER.info("Got a message from jimjamham")

    if message.content.startswith('!goal'):
        await create_goal_thread_from_input(message)

    if message.content.startswith('!add'):
        await add_members_to_goal(message)

    if message.content.startswith('!submit'):
        await submit_to_goal(message)

    if message.content.startswith('!get_roles'):
        await print_out_roles(message)


async def add_members_to_goal(message):
    member_set = set()
    for user in message.mentions:
        member_set.add(user)

    for role in message.role_mentions:
        for user in role.members:
            member_set.add(user)

    for user in member_set:
        await add_member_to_goal(message, user)


async def print_out_roles(message):
    for role in message.guild.roles:
        LOGGER.info(f'Role: {role} and id: {role.id}')


async def submit_to_goal(message):
    message_attachments = message.attachments
    message_text = message.content.replace('!submit', '').strip()
    if message.channel in GoalThread.thread_to_object.keys() \
            and len(message_attachments) > 0 and len(message_text) > 0:

        submitting_member = message.author
        goal_thread = GoalThread.thread_to_object[message.channel]

        if submitting_member.id not in goal_thread.members.keys():
            LOGGER.critical("Not a member of this thread")
            await goal_thread.thread.send("You aren't a member bro... you can't submit")
            return

        await goal_thread.thread.send(f"Received submission from {submitting_member.name}... confirming with others")
        await confirm_submission(goal_thread, submitting_member, message_text, message_attachments)


async def confirm_submission(goal_thread, submitting_member, message_text, message_attachments):

    async def confirm_submission_for_member(member_dict):
        member_object = member_dict["object"]
        file_attachments = await asyncio.gather(*[attachment.to_file() for attachment in message_attachments])
        msg = await member_object.send(f"Do you approve this submission from <{submitting_member.name}> "
                                       f"using text and attachments below (thumbs up or thumbs down): \n"
                                       f"<{message_text}>", files=file_attachments)
        await msg.add_reaction('👍')
        await msg.add_reaction('👎')
        rc = await wait_for_response(msg, member_object, goal_thread, submitting_member)
        LOGGER.debug(f"Got return code {rc} from {member_object.name}")
        if rc == 1:
            submitting_member_object["votes"] += 1 / total_members
        elif rc == -1:
            LOGGER.info(f"Got a no vote for {submitting_member.name} from {member_object.name}")

    # ========================================================================================
    total_members = len(goal_thread.members)
    submitting_member_object = goal_thread.members[submitting_member.id]
    if submitting_member_object["confirmed"] is True:
        await goal_thread.thread.send(f"HEY! You've already been confirmed. "
                                      f"Stop trying to submit {submitting_member.name}")
        return

    await asyncio.gather(*[confirm_submission_for_member(storage) for _, storage in goal_thread.members.items()])

    ratio = submitting_member_object["votes"]
    if ratio > 0.5:
        submitting_member_object["confirmed"] = True
        await goal_thread.thread.send(f"CONGRATULATIONS: <{submitting_member.name}>... your submission has been "
                                      f"confirmed by your peers with ratio {ratio}")
    else:
        await goal_thread.thread.send(f"YOU SUCK: <{submitting_member.name}>... your submission has been "
                                      f"denied by your peers with ratio {ratio}")
    # ========================================================================================


async def wait_for_response(msg, member_sent_to, goal_thread, submitting_member):
    def reaction_check(reaction, user):
        return msg == reaction.message and (str(reaction.emoji) == '👍' or str(reaction.emoji) == '👎')
    try:
        reaction, user = await client.wait_for('reaction_add', timeout=1200, check=reaction_check)
        LOGGER.info(f"received response to confirmation from {user} with {reaction}")
        if str(reaction.emoji) == '👍':
            return 1
        elif str(reaction.emoji) == '👎':
            return -1
        else:
            return 0
    except Exception as e:
        LOGGER.critical(f"error: {str(e)}")
        await goal_thread.thread.send(f"Member: <{member_sent_to.name}> did not respond to submission "
                                      f"from: <{submitting_member.name}> in time... SHAME")


async def list_members(guild):
    for member in guild.members:
        LOGGER.info(f'member named: {member}')


async def list_channels(guild):
    for channel in guild.channels:
        LOGGER.info(f'Got channel: {channel.name} of type {channel.type}')


async def create_goal_thread_from_input(message):
    thread_name = message.content.replace('!goal', '').strip()
    if len(thread_name) > 0:
        thread_object = await message.start_thread(name=thread_name)
        goal_thread = GoalThread(thread_object, thread_name)
        await thread_object.send(f"24 hour timer begins now....  ends at "
                                 f"{goal_thread.end_time.strftime('%Y-%m-%d-%H:%M:%S')}")

    else:
        await message.channel.send("Hey loser. Bad command. Include thread name '!goal thread_name'")


async def add_member_to_goal(message, member_object):
    if message.channel in GoalThread.thread_to_object.keys():
        goal_thread = GoalThread.thread_to_object[message.channel]
        await goal_thread.thread.send(f'Added new member {member_object.name} to this thing')
        goal_thread.add_member(member_object)
        asyncio.create_task(shame_member(member_object, goal_thread, goal_thread.end_time))


async def shame_member(member, goal_thread, end_time):
    LOGGER.info(f"Start awaiting for member {member}")
    await asyncio.sleep((end_time - datetime.datetime.now()).total_seconds())
    LOGGER.info(f"Done awaiting for member {member}")
    if goal_thread.members[member.id]["confirmed"] is False:
        await goal_thread.parent_channel.send(f"HEY <@&838902415117123605> SHAME THE HELL OUT OF {member.name} for not completing {goal_thread.name} in time")
        await goal_thread.thread.send(f"HEY <@&838902415117123605> SHAME THE HELL OUT OF {member.name} for not completing {goal_thread.name} in time")


client.run(TOKEN)

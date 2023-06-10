#!venv/bin/python

"""
Forwarder bot v1.1.2
Written by: https://github.com/RohullahNazarie

1) Create an isolated virtual environment using: `python -m venv venv`
2) Install requirements using: `pip install -r requirements.txt`
3) add your API_ID and API_HASH to Login.py
4) add API_ID, API_HASH and sudo to :: plugins/jsons/config.json
5) run this file ( main.py )
6) Enter your credential and login
"""

from Login import get_client
from plugins.utils import Entities, Filters, Config, Messages
from telethon.sync import events
from Types import *

from time import sleep

import re
import logging


# ==================
entities_manager = Entities()
filters_manager = Filters()
config_manager = Config()
message_manager = Messages()

client = get_client()

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.WARNING
)

client.start()

print("FORWARDER BOT STARTED ;)")
# ==================


@client.on(events.NewMessage(incoming=True))
async def status(message: Message):

    if config_manager.bot_enabled:
        return

    if await message.get_sender() == await client.get_me() or message.sender_id in config_manager.sudo:
        return

    else:
        raise events.StopPropagation


@client.on(events.NewMessage())
async def forwarder(message: Message):
    try:
        chat_id = message.chat.id
    except AttributeError:
        chat_id = message.chat_id

    if chat_id not in entities_manager.entities:
        return

    target_entities = entities_manager.get_target_entities(chat_id)

    if message.poll:
        for target in target_entities:
            await message.forward_to(target)
        return

    if config_manager.get('filter_words'):
        for word in filters_manager.words:
            message.text = re.sub(r'(?i){0}'.format(word[0]), word[1], message.text)

    if config_manager.get('add_signature'):
        if config_manager.sign:
            message.text = message.text + f'\n\n{config_manager.sign}'

    replied_message = None
    reply_to = None
    if message.is_reply:
        replied_message: Message = await message.get_reply_message()
        replied_message = replied_message.id

    for target in target_entities:

        if replied_message is not None:
            try:
                reply_to = message_manager.get(chat_id, replied_message)
            except ValueError:
                message.text = f'[ Replied to message id: {replied_message} ]\n\n' + message.text

            if reply_to:
                for i in reply_to:
                    if i[0] == target:
                        reply_to = i[1]

        sent_message = await client.send_message(target, message.message, reply_to=reply_to)
        message_manager.add(chat_id, message.id, target, sent_message.id)
        sleep(0.5)


@client.on(events.NewMessage(incoming=True))
async def forbid_non_sudo_commands(message: Message):
    if await message.get_sender() == await client.get_me() or message.sender_id in config_manager.sudo:
        return

    else:
        raise events.StopPropagation


@client.on(events.NewMessage(pattern=r'^[Ss]ync$'))
async def add_config(message: Message):

    replied_message: Message = await message.respond('Syncing dialogs...')

    try:
        dialogs = await client.get_dialogs()
    except Exception as e:
        await message.edit(f'❗️ Error in syncing chats:\n {e}')
        raise events.StopPropagation

    await replied_message.edit(f"✅ Successfully synced {len(dialogs)} chats")
    raise events.StopPropagation


@client.on(events.NewMessage(
    pattern=r'^[Ll]ink @?(-?[1-9a-zA-Z][a-zA-Z0-9_]{4,}) to @?(-?[1-9a-zA-Z][a-zA-Z0-9_]{4,})$'))
async def add_config(message: Message):
    msg: str = message.raw_text
    msg = msg.replace('@', '')
    pattern = re.compile(r'^[Ll]ink @?(-?[1-9a-zA-Z][a-zA-Z0-9_]{4,}) to @?(-?[1-9a-zA-Z][a-zA-Z0-9_]{4,})$')

    match = pattern.match(msg)
    if not match:
        return

    processing: Message = await message.reply('Processing...')

    base_entity = match.group(1).lower()
    target_entity = match.group(2).lower()

    try:
        base_entity = int(base_entity)
    except ValueError:
        pass

    try:
        target_entity = int(target_entity)
    except ValueError:
        pass

    try:
        base_entity = await client.get_entity(base_entity)
    except:
        await processing.edit('❗️ Base entity does not exists')
        return

    try:
        target_entity = await client.get_entity(target_entity)
    except:
        await processing.edit('❗️ Target entity does not exists')
        return

    try:
        entities_manager.add_config(base_entity.id, target_entity.id)
    except ValueError as e:
        await processing.edit(f'❗️ {e.args[0]}')
        return

    try:
        base_entity_title = base_entity.title
    except AttributeError:
        base_entity_title = base_entity.first_name
        if base_entity.last_name:
            base_entity_title += base_entity.last_name

    try:
        target_entity_title = target_entity.title
    except AttributeError:
        target_entity_title = target_entity.first_name
        if target_entity.last_name:
            target_entity_title += target_entity.last_name

    await processing.edit(f"✅ [ `{base_entity_title}` ] linked to [ `{target_entity_title}` ]")


@client.on(events.NewMessage(pattern=r'^[Uu]nlink @?(-?[1-9a-zA-Z][a-zA-Z0-9_]{4,})$'))
async def remove_config(message: Message):
    msg: str = message.raw_text
    msg = msg.replace('@', '')
    pattern = re.compile(r'^[Uu]nlink @?([1-9a-zA-Z][a-zA-Z0-9_]{4,})$')

    match = pattern.match(msg)
    if not match:
        return

    processing: Message = await message.reply('Processing...')

    base_entity = match.group(1).lower()

    try:
        base_entity = int(base_entity)
    except ValueError:
        pass

    try:
        base_entity = await client.get_entity(base_entity)
    except:
        await processing.edit('❗️ Base entity does not exists')
        return

    try:
        base_entity_title = base_entity.title
    except AttributeError:
        base_entity_title = base_entity.first_name
        if base_entity.last_name:
            base_entity_title += base_entity.last_name

    try:
        count = entities_manager.remove_config(base_entity.id)
    except ValueError as e:
        await processing.edit(f'❗️ {e.args[0]}')
        return

    await processing.edit(f"✅ [ `{base_entity_title}` ] unlinked from {count} entities")


@client.on(events.NewMessage(pattern=r'^[Aa]dd filter \"(.+)\" to \"(.+)\"$'))
async def add_filter(message: Message):
    msg: str = message.raw_text
    pattern = re.compile(r'^[Aa]dd filter \"(.+)\" to \"(.+)\"$')

    match = pattern.match(msg)
    if not match:
        return

    from_word = match.group(1)
    to_word = match.group(2)

    try:
        filters_manager.add_filter(from_word, to_word)
    except ValueError as e:
        await message.reply(f"❗️ {e.args[0]}")
        return

    await message.reply(f"✅ **{from_word}** will be edited to **{to_word}** (case insensitive)")


@client.on(events.NewMessage(pattern=r'^[Rr]emove filter \"(.+)\"$'))
async def remove_filter(message: Message):
    msg: str = message.raw_text
    pattern = re.compile(r'^[Rr]emove filter \"(.+)\"$')

    match = pattern.match(msg)
    if not match:
        return

    from_word = match.group(1)

    try:
        filters_manager.remove_filter(from_word)
    except ValueError as e:
        await message.reply(f"❗️ {e.args[0]}")
        return

    await message.reply(f"✅ **{from_word}** filters erased.")


@client.on(events.NewMessage(pattern=r'^[Ff]ilters$'))
async def get_filters(message: Message):

    filters = filters_manager.words

    if not filters:
        await message.reply("❗️ No filters submitted.")
        return

    text = "📁 Filter list: \n\n"

    for key, value in filters:
        text += f"**{key}** ➡️ **{value}**"
        text += '\n'

    await message.reply(text)


@client.on(events.NewMessage(pattern=r'^[Ss]ettings'))
async def get_settings(message: Message):

    text = "⚙️ Settings: \n\n"
    text += f"`Bot status   ` ➡ **{'On' if config_manager.bot_enabled else 'Off'}**\n"
    text += f"`Filter words ` ➡ **{'Enabled' if config_manager.get('filter_words') else 'Disabled'}**\n"
    text += f"`Add signature` ➡ **{'Enabled' if config_manager.get('add_signature') else 'Disabled'}**\n"

    if config_manager.sign:
        text += f"`Signature    ` ⬇️ \n**{config_manager.sign}**"
    else:
        text += f"`Signature    ` ➡ **Not defined**"

    await message.reply(text)


@client.on(events.NewMessage(pattern=r'^[Ll]inks'))
async def get_linked_entities(message: Message):

    entities = entities_manager.configs

    if not entities:
        await message.reply("❗️ There is no linked entities.")
        return

    text = "🖇 Linked entities: \n\n"

    for key, value in entities:
        text += f"**{key}** ➡️ **{value}**"
        text += '\n'

    await message.reply(text)


@client.on(events.NewMessage(pattern=r'^[Oo](:?n|ff)$'))
async def change_bot_status(message: Message):
    command = message.raw_text.lower()

    if command == 'on':
        config_manager.change('bot_enabled', True)
        await message.reply('👀 Bot turned on')
        return
    elif command == 'off':
        config_manager.change('bot_enabled', False)
        await message.reply('😴 Bot turned off')
        return


@client.on(events.NewMessage(pattern=r'^[Ff]ilters [Oo](:?n|ff)$'))
async def change_filters_status(message: Message):
    msg: str = message.raw_text
    pattern = re.compile(r'^[Ff]ilters ([Oo](:?n|ff))$')

    match = pattern.match(msg)
    if not match:
        return

    command = match.group(1).lower()

    if command == 'on':
        config_manager.change('filter_words', True)
        await message.reply('✅ Filter words enabled')
        return
    elif command == 'off':
        config_manager.change('filter_words', False)
        await message.reply('✅ Filter words disabled')
        return


@client.on(events.NewMessage(pattern=r'^[Ss]ign [Oo](:?n|ff)$'))
async def change_signature_status(message: Message):
    msg: str = message.raw_text
    pattern = re.compile(r'^[Ss]ign ([Oo](:?n|ff))$')

    match = pattern.match(msg)
    if not match:
        return

    command = match.group(1).lower()

    if command == 'on':
        config_manager.change('add_signature', True)
        await message.reply('✅ Adding signature enabled')
        return
    elif command == 'off':
        config_manager.change('add_signature', False)
        await message.reply('✅ Adding signature disabled')
        return


@client.on(events.NewMessage(pattern=r'^[Ss]ign text (.+)$'))
async def change_signature_text(message: Message):
    msg: str = message.raw_text
    pattern = re.compile(r'^[Ss]ign text (.+)$')

    match = pattern.match(msg)
    if not match:
        return

    signature = match.group(1).lower()

    config_manager.change('signature', signature)

    await message.reply(f'✅ Signature updated:\n{signature}')


@client.on(events.NewMessage(pattern=r'^[Hh]elp$'))
async def get_help(message: Message):
    with open('help.txt', 'r') as f:
        await message.reply(f.read(), parse_mode='html')
        return

client.run_until_disconnected()

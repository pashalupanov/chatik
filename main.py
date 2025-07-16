import os
import asyncio
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

# --- Конфиги ---
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNELS = [
    't.me/Selectel',
    't.me/vk_cloud_news',
    't.me/cloudruprovider',
]
KEYWORDS = ['update', 'обновлен', 'feature', 'изменен', 'релиз', 'release', 'новое', 'новинка', 'новая функция']

# --- Глобальное хранилище ---
recent_updates = []

# --- Сбор сообщений из каналов ---
async def fetch_updates():
    global recent_updates
    client = TelegramClient('anon', API_ID, API_HASH)
    await client.start()
    updates = []
    month_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    for channel in CHANNELS:
        try:
            entity = await client.get_entity(channel)
            history = await client(GetHistoryRequest(
                peer=entity,
                limit=100,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))
            for message in history.messages:
                if message.date < month_ago:
                    continue
                text = message.message or ''
                if any(k.lower() in text.lower() for k in KEYWORDS):
                    updates.append(f"[{channel}] {text[:200]}")
        except Exception as e:
            updates.append(f"[{channel}] Ошибка: {e}")
    recent_updates = updates
    await client.disconnect()

# --- Telegram-бот ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply('Привет! Я собираю обновления из каналов конкурентов. Напиши /updates чтобы получить свежие новости за последний месяц.')

@dp.message_handler(commands=['updates'])
async def send_updates(message: types.Message):
    await message.reply('Собираю свежие обновления, подожди...')
    await fetch_updates()
    if not recent_updates:
        await message.reply('За последний месяц ничего не найдено.')
    else:
        # Ограничим размер сообщения Telegram (макс 4096 символов)
        chunk = ''
        for upd in recent_updates:
            if len(chunk) + len(upd) + 2 > 4000:
                await message.reply(chunk)
                chunk = ''
            chunk += upd + '\n\n'
        if chunk:
            await message.reply(chunk)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True) 

import logging
import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from fastapi import FastAPI, Request

from tgbot.config import load_config
from tgbot.filters.admin import AdminFilter
from tgbot.handlers.admin import register_admin
from tgbot.handlers.user import register_user
from tgbot.middlewares.environment import EnvironmentMiddleware, ThrottlingMiddleware
from avito_parsing import main_avito

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из файла .env
config = load_config(".env")

# Инициализация бота и диспетчера
storage = RedisStorage2() if config.tg_bot.use_redis else MemoryStorage()
bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
dp = Dispatcher(bot, storage=storage)

# Регистрация middlewares, filters и handlers
def register_all_middlewares(dp, config):
    dp.setup_middleware(EnvironmentMiddleware(dispatcher=dp, config=config))
    dp.setup_middleware(ThrottlingMiddleware())

def register_all_filters(dp):
    dp.filters_factory.bind(AdminFilter)

def register_all_handlers(dp):
    register_admin(dp)
    register_user(dp)

register_all_middlewares(dp, config)
register_all_filters(dp)
register_all_handlers(dp)

# Инициализация FastAPI приложения
app = FastAPI()

# Настройка webhook
WEBHOOK_HOST = 'https://your.domain'
WEBHOOK_PATH = '/boting'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)

@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    Dispatcher.set_current(dp)
    Bot.set_current(bot)
    try:
        await dp.process_update(telegram_update)
    except Exception as e:
        logger.exception(f"Error processing update: {update}. Error: {e}")
        await bot.send_message(chat_id=config.tg_bot.admin_chat_id,
                               text=f"Bot is temporarily unavailable. Error: {e}")

# Запуск бота
if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8000)

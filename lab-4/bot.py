import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота 
bot_token = os.getenv("API_TOKEN")
if not bot_token:
    raise ValueError("Переменная окружения API_TOKEN не найдена")

bot = Bot(token=bot_token)
dp = Dispatcher(storage=MemoryStorage())

# Словарь для хранения курсов валют
rates = {}  

# Определение состояний для FSM
class CurrencyStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_conversion_currency = State()
    waiting_for_conversion_amount = State()

# Команда /save_currency (сохранение валюты)
@dp.message(Command("save_currency"))
async def save_currency_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(CurrencyStates.waiting_for_currency_name)

@dp.message(CurrencyStates.waiting_for_currency_name)
async def save_currency_name(message: types.Message, state: FSMContext):
    await state.update_data(currency_name=message.text.upper())  # Приводим к верхнему регистру
    await message.answer("Введите курс валюты к рублю:")
    await state.set_state(CurrencyStates.waiting_for_currency_rate)

@dp.message(CurrencyStates.waiting_for_currency_rate)
async def save_currency_rate(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    currency = user_data["currency_name"]
    
    try:
        rate = float(message.text.replace(",", "."))  # Поддержка ввода через запятую
        rates[currency] = rate
        await message.answer(f"Курс валюты {currency} {rate:.2f} руб. сохранен в словаре.")
    except ValueError:
        await message.answer("Ошибка! Введите корректное число.")
        return
    
    await state.clear()

# Команда /convert (конвертация валюты)
@dp.message(Command("convert"))
async def convert_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(CurrencyStates.waiting_for_conversion_currency)

@dp.message(CurrencyStates.waiting_for_conversion_currency)
async def convert_currency_name(message: types.Message, state: FSMContext):
    currency = message.text.upper()

    if currency not in rates:
        await message.answer("Ошибка! Валюта не найдена. Сначала сохраните курс с помощью /save_currency.")
        return

    await state.update_data(currency_name=currency)
    await message.answer(f"Введите сумму в валюте {currency} для конвертации в рубли:")
    await state.set_state(CurrencyStates.waiting_for_conversion_amount)

@dp.message(CurrencyStates.waiting_for_conversion_amount)
async def convert_amount(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    currency = user_data["currency_name"]
    rate = rates.get(currency, 0)

    try:
        amount = float(message.text.replace(",", "."))
        converted = amount * rate
        await message.answer(f"Сумма валюты в рублях:\n<b>{amount:.2f} {currency} = {converted:.2f} руб.</b>", parse_mode="HTML")
    except ValueError:
        await message.answer("Ошибка! Введите корректное число.")
        return

    await state.clear()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

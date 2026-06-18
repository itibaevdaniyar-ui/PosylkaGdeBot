import asyncio
import requests
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

ADMIN_ID = 8822799334

waiting_track = set()
waiting_courier = set()
waiting_operator = set()

STATUS_MAP = {
    "ISSPAY": "Отправление оплачено",
    "STR": "Принято к обработке",
    "RCPOPS": "Принято в отделении",
    "DLV": "Доставлено",
    "ARR": "Прибыло",
    "DESP": "Отправлено дальше",
    "RET": "Возврат отправителю"
}

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📦 Отследить посылку")],
        [KeyboardButton(text="🚚 Вызвать курьера")],
        [KeyboardButton(text="🏤 Найти отделение")],
        [KeyboardButton(text="📞 Связаться с оператором")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Добро пожаловать в PosylkaGde Bot 📦",
        reply_markup=menu
    )

@dp.message(F.text == "📦 Отследить посылку")
async def track_request(message: Message):
    waiting_track.add(message.from_user.id)
    await message.answer("Введите трек-номер:")

@dp.message(F.text == "🚚 Вызвать курьера")
async def courier_request(message: Message):
    waiting_courier.add(message.from_user.id)

    await message.answer(
        "Для вызова курьера отправьте одним сообщением:\n\n"
        "Имя:\n"
        "Телефон:\n"
        "Адрес:\n"
        "Вес:"
    )

@dp.message(F.text == "🏤 Найти отделение")
async def office_request(message: Message):
    await message.answer(
        "Функция поиска отделений скоро появится."
    )

@dp.message(F.text == "📞 Связаться с оператором")
async def operator_request(message: Message):
    waiting_operator.add(message.from_user.id)

    await message.answer(
        "Напишите ваш вопрос оператору одним сообщением."
    )

@dp.message()
async def process_message(message: Message):

    if message.from_user.id in waiting_operator:
        waiting_operator.remove(message.from_user.id)

        await message.bot.send_message(
            ADMIN_ID,
            f"📞 Обращение к оператору\n\n"
            f"{message.text}\n\n"
            f"ID клиента: {message.from_user.id}"
        )

        await message.answer(
            "✅ Ваше обращение отправлено оператору."
        )
        return

    if message.from_user.id in waiting_courier:
        waiting_courier.remove(message.from_user.id)

        await message.bot.send_message(
            ADMIN_ID,
            f"🚚 Новая заявка на курьера\n\n"
            f"{message.text}\n\n"
            f"ID клиента: {message.from_user.id}"
        )

        await message.answer(
            "✅ Заявка принята.\nНаш оператор свяжется с вами."
        )
        return

    if message.from_user.id not in waiting_track:
        return

    track_number = message.text.strip().upper()
    waiting_track.remove(message.from_user.id)

    try:
        url = f"https://pls-test.post.kz/api/v2/{track_number}/events"

        response = requests.get(url, timeout=15)

        if response.status_code != 200:
            await message.answer(
                "Не удалось получить данные по отправлению."
            )
            return

        data = response.json()

        if not data.get("events"):
            await message.answer(
                "События по отправлению не найдены."
            )
            return

        events_text = f"📦 {track_number}\n\n"

        for day in data["events"]:
            for activity in day["activity"]:
                status_code = activity["status"][0]
                status_text = STATUS_MAP.get(
                    status_code,
                    status_code
                )

                events_text += (
                    f"📍 {status_text}\n"
                    f"🏙 {activity['city']}\n"
                    f"🏤 {activity['name']}\n"
                    f"🕒 {activity['time']}\n\n"
                )

        await message.answer(events_text[:4000])

    except Exception as e:
        await message.answer(f"Ошибка: {e}")

async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

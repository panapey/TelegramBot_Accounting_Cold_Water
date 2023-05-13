import pyodbc
from aiogram import Bot, Dispatcher, executor, types
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Подключение к базе данных mssql
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};SERVER=YOUR_SERVER;DATABASE=YOUR_DATABASE;Trusted_Connection=yes')
cursor = conn.cursor()

bot = Bot(token='YOUR_BOT_TOKEN_HERE')
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_cmd_handler(message: types.Message):
    # Проверка, зарегистрирован ли уже пользователь
    cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id = ?", message.from_user.id)
    row = cursor.fetchone()
    if row[0] > 0:
        await message.answer("Вы уже зарегистрированы в нашей системе")
        return

    # Добавление информации о пользователе в таблицу
    cursor.execute("INSERT INTO users (telegram_id, chat_id, first_name, last_name, username) VALUES (?, ?, ?, ?, ?)",
                   message.from_user.id, message.chat.id, message.from_user.first_name, message.from_user.last_name,
                   message.from_user.username)
    conn.commit()

    await message.answer("Добро пожаловать! Вы успешно зарегистрировались в нашей системе")


@dp.message_handler(commands=['subscribe'])
async def subscribe_cmd_handler(message: types.Message):
    # Добавление информации о пользователе в таблицу
    cursor.execute("UPDATE users SET chat_id = ? WHERE telegram_id = ?", message.chat.id, message.from_user.id)
    conn.commit()

    await message.answer("Вы подписались на ежемесячные уведомления о внесении показателей счетчиков")


async def send_notifications():
    # Выборка информации о пользователях из таблицы
    cursor.execute("SELECT telegram_id, chat_id FROM users WHERE chat_id IS NOT NULL")
    rows = cursor.fetchall()

    # Отправка уведомлений пользователям
    for row in rows:
        user_id = row[0]
        chat_id = row[1]

        await bot.send_message(chat_id, f"Не забудьте внести показатели счетчиков за этот месяц!")


# Создание планировщика задач
scheduler = AsyncIOScheduler()
scheduler.add_job(send_notifications, 'cron', day=1)  # Запуск задания 1-го числа каждого месяца
scheduler.start()


@dp.message_handler(commands=['register_meter'])
async def register_meter_cmd_handler(message: types.Message):
    # Разбор аргументов команды
    args = message.text.split()[1:]
    if len(args) != 3:
        await message.answer("Использование: /register_meter <type> <serial_number> <location>")
        return

    meter_type = args[0]
    serial_number = args[1]
    location = args[2]

    # Добавление записи в таблицу приборов учета
    cursor.execute(
        "INSERT INTO meters (user_id, type, serial_number, location) VALUES ((SELECT id FROM users WHERE telegram_id = ?), ?, ?, ?)",
        message.from_user.id, meter_type, serial_number, location)
    conn.commit()

    await message.answer(
        f"Прибор учета {meter_type} зарегистрирован: серийный номер {serial_number}, расположение {location}")


@dp.message_handler(commands=['add_counter_value'])
async def add_counter_value_cmd_handler(message: types.Message):
    # Разбор аргументов команды
    args = message.text.split()[1:]
    if len(args) != 2:
        await message.answer("Использование: /add_counter_value <counter_id> <value>")
        return

    counter_id = int(args[0])
    value = float(args[1])

    # Check if user_id and counter_id exist in users and meters tables
    user_id = cursor.execute("SELECT id FROM users WHERE telegram_id = ?", message.from_user.id).fetchone()
    if not user_id:
        await message.answer("User not found in users table")
        return
    counter_exists = cursor.execute("SELECT 1 FROM meters WHERE id = ?", counter_id).fetchone()
    if not counter_exists:
        await message.answer("Counter not found in meters table")
        return

    # Добавление записи в таблицу показателей счетчиков
    cursor.execute(
        "INSERT INTO counter_values (user_id, counter_id, value) VALUES (?, ?, ?)",
        user_id[0], counter_id, value)
    conn.commit()

    await message.answer(f"Значение счетчика {counter_id} добавлено: {value}")


@dp.message_handler(commands=['calculate_payment'])
async def calculate_payment_cmd_handler(message: types.Message):
    # Выборка информации о показателях счетчиков из таблицы
    cursor.execute("SELECT SUM(value) FROM counter_values WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)",
                   message.from_user.id)
    row = cursor.fetchone()
    if row is None:
        await message.answer("No usage data found for user")
        return
    total_usage = row[0]

    # Расчет суммы к оплате
    total_payment = total_usage * 45

    await message.answer(f"Сумма к оплате: {total_payment} рублей")


if __name__ == '__main__':
    executor.start_polling(dp)

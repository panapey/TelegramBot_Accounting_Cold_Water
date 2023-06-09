import logging

import pyodbc
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token="6047380957:AAF3LLm8bM0Q7144-fOtpXhrFTUrpQPXuC0")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Подключение к базе данных
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};"
                      "SERVER=LAPTOP-DA4JVMQ8\SQLEXPRESS;"
                      "DATABASE=botdb;"
                      "Trusted_Connection=yes;")
cursor = conn.cursor()


# Определение состояний для конечного автомата
class Form(StatesGroup):
    full_name = State()


class MeterForm(StatesGroup):
    meter_type = State()
    serial_number = State()
    location = State()


class CounterForm(StatesGroup):
    counter_id = State()
    value = State()


async def send_action_keyboard(chat_id):
    # Создание кнопок
    button1 = InlineKeyboardButton("Подписаться на уведомления", callback_data="subscribe")
    button2 = InlineKeyboardButton("Зарегистрировать прибор учета", callback_data="register_meter")
    button3 = InlineKeyboardButton("Добавить показание счетчика", callback_data="add_counter_value")
    button4 = InlineKeyboardButton("Рассчитать платеж", callback_data="calculate_payment")

    # Создание клавиатуры
    keyboard = InlineKeyboardMarkup()
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)
    keyboard.add(button4)

    # Отправка сообщения с клавиатурой
    await bot.send_message(chat_id, "Выберите действие:", reply_markup=keyboard)


@dp.message_handler(commands=['start'])
async def start_cmd_handler(message: types.Message):
    # Проверка, зарегистрирован ли уже пользователь
    cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_id = ?", message.from_user.id)
    row = cursor.fetchone()
    if row[0] > 0:
        # Выборка информации о пользователе из таблицы
        cursor.execute("SELECT full_name, account_number FROM users WHERE telegram_id = ?", message.from_user.id)
        row = cursor.fetchone()
        full_name = row[0]
        account_number = row[1]

        # Отправка сообщения с приветствием и информацией о пользователе
        await message.answer(f"Добро пожаловать, {full_name}, ваш единый лицевой счет {account_number}")
    else:
        # Отправка сообщения с запросом информации о пользователе
        await message.answer("Пожалуйста, введите ваше ФИО и единый лицевой счет в формате:\nФИО;Номер лицевого счета")

        # Сохранение состояния ожидания ввода информации о пользователе
        await Form.full_name.set()

    # Отправка клавиатуры с кнопками для выбора действия
    await send_action_keyboard(message.chat.id)


@dp.message_handler(state=Form.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    # Разбор введенной информации о пользователе
    full_name, account_number = message.text.split(';')

    # Добавление информации о пользователе в таблицу
    cursor.execute(
        "INSERT INTO users (telegram_id, chat_id, first_name, last_name, username, full_name, account_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
        message.from_user.id, message.chat.id, message.from_user.first_name, message.from_user.last_name,
        message.from_user.username, full_name.strip(), account_number.strip())
    conn.commit()

    # Отправка сообщения с приветствием и информацией о пользователе
    await message.answer(f"Добро пожаловать, {full_name}, ваш единый лицевой счет {account_number}")

    # Отправка клавиатуры с кнопками для выбора действия
    await send_action_keyboard(message.chat.id)

    # Сброс состояния
    await state.finish()


@dp.callback_query_handler(lambda c: c.data == 'subscribe')
async def process_callback_subscribe(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Добавление информации о пользователе в таблицу
    cursor.execute("UPDATE users SET chat_id = ? WHERE telegram_id = ?", callback_query.message.chat.id,
                   callback_query.from_user.id)
    conn.commit()

    await bot.send_message(callback_query.from_user.id,
                           "Вы подписались на ежемесячные уведомления о внесении показателей счетчиков")


@dp.callback_query_handler(lambda c: c.data == 'register_meter')
async def process_callback_register_meter(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Создание кнопок
    button1 = InlineKeyboardButton("Холодная вода", callback_data="register_meter_cold")
    button2 = InlineKeyboardButton("Горячая вода", callback_data="register_meter_hot")

    # Создание клавиатуры
    keyboard = InlineKeyboardMarkup()
    keyboard.add(button1)
    keyboard.add(button2)

    # Отправка сообщения с клавиатурой
    await bot.send_message(callback_query.from_user.id, "Выберите тип воды:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'register_meter_cold')
async def process_callback_register_meter_cold(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    # Сохранение типа прибора учета
    await MeterForm.meter_type.set()
    await state.update_data(meter_type='cold')

    # Отправка сообщения с запросом серийного номера
    await bot.send_message(callback_query.from_user.id, "Введите серийный номер прибора учета:")
    await MeterForm.serial_number.set()


@dp.callback_query_handler(lambda c: c.data == 'register_meter_hot')
async def process_callback_register_meter_hot(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)

    # Сохранение типа прибора учета
    await MeterForm.meter_type.set()
    await state.update_data(meter_type='hot')

    # Отправка сообщения с запросом серийного номера
    await bot.send_message(callback_query.from_user.id, "Введите серийный номер прибора учета:")
    await MeterForm.serial_number.set()


@dp.message_handler(state=MeterForm.serial_number)
async def process_serial_number(message: types.Message, state: FSMContext):
    # Сохранение серийного номера прибора учета
    await state.update_data(serial_number=message.text)

    # Отправка сообщения с запросом расположения прибора учета
    await message.answer("Введите расположение прибора учета:")

    # Смена состояния на ожидание ввода расположения прибора учета
    await MeterForm.next()


@dp.message_handler(state=MeterForm.location)
async def process_location(message: types.Message, state: FSMContext):
    # Получение данных из состояния
    data = await state.get_data()
    meter_type = data.get('meter_type')
    serial_number = data.get('serial_number')
    location = message.text

    # Добавление записи в таблицу приборов учета
    cursor.execute(
        "INSERT INTO meters (user_id, type, serial_number, location) VALUES ((SELECT id FROM users WHERE telegram_id = ?), ?, ?, ?)",
        message.from_user.id, meter_type, serial_number, location)
    conn.commit()

    # Отправка сообщения об успешной регистрации прибора учета

    await message.answer(
        f"Прибор учета {meter_type} зарегистрирован: серийный номер {serial_number}, расположение {location}")

    # Сброс состояния
    await state.finish()


selected_counter_id = None


@dp.callback_query_handler(lambda c: c.data.startswith('select_counter:'))
async def process_callback_select_counter(callback_query: types.CallbackQuery):
    global selected_counter_id
    print(callback_query.data)
    await bot.answer_callback_query(callback_query.id)

    # Получение выбранного прибора учета из данных callback
    counter_id = callback_query.data.split(':')[1]

    # Сохранение выбранного прибора учета в глобальную переменную
    selected_counter_id = counter_id

    # Отправка сообщения с запросом показания счетчика
    await bot.send_message(callback_query.from_user.id, "Введите показание счетчика:")


@dp.callback_query_handler(lambda c: c.data == 'add_counter_value')
async def process_callback_add_counter_value(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Выборка информации о приборах учета пользователя из таблицы
    cursor.execute(
        "SELECT id, type, meter_type FROM meters WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)",
        callback_query.from_user.id)
    rows = cursor.fetchall()

    # Формирование текста сообщения
    text = "Выберите прибор учета:\n"

    # Создание кнопок для выбора прибора учета
    buttons = []
    for row in rows:
        counter_id = row[0]
        counter_type = row[1]
        meter_type = row[2]
        button_text = f"{counter_id}: {counter_type} ({meter_type})"
        button_callback_data = f"select_counter:{counter_id}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=button_callback_data))

        # Вывод значения callback_data для проверки
        print(f"Button callback_data: {button_callback_data}")

    # Создание клавиатуры с кнопками
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)

    # Отправка сообщения с выбором прибора учета
    await bot.send_message(callback_query.from_user.id, text, reply_markup=keyboard)


@dp.message_handler()
async def process_counter_value(message: types.Message):
    global selected_counter_id

    # Получение значения счетчика из сообщения
    value = message.text

    # Добавление записи в таблицу показателей счетчиков
    cursor.execute(
        "INSERT INTO counter_values (user_id, counter_id, value) VALUES ((SELECT id FROM users WHERE telegram_id = ?), ?, ?)",
        message.from_user.id, selected_counter_id, value)
    conn.commit()

    # Отправка сообщения об успешном добавлении показания счетчика
    await message.answer(f"Значение счетчика {selected_counter_id} добавлено: {value}")

    # Сброс значения глобальной переменной
    selected_counter_id = None


@dp.callback_query_handler(lambda c: c.data == 'calculate_payment')
async def process_callback_calculate_payment(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Выборка информации о показателях счетчиков из таблицы
    cursor.execute(
        "SELECT m.meter_type, SUM(cv.value) FROM counter_values cv JOIN meters m ON cv.counter_id = m.id WHERE cv.user_id = (SELECT id FROM users WHERE telegram_id = ?) GROUP BY m.meter_type",
        callback_query.from_user.id)
    rows = cursor.fetchall()

    # Расчет платежей
    total_cold_water_usage = 0
    total_hot_water_usage = 0
    for row in rows:
        meter_type = row[0]
        total_usage = row[1]
        if meter_type == 'Холодная вода':
            total_cold_water_usage += total_usage
            total_payment = total_usage * 45
            await bot.send_message(callback_query.from_user.id,
                                   f"Сумма к оплате за холодную воду: {total_payment} рублей")
        elif meter_type == 'Горячая вода':
            total_hot_water_usage += total_usage
            total_payment = total_usage * 55
            await bot.send_message(callback_query.from_user.id,
                                   f"Сумма к оплате за горячую воду: {total_payment} рублей")

    # Расчет платежа за сточные воды
    total_sewage_payment = (total_cold_water_usage + total_hot_water_usage) * 35
    await bot.send_message(callback_query.from_user.id,
                           f"Сумма к оплате за сточные воды: {total_sewage_payment} рублей")


if __name__ == '__main__':
    executor.start_polling(dp)

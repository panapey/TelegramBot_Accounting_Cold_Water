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
bot = Bot(token="YOUR_BOT_TOKEN")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Подключение к базе данных
conn = pyodbc.connect("DRIVER={ODBC Driver 17 for SQL Server};"
                      "SERVER=YOUR_SERVER;"
                      "DATABASE=botdb;"
                      "Trusted_Connection=yes;")
cursor = conn.cursor()

meter_type_translation = {'cold': 'холодная вода', 'hot': 'горячая вода'}


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
    button3 = InlineKeyboardButton("Удалить прибор учета", callback_data="delete_counter")
    button4 = InlineKeyboardButton("Вывести приборы учета", callback_data="display_counters")
    button5 = InlineKeyboardButton("Добавить показание счетчика", callback_data="add_counter_value")
    button6 = InlineKeyboardButton("Рассчитать платеж", callback_data="calculate_payment")

    # Создание клавиатуры
    keyboard = InlineKeyboardMarkup()
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)
    keyboard.add(button4)
    keyboard.add(button5)
    keyboard.add(button6)

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
        await send_action_keyboard(message.chat.id)
    else:
        # Отправка сообщения с запросом информации о пользователе
        await message.answer("Пожалуйста, введите ваше ФИО и единый лицевой счет в формате:\nФИО;Номер лицевого счета")

        # Сохранение состояния ожидания ввода информации о пользователе
        await Form.full_name.set()


@dp.message_handler(state=Form.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    # Разделение введенных данных на ФИО и номер лицевого счета
    user_data = message.text.split(';')
    full_name = user_data[0]
    account_number = user_data[1]

    # Проверка длины номера единого лицевого счета
    if len(account_number) > 10:
        await message.answer("Номер единого лицевого счета не должен превышать 10 символов")
    else:
        # Сохранение информации о пользователе в базе данных
        cursor.execute(
            "INSERT INTO users (telegram_id, chat_id, first_name, last_name, username, full_name, account_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
            message.from_user.id, message.chat.id, message.from_user.first_name, message.from_user.last_name,
            message.from_user.username, full_name.strip(), account_number.strip())
        conn.commit()

        # Отправка сообщения с приветствием и информацией о пользователе
        await message.answer(f"Добро пожаловать, {full_name}, ваш единый лицевой счет {account_number}")
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

    # Словарь с переводом для meter_type
    meter_type_translation_ = {'cold': 'холодной воды', 'hot': 'горячей воды'}

    # Отправка сообщения об успешной регистрации прибора учета
    await message.answer(
        f"Прибор учета {meter_type_translation_[meter_type]} зарегистрирован: серийный номер {serial_number}, расположение {location}")

    # Сброс состояния
    await state.finish()
    await send_action_keyboard(message.chat.id)


@dp.callback_query_handler(lambda c: c.data == 'display_counters')
async def process_callback_display_counters(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Вызов функции для отображения приборов учета
    await display_counters(callback_query.from_user.id)


async def display_counters(user_id: int):
    # Выборка информации о приборах учета пользователя из таблицы
    cursor.execute(
        "SELECT id, type, serial_number, location FROM meters WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?) ORDER BY type",
        (user_id))
    rows = cursor.fetchall()
    print(f"Rows: {rows}")

    # Формирование текста сообщения
    text = "Ваши приборы учета:\n"

    previous_counter_type = None
    for row in rows:
        counter_type = row[1]
        serial_number = row[2]
        location = row[3]

        # Добавление подзаголовка для списка приборов учета текущего типа
        if counter_type != previous_counter_type:
            text += f"\n{meter_type_translation[counter_type]}:\n"

        text += f"- {serial_number}, местоположение '{location}'\n"
        previous_counter_type = counter_type

    # Отправка сообщения с информацией о приборах учета
    await bot.send_message(user_id, text)


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
        "SELECT id, type, serial_number FROM meters WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)",
        callback_query.from_user.id)
    rows = cursor.fetchall()

    # Формирование текста сообщения
    text = "Выберите прибор учета:\n"

    # Создание кнопок для выбора прибора учета
    buttons = []
    for row in rows:
        counter_id = row[0]
        counter_type = row[1]
        serial_number = row[2]
        button_text = f"{serial_number}: {meter_type_translation[counter_type]}"
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

    # Get the serial number of the selected counter
    cursor.execute("SELECT serial_number FROM meters WHERE id = ?", (selected_counter_id,))
    serial_number = cursor.fetchone()[0]

    # Send the message with the serial number
    await message.answer(f"Значение счетчика {serial_number} добавлено: {value}")

    # Сброс значения глобальной переменной
    selected_counter_id = None
    await send_action_keyboard(message.chat.id)


@dp.callback_query_handler(lambda c: c.data == 'calculate_payment')
async def process_callback_calculate_payment(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Выборка информации о зарегистрированных счетчиках
    cursor.execute(
        "SELECT m.id, m.type, m.serial_number FROM meters m WHERE m.user_id = (SELECT id FROM users WHERE telegram_id = ?)",
        callback_query.from_user.id)
    rows = cursor.fetchall()

    # Создание кнопок для выбора счетчика
    buttons = []
    for row in rows:
        meter_id = row[0]
        meter_type = row[1]
        serial_number = row[2]
        button_text = f"{serial_number}: {meter_type_translation[meter_type]}"
        if meter_type:
            button = InlineKeyboardButton(button_text, callback_data=f'meter_{meter_id}')
            buttons.append(button)

    # Создание кнопки для расчета оплаты сточных вод
    sewage_button = InlineKeyboardButton('Расчёт платы сточных вод', callback_data='sewage_payment')

    # Создание клавиатуры
    keyboard = InlineKeyboardMarkup()
    keyboard.add(*buttons)
    keyboard.add(sewage_button)

    # Отправка сообщения с клавиатурой
    await bot.send_message(callback_query.from_user.id, 'Выберите счетчик или рассчитайте оплату сточных вод:',
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('meter_'))
async def process_callback_meter(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Получение идентификатора счетчика из данных callback
    meter_id = int(callback_query.data.split('_')[1])

    # Выборка информации о показателях счетчика из таблицы
    cursor.execute(
        "SELECT TOP 2 m.type, cv.value FROM counter_values cv JOIN meters m ON cv.counter_id = m.id WHERE cv.user_id = (SELECT id FROM users WHERE telegram_id = ?) AND cv.counter_id = ? ORDER BY cv.timestamp DESC",
        callback_query.from_user.id, meter_id)
    rows = cursor.fetchall()

    # Расчет платежа
    if len(rows) > 0:
        meter_type = rows[0][0]
        usage = rows[0][1]
        if len(rows) > 1:
            usage -= rows[1][1]
        if meter_type == 'cold':
            price_per_unit = 45
            total_payment = usage * price_per_unit
            await bot.send_message(callback_query.from_user.id,
                                   f"Показания\n{rows[0][1]}-{(rows[1][1] if len(rows) > 1 else 0)}={usage} м3\nНачисление по счетчику\n{usage} м3 * {price_per_unit} рублей = {total_payment} рублей\nИтого к оплате\n{total_payment} рублей")

        elif meter_type == 'hot':
            price_per_unit = 55
            total_payment = usage * price_per_unit
            await bot.send_message(callback_query.from_user.id,
                                   f"Показания\n{rows[0][1]}-{(rows[1][1] if len(rows) > 1 else 0)}={usage} м3\nНачисление по счетчику\n{usage} м3 * {price_per_unit} рублей = {total_payment} рублей\nИтого к оплате\n{total_payment} рублей")
    else:
        await bot.send_message(callback_query.from_user.id,
                               f"Нет показаний для расчета оплаты")


@dp.callback_query_handler(lambda c: c.data == 'sewage_payment')
async def process_callback_sewage_payment(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Выборка информации о показателях счетчиков из таблицы
    cursor.execute(
        "SELECT m.id, cv.value FROM counter_values cv JOIN meters m ON cv.counter_id = m.id WHERE cv.user_id = (SELECT id FROM users WHERE telegram_id = ?) ORDER BY cv.timestamp DESC",
        callback_query.from_user.id)
    rows = cursor.fetchall()

    # Расчет общего использования
    usage_by_meter = {}
    for row in rows:
        meter_id = row[0]
        value = row[1]
        if meter_id not in usage_by_meter:
            usage_by_meter[meter_id] = value
        else:
            usage_by_meter[meter_id] -= value

    total_usage = sum(usage_by_meter.values())
    price_per_unit = 35
    total_sewage_payment = total_usage * price_per_unit
    await bot.send_message(callback_query.from_user.id,
                           f"Показания\n{total_usage} м3\n\nНачисление по счетчику\n{total_usage} м3 * {price_per_unit} рублей = {total_sewage_payment} рублей\n\nИтого к оплате\n{total_sewage_payment} рублей")


@dp.callback_query_handler(lambda c: c.data.startswith('delete_counter:'))
async def process_callback_delete_counter(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Получение выбранного прибора учета из данных callback
    counter_id = int(callback_query.data.split(':')[1])

    # Удаление записей из таблицы показателей счетчиков
    cursor.execute("DELETE FROM counter_values WHERE counter_id = ?", (counter_id,))
    conn.commit()

    # Удаление прибора учета из базы данных
    cursor.execute("DELETE FROM meters WHERE id = ?", (counter_id,))
    conn.commit()

    # Отправка сообщения об успешном удалении прибора учета
    await bot.send_message(callback_query.from_user.id, f"Прибор учета {counter_id} удален")

    # Обновление списка приборов учета
    await display_counters_list(callback_query.from_user.id)


async def display_counters_list(user_id: int):
    # Выборка информации о приборах учета пользователя из таблицы
    cursor.execute(
        "SELECT id, type, serial_number FROM meters WHERE user_id = (SELECT id FROM users WHERE telegram_id = ?)",
        (user_id,))
    rows = cursor.fetchall()

    if not rows:
        # Отправка сообщения об отсутствии приборов учета
        await bot.send_message(user_id, "У вас нет приборов учета")
        return

    # Формирование текста сообщения
    text = "Выберите прибор учета для удаления:\n"

    # Создание кнопок для выбора прибора учета
    buttons = []
    for row in rows:
        counter_id = row[0]
        counter_type = row[1]
        serial_number = row[2]
        button_text = f"{serial_number}: {meter_type_translation[counter_type]}"
        button_callback_data = f"delete_counter:{counter_id}"
        buttons.append(InlineKeyboardButton(button_text, callback_data=button_callback_data))

        # Вывод значения callback_data для проверки
        print(f"Button callback_data: {button_callback_data}")

    # Создание клавиатуры с кнопками
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)

    # Отправка сообщения с выбором прибора учета для удаления
    await bot.send_message(user_id, text, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'delete_counter')
async def process_callback_delete_counter(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Вызов функции для отображения списка приборов учета
    await display_counters_list(callback_query.from_user.id)
    await send_action_keyboard(callback_query.message.chat.id)


if __name__ == '__main__':
    executor.start_polling(dp)

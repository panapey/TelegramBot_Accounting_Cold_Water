TelegramBot_Accounting_Cold_Water

Run in project directory:

pip install -r requirements.txt
В "TgBot.py" нужно указать данные для подключения к БД MSSQL и Токен для Бота

'DRIVER={ODBC Driver 17 for SQL Server};SERVER=YOUR_SERVER\SQLEXPRESS;DATABASE=DATABASE;Trusted_Connection=yes')

bot = Bot(token='YOUR_TOKEN')

Запуск:

python TgBot.py

Остановка:

Ctrl + C

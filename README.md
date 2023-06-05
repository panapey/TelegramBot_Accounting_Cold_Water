TelegramBot_Accounting_Cold_Water

Запустить в директории проекта:
```cpp
pip install -r requirements.txt
```
В "TgBot.py" нужно указать данные для подключения к БД MSSQL и Токен для Бота
```cpp
'DRIVER={ODBC Driver 17 for SQL Server};SERVER=YOUR_SERVER\SQLEXPRESS;DATABASE=DATABASE;Trusted_Connection=yes')
```
```cpp
bot = Bot(token='YOUR_TOKEN')
```
Запуск:
```cpp
python TgBot.py
```
Остановка:
```cpp
Ctrl + C
```

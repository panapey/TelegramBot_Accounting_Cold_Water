# TelegramBot_Accounting_Cold_Water
# ДЛЯ ПРОЕКТА
Вызвать команду в консоли в директории проекта:
```cpp
pip install -r requirements.txt
```
В "TgBot.py" нужно указать данные для подключения к БД MSSQL и Токен для Бота
```cpp
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};SERVER=YOUR_SERVER;DATABASE=YOUR_DATABASE;Trusted_Connection=yes')
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
# ДЛЯ БД

В SSMS создать новый запрос и вызвать в нем код из файла bot.sql
После выполнения скрипта в списке баз данных появится наша бд botdb
```cpp
<img width="163" alt="image" src="https://github.com/panapey/TelegramBot_Accounting_Cold_Water/assets/61374383/c0c48dd1-9d44-4113-a97b-226d30cda32d">
```
далее заходим в раздел свойства
```cpp
<img width="203" alt="image" src="https://github.com/panapey/TelegramBot_Accounting_Cold_Water/assets/61374383/08c59d5f-1b8e-4d19-8b57-828bfb5d1460">
```
дальше нажимаем на просмотр свойств подключения
```cpp
<img width="161" alt="image" src="https://github.com/panapey/TelegramBot_Accounting_Cold_Water/assets/61374383/56f2bdd2-efba-4cc9-8b49-27a41cb4fdd5">
```
в открывшемся окне копируем интересующие нас параметры (они помечены точками сбоку)
```cpp
<img width="377" alt="image" src="https://github.com/panapey/TelegramBot_Accounting_Cold_Water/assets/61374383/4476c31a-6f14-4603-975a-d04e58a7a293">
```

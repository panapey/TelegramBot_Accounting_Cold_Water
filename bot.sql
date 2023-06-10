-- Создание базы данных
CREATE DATABASE botdb;

-- Использование созданной базы данных
USE botdb;

-- Создание таблицы пользователей
CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY,
    telegram_id INT NOT NULL,
    chat_id BIGINT NOT NULL,
    first_name NVARCHAR(255),
    last_name NVARCHAR(255),
    username NVARCHAR(255),
    full_name NVARCHAR(255), -- Добавление поля ФИО
    account_number NVARCHAR(255) -- Добавление поля единый лицевой счет
);

-- Создание таблицы приборов учета
CREATE TABLE meters (
    id INT PRIMARY KEY IDENTITY,
    user_id INT NOT NULL,
    type NVARCHAR(255) NOT NULL,
    serial_number NVARCHAR(255) NOT NULL,
    location NVARCHAR(255) NOT NULL,
    meter_type NVARCHAR(255), -- Добавление поля тип счетчика
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Создание таблицы показателей счетчиков
CREATE TABLE counter_values (
    id INT PRIMARY KEY IDENTITY,
    user_id INT NOT NULL,
    counter_id INT NOT NULL,
    value FLOAT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT GETDATE(),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (counter_id) REFERENCES meters(id)
);

-- Создание таблицы тарифов
CREATE TABLE tariffs (
    id INT PRIMARY KEY IDENTITY,
    type NVARCHAR(255) NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    price_per_unit FLOAT NOT NULL
);

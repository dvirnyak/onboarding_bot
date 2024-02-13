# Onboarding Telegram Bot

### Телеграм бот для обучения новых сотрудников. <br><br>
**Сотрудники** смотрят материалы по блокам продуктов 
и в конце каждого блока проходят тест из нескольких вопросов.

1 | 2 | 3 | 4 | 5
:--:|:--:|:--:|:--:|:--:
![user_screenshot_1.jpg](docs%2Fuser_screenshot_1.jpg)|![user_screenshot_2.jpg](docs%2Fuser_screenshot_2.jpg)|![user_screenshot_3.jpg](docs%2Fuser_screenshot_3.jpg)|![user_screenshot_4.jpg](docs%2Fuser_screenshot_4.jpg)|![user_screenshot_5.jpg](docs%2Fuser_screenshot_5.jpg)

<br>

**Администраторы** могут:
- смотреть статистику по результатам сотрудников
- добавлять / редактировать информацию о продуктах
- добавлять / редактировать вопросы в тестах
- отправлять уведомления выбранным категориям (не прошедшие тест / прошедшие, но с низкими результатами)
- получать и настраивать уведомления (о пройденных тестах, новых регистрациях)

1 |                            2                             | 3
:--:|:--------------------------------------------------------:|:--:
![admin_screenshot_1.jpg](docs%2Fadmin_screenshot_1.jpg)| ![admin_screenshot_2.jpg](docs%2Fadmin_screenshot_2.jpg) |![admin_screenshot_3.jpg](docs%2Fadmin_screenshot_3.jpg)


### Технические детали

- Для хранения данных используется БД и sqlalchemy
- Построение графиков через matplotlib
- Поддержка асинхронности средствами python-telegram-bot & asyncio
- Кэшируются file_id картинок для Телеграма

### Установка и запуск
`git clone https://github.com/dvirnyak/quiz_telegram_bot`

`cd quiz_telegram_bot`

`pip3 install -r requirements.txt`

*Указать в файле `.env`:*
- `DB_PATH` - путь до БД
- `TELEGRAM_TOKEN` - токен Telegram API
- `ADMIN_KEY` - пароль для администратора
- `DEV_KEY` - пароль разработчика

`python3 start_bot.py`
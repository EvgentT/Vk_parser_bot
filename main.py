from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import telebot
import requests
import time
import sqlite3


class Bot:
    def __init__(self):
        self.TOKEN = "BOT_TOKEN"
        self.bot = telebot.TeleBot(self.TOKEN)
        self.offset = 0
        self.con = sqlite3.connect("base.db", check_same_thread=False)
        self.cur = self.con.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Link(
                                    link TEXT NOT NULL,
                                    offset INTEGER
                                    )
                                    """)
        self.cur.execute("""CREATE TABLE IF NOT EXISTS ID(
                                           id INTEGER
                                           )
                                           """)

        self.link = [line[0] for line in self.con.execute("""select link
                    from Link """).fetchall()]
        self.wall = [line[0] for line in self.con.execute("""select id
                    from ID """).fetchall()]

        @self.bot.message_handler(commands=["help", "start"])
        def send_message(message):
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = KeyboardButton("Добавить ➕")
            btn2 = KeyboardButton("Список")
            markup.add(btn1, btn2)
            self.bot.send_message(message.chat.id, "Я Vk_parser бот, отправь мне ссылку на сообществ)",reply_markup=markup)

        @self.bot.message_handler(content_types=['text'])
        def echo_message(message):
                self.id = message.chat.id
                if message.text == "Готово":
                    self.gotovo(message)

                elif message.text == "Добавить ➕":
                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = KeyboardButton("Готово")
                    back = KeyboardButton("Главное меню")
                    markup.add(btn1,  back)
                    self.bot.send_message(message.chat.id, "Отправьте мне ссылку на сообществ)",
                                          reply_markup=markup)

                if message.text[:15] == "https://vk.com/":
                    if message.text[15:] not in self.link:
                        self.cur.execute("INSERT INTO Link(link) VALUES (?)",(message.text[15:],))
                        self.con.commit()
                        self.link = self.base_read()
                        self.bot.send_message(message.chat.id, "Добавлено!")
                    else:
                        self.bot.send_message(message.chat.id, "Эту группу уже добавили!)")


                elif message.text == "Список":
                    self.bot.send_message(message.chat.id, "Удалить ❌",
                                          reply_markup=inline_keyboard())


                elif message.text == "Главное меню" :
                    markup = ReplyKeyboardMarkup(resize_keyboard=True)
                    btn1 = KeyboardButton("Добавить ➕")
                    btn2 = KeyboardButton("Список")
                    markup.add(btn1, btn2)
                    self.bot.send_message(message.chat.id, "Меню",
                                      reply_markup=markup)

        @staticmethod
        def inline_keyboard():
            options = [line[0] for line in self.con.execute("""select link
                                            from Link """).fetchall()]
            keyboard = InlineKeyboardMarkup(row_width=2)
            buttons = [InlineKeyboardButton(s, callback_data=s) for s in options]
            keyboard.add(*buttons)
            return keyboard

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            self.cur.execute("DELETE from Link where link = (?)", (call.data,))
            self.con.commit()
            self.bot.delete_message(call.message.chat.id,
                                    call.message.message_id)
            self.link = self.base_read()
            self.bot.send_message(self.id, "Удалить ❌",
                                  reply_markup=inline_keyboard())

    def run(self):
        self.bot.infinity_polling()

    def response(self):
        self.argv = 0
        access_token = "access_token"
        for domain in self.link:
            params = {
                "access_token": access_token,
                "domain": domain,
                "count": 50,
                "offset" : self.offset,
                "v": 5.199
            }
            response = requests.get("https://api.vk.com/method/wall.get", params=params)
            response_name = requests.get("https://api.vk.com/method/groups.getById", params={
                "access_token": access_token,
                "group_id": domain,
                "v": 5.199
            })
            name = response_name.json()["response"]["groups"][0]["name"]
            data = response.json()["response"]["items"]
            for i in data:
                if i["id"] not in self.wall:
                    self.cur.execute("INSERT INTO ID(id) VALUES (?)", (i["id"],))
                    self.con.commit()
                    self.wall = self.wall_base_read()
                    for j in i["attachments"]:
                        if j["type"] == "photo":
                                self.bot.send_document(self.id, j["photo"]["sizes"][-1]["url"])
                        elif j["type"] == "video":
                            self.bot.send_message(self.id, f"https://vk.com/video{j['video']['owner_id']}_{j['video']['id']}" )
                    if len(i["text"])>1:
                        self.bot.send_message(self.id, f"{name}\n{i['text']}\n{datetime.utcfromtimestamp(int(i['date'])).strftime('%Y.%m.%d %H:%M:%S')}")
                    else:
                        self.bot.send_message(self.id, f"{name}\n{datetime.utcfromtimestamp(int(i['date'])).strftime('%Y.%m.%d %H:%M:%S')}")

                    time.sleep(2)
    def check_news(self):
        while True:
            self.response()
            self.wall = self.wall_base_read()
            if self.offset < 500:
                self.offset += 100
            elif self.offset >= 500:
                self.offset = 0
            time.sleep(900)


    def base_read(self):
        return [line[0] for line in self.con.execute("""select link
                                            from Link """).fetchall()]

    def wall_base_read(self):
        return [line[0] for line in self.con.execute("""select id
                    from ID """).fetchall()]

    def gotovo(self, message):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = KeyboardButton("Добавить ➕")
        btn2 = KeyboardButton("Список")
        markup.add(btn1, btn2)
        self.bot.send_message(message.chat.id, "Спасибо!",
                              reply_markup=markup)
        self.check_news()


bot = Bot()

if __name__ == '__main__':
    bot.run()


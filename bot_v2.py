import requests
import telebot
from telebot import types

import config
import states

bot = telebot.TeleBot(config.TOKEN)



def greetings_msg(user_name):
    return 'Йо {}, чікі-пау це бот <b>Мапи Реновації</b>.\nЩоб добавити нову тисни /add'.format(user_name)


ask_data_msg = 'Щоб добавити нову заброшку, потрібно зробити кілька простих кроків. Мені необхідна локація а також фото крошки заброшки'
ask_location_msg = 'Чекаю на локацію. Можна надіслати посилання на гугл карти або вказати адресу у вигляді: вулиця Майдан Незалежності 1.\nПісля завершення тисни /next'
ask_photo_msg = 'Завантаж фотографії.\nІ переходь до наступного кроку /next'
ask_details_msg = 'Також можна залишити додаткову інформацію.\nІ натискай /end'
thanks_msg = 'Дякую! Твоя заброшка збережена\n'
again_msg = 'Щоб додати ще заброшку, тисни /add'


def is_on_location_step(message):
    return stateMap.get(message.chat.id, -1) == states.LOCATION

def is_on_photo_step(message):
    return stateMap.get(message.chat.id, -1) == states.PHOTO

def is_on_comment_step(message):
    return stateMap.get(message.chat.id, -1) == states.COMMENT

@bot.message_handler(commands=['start'])
def start_command(message):
    clear_chat_data(message.chat.id)

    stateMap[message.chat.id] = states.START

    bot.send_sticker(message.chat.id, open('static/hug.jpg', 'rb'))
    bot.send_message(message.chat.id, greetings_msg(message.from_user.first_name), parse_mode='html')

@bot.message_handler(commands=['add'])
#@bot.message_handler(func=lambda message: message.text == 'Добавити нову заброшку', content_types=['text'])
def add_new_zabroshka(message):
    stateMap[message.chat.id] = states.LOCATION
    bot.send_message(message.chat.id, ask_data_msg)
    bot.send_message(message.chat.id, ask_location_msg)

@bot.message_handler(func=is_on_location_step, commands=['next'])
#@bot.message_handler(func=lambda message: is_on_location_step(message) and message.text == 'Наступний крок', content_types=['text'])
def go_to_photo_state(message):
    stateMap[message.chat.id] = states.PHOTO
    bot.send_message(message.chat.id, ask_photo_msg)

@bot.message_handler(func=is_on_location_step, content_types=['text'])
def add_location(message):
    location.setdefault(message.chat.id, []).append(message.text)

@bot.message_handler(func=is_on_photo_step, commands=['next'])
#@bot.message_handler(func=lambda message: is_on_photo_step(message) and message.text == 'Наступний крок', content_types=['text'])
def go_to_comment_state(message):
    stateMap[message.chat.id] = states.COMMENT
    bot.send_message(message.chat.id, ask_details_msg)

@bot.message_handler(func=is_on_photo_step, content_types=['photo', 'document'])
def get_photos(message):
    photoInfo = None
    if message.photo:
        photoInfo = bot.get_file(message.photo[-1].file_id)
    elif message.document:
        photoInfo = bot.get_file(message.document.file_id)

    if photoInfo:
        photos.setdefault(message.chat.id, []).append(photoInfo.file_path)

@bot.message_handler(commands=['end'])
#@bot.message_handler(func=lambda message: message.text == 'Завершити', content_types=['text'])
def finish(message):
    save_chat_data(message.chat.id)
    clear_chat_data(message.chat.id)

    bot.send_message(message.chat.id, thanks_msg)
    bot.send_message(message.chat.id, again_msg)

@bot.message_handler(func=is_on_comment_step, content_types=['text'])
def add_comment(message):
    comment.setdefault(message.chat.id, []).append(message.text)

def download_photos(chat_id):
    for photo_path in photos.get(chat_id, []):
        response = requests.get('https://api.telegram.org/file/bot{}/{}'.format(config.TOKEN, photo_path))
        if response.status_code != 200:
            return
        
        file = open(photo_path.split('/')[-1], 'wb') #can be save to s3 with hash
        file.write(response.content)
        file.close()

def save_chat_data(char_id):
    download_photos(char_id)
    # save location, comment and photo

def clear_chat_data(char_id):
    location.pop(char_id, None)
    comment.pop(char_id, None)
    photos.pop(char_id, None)

if __name__ == "__main__":
    photos, location, comment = {}, {}, {}
    stateMap = {}

    bot.polling(none_stop=True)



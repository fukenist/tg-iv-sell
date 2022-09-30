import telebot
from telebot import types
from pymongo import MongoClient
import time
from telegram import ParseMode
import requests
import json
import os


#Первое, что нужно сделать это импортировать нашу библиотеку и подключить токен бота:
token = 'xf555555555555:xxxxxxxxxxxxxxxxxxxxxxxxx'
bot = telebot.TeleBot(token)
PORT = int(os.environ.get('PORT', 5000))
#connect to MongoDB
cluster = MongoClient("mongodb+srv://kulklao:i14567q@5656sdsd.qa1ye.mongodb.net/?retryWrites=true&w=majority&ssl=true")

db = cluster['db_mng']
collection = db['sobral']

model = '';
ram = '';
state = '';
photo_list = []
price_list = {'iphone se' : {'16' : 3000, '32' : 4000, '64' : 4500, '128' : 5000}, 'iphone 6s' : {'16' : 4000, '32' : 4500, '64' : 5500, '128' : 6000}, 'iphone 6s plus' : {'16' : 4500, '32' : 5000, '64' : 5500, '128' : 6500}, 'iphone 7' : {'32' : 6000, '128' : 7500, '256' : 8500}, 'iphone 7 plus' : {'32' : 10000, '128' :12000, '256' :13500}, 'iphone 8' : {'64' : 11000, '128' :12500, '256' :13500}, 'iphone 8 plus' : {'64' : 14000, '128' :16000, '256' :18000}, 'iphone se 2020' : {'32' : 15000, '128' :16500, '256' :17500}, 'iphone se 2022' : {'32' : 17000, '128' :18500, '256' :19000}, 'iphone x' : {'64' : 17000, '256' :19000}, 'iphone xs' : {'64' : 19000, '256' :22000}, 'iphone xr' : {'64' : 19000, '128' : 21000, '256' :23000}, 'iphone xs max' : {'64' : 24000, '256' :26000}, 'iphone 11' : {'64' : 26000, '128' : 28000, '256' : 30000}, 'iphone 11 pro' : {'64' : 33000, '256' : 36000}, 'iphone 11 pro max' : {'64' : 35000, '256' :38000}, 'iphone 12 mini' : {'64' : 30000, '128' : 33000,'256' : 35000}, 'iphone 12' : {'64' : 35000, '128' : 37000, '256' : 38000}, 'iphone 12 pro' : {'128' : 48000, '256' : 52000,'512' : 55000}, 'iphone 12 pro max' : {'128' : 52000, '256' : 55000,'512' : 57000}, 'iphone 13 mini' : {'128' : 38000, '256' : 40000,'512' : 42000}, 'iphone 13' : {'128' : 45000, '256' : 47000,'512' : 49000}, 'iphone 13 pro' : {'128' : 50000, '256' : 53000,'512' : 55000, '1024' : 58000}, 'iphone 13 pro max' : {'128' : 53000, '256' : 55000,'512' : 57000, '1024' : 60000}}

@bot.message_handler(commands=['start'])

def startup(message):
    if collection.find_one({"_id" : message.from_user.id}) is None:
        collection.insert_one({"_id" : message.from_user.id})
    bot.send_message(message.from_user.id, "<b>1. </b>Какая модель? <b>iphone</b> обязательно напиши" + '\n' + 'Например: iphone 10', parse_mode="HTML")
    bot.register_next_step_handler(message, get_model)


def get_model(message):
	model = message.text.lower()
	if model not in price_list:
		bot.send_message(message.from_user.id, 'Такой модели iphone ещё свет не видел. Попробуй снова. Нажми /start')
		bot.register_next_step_handler(message, startup)
	else:
		collection.update_one({
			"_id" : message.from_user.id},{ '$set' : {
			"model" : model
			}})
		bot.send_message(message.from_user.id, '<b>2. </b>Какая память? (только цифрами)', parse_mode="HTML")
		bot.register_next_step_handler(message, get_ram)

def get_ram(message):	
	cell = collection.find_one({"_id" : message.from_user.id})
	try:
		ram = int(message.text)
		collection.update_one({
			"_id" : message.from_user.id},{ '$set' : {
			"ram" : ram
			}})
		if str(ram) not in price_list[cell['model']]:
			bot.send_message(message.from_user.id, 'Эта модель не выпускается с такой памятью')
			bot.send_message(message.from_user.id, '<b>2. </b>Какая память? (только цифрами)', parse_mode="HTML")
			bot.register_next_step_handler(message, get_ram)
		else:
			bot.send_message(message.from_user.id, '<b>3. </b>Скинь фото телефона. По одному в сообщении. Если нужно отправить несколько - шлите несколько сообщений. После отправки всех фото пишите /stop', parse_mode="HTML")
			bot.register_next_step_handler(message, get_photo)
	except Exception:
		bot.send_message(message.from_user.id, 'Цифрами только')
		bot.send_message(message.from_user.id, '<b>2. </b>Какая память? (только цифрами)', parse_mode="HTML")
		bot.register_next_step_handler(message, get_ram)
	

@bot.message_handler(content_types=['photo'])

def get_photo(message):
	try:
		photo = message.photo[-1].file_id
		if photo not in photo_list:
			photo_list.append(photo)
	except Exception:
		bot.send_message(message.from_user.id, 'Можно и без фото. Жми /stop')
		bot.register_next_step_handler(message, image_received)
	print(photo_list)



@bot.message_handler(commands=['stop'])
def image_received(message):
	if photo_list:
		bot.send_message(message.from_user.id, 'Фото получено')
		for photo in photo_list:
			file_photo = requests.get('https://api.telegram.org/bot' + token + '/getFile?file_id=' + photo)
			json_file = json.loads(file_photo.content.decode('utf-8'))
			collection.update_one({"_id" : message.from_user.id}, {'$set' : {
				photo : json_file['result']['file_path']
				}})
		
	markup = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard = True, one_time_keyboard=True)
	markup.add("Да", "Нет")
	bot.send_message(message.from_user.id, '<b>3. </b>Ростест?', parse_mode="HTML", reply_markup=markup)
	bot.register_next_step_handler(message, get_repair)

#https://api.telegram.org/file/bot<token>/<file_path>

def get_repair(message):
	repair = message.text
	collection.update_one({"_id" : message.from_user.id}, {'$set' : {
		'repair' : repair
		}})
	markup = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard = True, one_time_keyboard=True)
	markup.add("Да", "Нет")
	bot.send_message(message.from_user.id, '<b>3. </b>Ремонт?', parse_mode="HTML", reply_markup=markup)
	bot.register_next_step_handler(message, get_rostest)

def get_rostest(message):
	rostest = message.text
	collection.update_one({"_id" : message.from_user.id}, {'$set' : {
		'rostest' : rostest
		}})
	markup = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard = True, one_time_keyboard=True)
	markup.add("1", "2", "3", "4", "5")
	bot.send_message(message.from_user.id, '<b>4. </b>Какое состояние? от 1(плохое) до 5(идеальное)', parse_mode="HTML", reply_markup=markup)
	bot.register_next_step_handler(message, get_state)

def get_state(message):
	
	state = message.text;
	collection.update_one({"_id" : message.from_user.id},{ '$set' : {
		"state" :state
		}})
	bot.send_message(message.from_user.id, '<b>5. </b>Желаемая цена (только цифрами, в рублях)', parse_mode='HTML')
	bot.register_next_step_handler(message, get_wprice)

def get_wprice(message):
	wprice = message.text 
	collection.update_one({"_id" : message.from_user.id}, {"$set" : {
		'wprice' : wprice
		}})


	cell = collection.find_one({"_id" : message.from_user.id})
	question = '<b>Модель: </b>' + cell['model'] + '\n'+ '<b>Память: </b>' + str(cell['ram'])+ '\n'+ "<b>Ростест: </b>" + str(cell['rostest'])+ '\n' + "<b>Состояние: </b>" + cell['state']+ '\n' + "<b>Желаемая цена:  </b>" + cell['wprice'] + '\n' + '<b>Правильно?</>'
	bot.send_message(message.from_user.id, parse_mode="HTML", text=question)
	markup = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard = True, one_time_keyboard=True)
	markup.add("Да", "Нет")
	bot.send_message(message.from_user.id, "Выбери ответ:", reply_markup=markup)
	bot.register_next_step_handler(message, show_price)

def show_price(message):
	result = message.text
	cell = collection.find_one({"_id" : message.from_user.id})
	cell_ram = str(cell['ram'])

	price = price_list[cell['model']][cell_ram]
	if int(cell['state']) == 1 or int(cell['state']) == 2:
		price = int(price) - 2000
	elif int(cell['state']) == 3 or int(cell['state']) == 4:
		price = int(price) - 1000
	if result == 'Да':
		proposal = 'Готовы купить ваш <b>' + cell['model'] + '</b>' + '\n' + 'с памятью <b>' + cell_ram + '</b>' + ' за <b>' + str(price) + '</b>. Устраивает цена?'
		bot.send_message(message.from_user.id, parse_mode='HTML', text=proposal)
		markup = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard=True, one_time_keyboard=True)
		markup.add('Да', 'Нет')
		bot.send_message(message.from_user.id, 'Выбери ответ:', reply_markup=markup)
		bot.register_next_step_handler(message, get_result)
	else:
		bot.send_message(message.from_user.id, 'Давай по новой. Жми /start')
		bot.register_next_step_handler(message, startup)	
	

def get_result(message):
	
	result = message.text

	if result == 'Да':
		bot.send_message(message.from_user.id, 'Записал')
		markup = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard = True, one_time_keyboard=True)
		button = types.KeyboardButton(text="Оставь", request_contact=True)
		markup.add(button)
		bot.send_message(message.chat.id, 'Есть контакт?', reply_markup=markup)
	else:
		bot.send_message(message.from_user.id, 'Не сошлись в цене. Бывает')

@bot.message_handler(content_types='contact')

def contact(message):
	if message.contact is not None:
		print(message.contact)
		bot.send_message(message.from_user.id, 'Есть контакт. Мы вам позвоним!')
		bot.send_message(message.from_user.id, 'Хотите продать ещё один iphone?')
		markup = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard=True, one_time_keyboard=True)
		markup.add('Да', 'Нет')
		bot.send_message(message.from_user.id, 'Выбери ответ:', reply_markup=markup)
		collection.update_many({"_id" : message.from_user.id},{ '$set' : {
			"contact" : message.contact.phone_number,
			"name" : message.contact.first_name,
			"surname" : message.contact.last_name			
			}})
		cell = collection.find_one({"_id" : message.from_user.id})
		result = '<b>Модель: </b>' + cell['model'] + '\n'+ '<b>Память: </b>' + str(cell['ram'])+ '\n'+ "<b>Ростест: </b>" + str(cell['rostest'])+ '\n' + "<b>Состояние: </b>" + cell['state'] + '\n' + "<b>Желаемая цена:  </b>" + cell['wprice'] + '\n' + cell['contact'] + ' ' +cell['name']
		bot.send_message('1207067214', parse_mode='HTML', text=result)
		#bot.send_message('337897610', parse_mode='HTML', text=result)
		bot.register_next_step_handler(message, finish)
		for ph in photo_list:
			print(cell[ph])
			bot.send_photo('1207067214', 'https://api.telegram.org/file/bot' + token +'/'+ cell[ph])
		
			
def finish(message):
	result = message.text
	if result == 'Да':
		bot.send_message(message.from_user.id, 'Пройди опрос по новой. Жми /start')
		bot.register_next_step_handler(message, startup)
	else:
		bot.send_message(message.from_user.id, 'Всего хорошего!')


if __name__ == '__main__':
	bot.polling(none_stop=True, interval=0)


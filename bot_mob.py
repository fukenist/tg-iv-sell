import telebot
from telebot import types
from pymongo import MongoClient
import time
from telegram import ParseMode
import requests
import json



#Первое, что нужно сделать это импортировать нашу библиотеку и подключить токен бота:
token = '5461448473:AAH41_ke8ZqBLzpbZDzX8pptV0JxB0jDpFo'
bot = telebot.TeleBot(token)
#connect to MongoDB
cluster = MongoClient("mongodb+srv://kulklao:i124q@cluster0.qa1ye.mongodb.net/?retryWrites=true&w=majority&ssl=true")

db = cluster['db_mng']
collection = db['sobral']

model = '';
ram = '';
state = '';
photo_list = []
price_list = {'iphone 10' : {'64' : 15000, '256' :20000}, 'iphone 11' : {'64' : 17000, '128' : 20000, '256' : 23000}}

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
	bot.register_next_step_handler(message, get_rostest)

#https://api.telegram.org/file/bot<token>/<file_path>

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
	if result == 'Да':
		proposal = 'Готовы купить ваш <b>' + cell['model'] + '</b>' + '\n' + 'с памятью <b>' + cell_ram + '</b>' + '\n' + 'при условии, что он в идеальном состоянии' + '\n' + 'за <b>' + str(price) + '</b>. Устраивает цена?'
		bot.send_message(message.from_user.id, parse_mode='HTML', text=proposal)
		markup = types.ReplyKeyboardMarkup(row_width = 1, resize_keyboard=True, one_time_keyboard=True)
		markup.add('Да', 'Нет')
		bot.send_message(message.from_user.id, 'Выбери ответ:', reply_markup=markup)
	else:
		bot.send_message(message.from_user.id, 'Давай по новой. Жми /start')	
	bot.register_next_step_handler(message, get_result)

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
		collection.update_many({"_id" : message.from_user.id},{ '$set' : {
			"contact" : message.contact.phone_number,
			"name" : message.contact.first_name,
			"surname" : message.contact.last_name
			
			}})
		cell = collection.find_one({"_id" : message.from_user.id})
		result = '<b>Модель: </b>' + cell['model'] + '\n'+ '<b>Память: </b>' + str(cell['ram'])+ '\n'+ "<b>Ростест: </b>" + str(cell['rostest'])+ '\n' + "<b>Состояние: </b>" + cell['state'] + '\n' + "<b>Желаемая цена:  </b>" + cell['wprice'] + '\n' + cell['contact'] + ' ' +cell['name']
		bot.send_message('1207067214', parse_mode='HTML', text=result)
		for ph in photo_list:
			print(cell[ph])
			bot.send_photo('1207067214', 'https://api.telegram.org/file/bot' + token +'/'+ cell[ph])
			
			#337897610

bot.polling(none_stop=True, interval=0)


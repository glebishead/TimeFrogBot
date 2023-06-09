import os
from asyncio import sleep
from json import loads, dump
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from werkzeug.security import generate_password_hash
from data import db_session
from data.users import User
from keybuttonclient import kb_client


def get_messages_text():
	with open('messages.json', 'r', encoding='utf-8') as _file:
		return loads(_file.read())


def get_timetable():
	with open('timetable.json', 'r', encoding='utf-8') as _file:
		return loads(_file.read())


def write_timetable():
	global timetable
	print(f'from write_timetable {timetable}')
	with open('timetable.json', 'w', encoding='utf-8') as _file:
		return dump(timetable, _file)


def bot_typing_decorator(func):
	async def wrapper(update, *args, **kwargs):
		await update.message.chat.send_chat_action('typing')
		await sleep(1)
		return await func(update, *args, **kwargs)
	return wrapper


async def start(update, context):
	global messages_text
	
	await update.message.chat.send_chat_action('choose_sticker')
	await sleep(1)
	with open('static/stickers/sticker.webp', 'rb') as sticker:
		await update.message.reply_sticker(sticker)
	
	await update.message.chat.send_chat_action('typing')
	await sleep(1)
	await update.message.reply_text(f"{messages_text['start1']}"
	                                f"{update.message.chat.first_name}"
	                                f"{messages_text['start2']}", reply_markup=kb_client)
	
	db_sess = db_session.create_session()
	if not db_sess.query(User).filter(User.id == update.message.chat.id).first():
		user = User(id=update.message.chat.id,
		            username=update.message.chat.username)
		db_sess.add(user)
	db_sess.commit()


@bot_typing_decorator
async def add_note(update, context):
	global messages_text, timetable
	
	await update.message.reply_text("Добавил заметку успешно")
	
	db_sess = db_session.create_session()
	if db_sess.query(User).filter(User.id == update.message.chat.id).first():
		text_message = update.message.text.split()
		if str(update.message.chat.id) not in timetable.keys():
			timetable[str(update.message.chat.id)] = {text_message[1]: [text_message[2]]}
		else:
			timetable[str(update.message.chat.id)][text_message[1]] = text_message[2]
	print(f'from add_note {timetable}')
	db_sess.commit()


@bot_typing_decorator
async def change_password(update, context):
	global messages_text
	
	db_sess = db_session.create_session()
	if db_sess.query(User).filter(User.id == update.message.chat.id).first():
		db_sess.query(User).filter(
			User.id == update.message.chat.id
		).first().hashed_password = generate_password_hash(update.message.text.split()[1])
		await update.message.reply_text(messages_text['password_change_success'])
	else:
		await update.message.reply_text(messages_text['password_change_fail'])
	db_sess.commit()


@bot_typing_decorator
async def change_email(update, context):
	db_sess = db_session.create_session()
	if db_sess.query(User).filter(User.id == update.message.chat.id).first():
		db_sess.query(User).filter(
			User.id == update.message.chat.id
		).first().email = update.message.text.split()[1]
		await update.message.reply_text(messages_text['email_change_success'])
	else:
		await update.message.reply_text(messages_text['email_change_fail'])
	db_sess.commit()


@bot_typing_decorator
async def change_name(update, context):
	db_sess = db_session.create_session()
	if db_sess.query(User).filter(User.id == update.message.chat.id).first():
		db_sess.query(User).filter(User.id == update.message.chat.id).first().username = update.message.text.split()[1]
		await update.message.reply_text(messages_text['name_change_success'])
	else:
		await update.message.reply_text(messages_text['name_change_fail'])
	db_sess.commit()


@bot_typing_decorator
async def echo(update, context):
	await update.message.reply_text(update.message.text)


def main():
	# Build application
	application = Application.builder().token(os.getenv('TOKEN')).build()
	
	# Create command handlers
	start_handler = CommandHandler(['start', 'help'], start)
	change_name_handler = CommandHandler('change_name', change_name)
	change_email_handler = CommandHandler('change_email', change_email)
	change_password_handler = CommandHandler('change_password', change_password)
	add_note_handler = CommandHandler('add_note', add_note)
	
	# Create text_handlers
	text_handler = MessageHandler(filters.TEXT, echo)
	
	# Command handlers
	application.add_handler(start_handler)
	application.add_handler(change_name_handler)
	application.add_handler(change_email_handler)
	application.add_handler(change_password_handler)
	application.add_handler(add_note_handler)
	
	# Text handlers
	application.add_handler(text_handler)
	
	# Run application
	application.run_polling(drop_pending_updates=True)


def connect_db():
	try:
		db_session.global_init('db/users.db')
	except Exception as e:
		print(e)


if __name__ == '__main__':
	messages_text = get_messages_text()
	timetable = get_timetable()
	connect_db()
	
	# Start scheduler
	scheduler = AsyncIOScheduler()
	scheduler.add_job(write_timetable, 'interval', seconds=3)
	scheduler.start()
	
	main()

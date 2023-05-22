import os
from asyncio import sleep
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from werkzeug.security import generate_password_hash
from data import db_session
from data.users import User


def bot_typing_decorator(func):
	async def wrapper(update, *args, **kwargs):
		await update.message.chat.send_chat_action('typing')
		await sleep(1)
		return await func(update, *args, **kwargs)
	return wrapper


async def start(update, context):
	await update.message.chat.send_chat_action('choose_sticker')
	await sleep(2)
	with open('static/stickers/sticker.webp', 'rb') as sticker:
		await update.message.reply_sticker(sticker)
	
	await update.message.chat.send_chat_action('typing')
	await sleep(2)
	await update.message.reply_text(f"Привет, {update.message.chat.first_name}. Можешь звать меня TimeЖаб. "
	                                f"Если хочешь, буду напоминать о важных делах. Буду рад помочь)")
	
	db_sess = db_session.create_session()
	if not db_sess.query(User).filter(User.id == update.message.chat.id).first():
		user = User(id=update.message.chat.id,
		            username=update.message.chat.username)
		db_sess.add(user)
	db_sess.commit()


@bot_typing_decorator
async def change_password(update, context):
	db_sess = db_session.create_session()
	if db_sess.query(User).filter(User.id == update.message.chat.id).first():
		db_sess.query(User).filter(
			User.id == update.message.chat.id
		).first().hashed_password = generate_password_hash(update.message.text.split()[1])
		await update.message.reply_text("Пароль изменен успешно!")
	else:
		await update.message.reply_text("Смена пароля прервана. Может быть Вы не зарегистрированы?")
	db_sess.commit()


@bot_typing_decorator
async def change_email(update, context):
	db_sess = db_session.create_session()
	if db_sess.query(User).filter(User.id == update.message.chat.id).first():
		db_sess.query(User).filter(
			User.id == update.message.chat.id
		).first().email = update.message.text.split()[1]
		await update.message.reply_text("Почта изменена успешно")
	else:
		await update.message.reply_text("Смена почты прервана. Может быть Вы не зарегистрированы?")
	db_sess.commit()


@bot_typing_decorator
async def change_name(update, context):
	db_sess = db_session.create_session()
	if db_sess.query(User).filter(User.id == update.message.chat.id).first():
		db_sess.query(User).filter(User.id == update.message.chat.id).first().username = update.message.text.split()[1]
		await update.message.reply_text("Имя изменено успешно!")
	else:
		await update.message.reply_text("Смена имени прервана. Может быть Вы не зарегистрированы?")
	db_sess.commit()


@bot_typing_decorator
async def echo(update, context):
	await update.message.reply_text(update.message.text)


def main():
	# Build application
	application = Application.builder().token(os.getenv('TOKEN')).build()
	
	# Create command handlers
	start_handler = CommandHandler('start', start)
	change_name_handler = CommandHandler('change_name', change_name)
	change_email_handler = CommandHandler('change_email', change_email)
	change_password_handler = CommandHandler('change_password', change_password)
	
	# Create text_handlers
	text_handler = MessageHandler(filters.TEXT, echo)
	
	# Command handlers
	application.add_handler(start_handler)
	application.add_handler(change_name_handler)
	application.add_handler(change_email_handler)
	application.add_handler(change_password_handler)
	
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
	connect_db()
	main()

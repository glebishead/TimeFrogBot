from telegram import KeyboardButton, ReplyKeyboardMarkup

button1 = KeyboardButton('/start')
kb_client = ReplyKeyboardMarkup([[button1]], resize_keyboard=True)

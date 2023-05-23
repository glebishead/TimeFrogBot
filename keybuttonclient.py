from telegram import KeyboardButton, ReplyKeyboardMarkup

b1 = KeyboardButton('/start')
kb_client = ReplyKeyboardMarkup([[b1]], resize_keyboard=True)

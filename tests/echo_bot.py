from bot.bot import Bot
from bot.handler import MessageHandler

TOKEN = "001.1766502784.4288028080:1008894883" #your token here

bot = Bot(token=TOKEN)

bot.send_text(chat_id='AoLN5qJHItuafWVKI1Y', text='1212')

# def message_cb(bot, event):
#     bot.send_text(chat_id=event.from_chat, text=event.text)
#
#
# bot.dispatcher.add_handler(MessageHandler(callback=message_cb))
# bot.start_polling()
# bot.idle()

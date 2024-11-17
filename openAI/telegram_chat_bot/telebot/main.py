from dotenv import load_dotenv
import os
import sys
import openai
from aiogram import Bot, Dispatcher, executor, types

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

class Reference:

    """
        The class to store previous response from openai API
    """
    def __init__(self) -> None:
        self.response = ""


reference = Reference()
model_name = 'gpt-3.5-turbo'

# Initialize Bot and Dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    """
        The handler receives messages with '/start' command
    """
    await message.reply("Hi\nI'm Tele Bot.\n How can I help you?")

@dp.message_handler(commands=['clear'])
async def welcome(message: types.Message):
    """
        The handler receives messages with '/clear' command
    """
    clear_past()
    await message.reply("I've cleared the past conversation and context.")


@dp.message_handler(commands=['help'])
async def helper(message: types.Message):
    """
       The handler to display the help menu
    """    
    help_command = """
        Hi there! I'm a Tele bot. Here are few useful commands:
        /start - to start the conversation
        /clear - to clear the previous conversation and context
        /help - to get the help menu
        Hope this helps!
    """
    await message.reply(help_command)

def clear_past():
    """
        The function clears previous conversation and context
    """    
    reference.response = ""

@dp.message_handler()
async def chatgpt(message: types.Message):
    """
        The handler to process the user's input and generate response using openai API
    """
    print(f'>>> USER: \n\t {message.text}')
    response = openai.ChatCompletion.create(
        model = model_name,
        messages = [
            {"role": "assistant", "content": reference.response},
            {"role": "user", "content": message.text}
        ]
    )
    reference.response = response['choices'][0]['message']['content']
    print(f'>>> CHATGPT: \n\t {reference.response}')
    await bot.send_message(chat_id = message.chat.id, text = reference.response)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
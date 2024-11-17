from dotenv import load_dotenv  # Import load_dotenv for reading .env files
import os  # Import OS for environment variable access
import sys  # Import sys for system-specific parameters and functions
import openai  # Import OpenAI API
from aiogram import Bot, Dispatcher, executor, types  # Import aiogram for Telegram bot

load_dotenv()  # Load environment variables from a .env file
openai.api_key = os.getenv('OPENAI_API_KEY')  # Get OpenAI API key from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Get Telegram bot token from environment variables

class Reference:
    """
    The class to store previous response from OpenAI API
    """
    def __init__(self) -> None:
        self.response = ""  # Initialize with an empty response

reference = Reference()  # Create a Reference instance
model_name = 'gpt-3.5-turbo'  # Define the model name

# Initialize Bot and Dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)  # Create a bot instance with the token
dp = Dispatcher(bot)  # Create a Dispatcher instance for the bot

@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    """
    The handler receives messages with '/start' command
    """
    await message.reply("Hi\nI'm Tele Bot.\n How can I help you?")  # Reply with a welcome message

@dp.message_handler(commands=['clear'])
async def clear(message: types.Message):
    """
    The handler receives messages with '/clear' command
    """
    clear_past()  # Clear past conversation
    await message.reply("I've cleared the past conversation and context.")  # Reply with a confirmation

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
    await message.reply(help_command)  # Reply with the help command list

def clear_past():
    """
    The function clears previous conversation and context
    """    
    reference.response = ""  # Reset the stored response

@dp.message_handler()
async def chatgpt(message: types.Message):
    """
    The handler to process the user's input and generate response using OpenAI API
    """
    print(f'>>> USER: \n\t {message.text}')  # Print the user's message
    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[
            {"role": "assistant", "content": reference.response},
            {"role": "user", "content": message.text}
        ]
    )  # Generate response using OpenAI's ChatCompletion API
    reference.response = response['choices'][0]['message']['content']  # Store the response
    print(f'>>> CHATGPT: \n\t {reference.response}')  # Print the response
    await bot.send_message(chat_id=message.chat.id, text=reference.response)  # Send the response to the user

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)  # Start polling for updates

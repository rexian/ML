import openai  # Import the OpenAI library
import os  # Import the OS library for environment variables
from dotenv import load_dotenv  # Import load_dotenv for reading .env files
from flask import Flask, request, jsonify, render_template  # Import Flask and related functions

# Load environment variables from a .env file
load_dotenv()
# Get the OpenAI API key from the environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

# Create a Flask application instance
app = Flask(__name__)

@app.route('/')
def index():
    # Render the index.html template when accessing the root URL
    return render_template('index.html')

@app.route('/generateimages/<prompt>')
def generate(prompt):
    print("prompt:", prompt)  # Print the prompt to the console
    # Generate images based on the prompt using OpenAI's API
    response = openai.Image.create(prompt=prompt, n=5, size="256x256")
    print(response)  # Print the response to the console
    # Return the response as a JSON object
    return jsonify(response)

# Run the Flask application on the local server at port 8080 with debug mode enabled
app.run(host='0.0.0.0', debug=True, port=8080)

from flask import Flask, render_template, request
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return "Running"

if __name__ == '__main__':
    app.run(debug=True, port=5000)

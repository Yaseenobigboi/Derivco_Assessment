# this must be the main entry point - it starts the Flask server and will import all routes later

from flask import Flask

app = Flask(__name__)
app.secret_key = 'mzansibuilds-secret-key'


@app.route('/')
def home():
    return 'MzansiBuilds is running!'


if __name__ == '__main__':
    app.run(debug=True)

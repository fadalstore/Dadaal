from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Dadaal App - Backend Active"

if __name__ == '__main__':
    app.run(debug=True)
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

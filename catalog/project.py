from app import app
from app.login import *
from app.category import *
from app.google import *
from app.user import *


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000, debug=True)

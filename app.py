import os
from app import create_app

env_mode = os.environ.get('FLASK_ENV', 'dev')
app = create_app(env_mode)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


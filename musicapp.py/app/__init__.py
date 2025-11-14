from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Inicializa as extensões
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuração
    app.config['SECRET_KEY'] = 'dev-secret-key-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spotify.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    
    # Inicializa extensões com o app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Importa e registra blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.songs import songs_bp
    from app.routes.playlists import playlists_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(songs_bp)
    app.register_blueprint(playlists_bp)
    
    # Configura user loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Cria pasta de uploads e banco de dados
    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()
    
    return app
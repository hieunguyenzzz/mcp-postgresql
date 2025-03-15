import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/mcp')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
    LLM_API_URL = os.environ.get('LLM_API_URL', '')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://postgres:postgres@db:5432/mcp_test')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Return the appropriate configuration object based on the environment."""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config[config_name] 
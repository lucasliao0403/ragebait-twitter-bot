import configparser
import os
from pathlib import Path

class Config:
    def __init__(self, config_path="config.ini"):
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.create_default_config()
        self.config.read(self.config_path)

    def create_default_config(self):
        self.config['TWITTER'] = {
            'username': 'your_twitter_username',
            'email': 'your_twitter_email',
            'password': 'your_twitter_password'
        }

        self.config['RATE_LIMITS'] = {
            'min_delay_between_requests': '5',
            'max_requests_per_hour': '50',
            'max_posts_per_day': '10',
            'min_post_spacing_minutes': '30'
        }

        with open(self.config_path, 'w') as f:
            self.config.write(f)

    @property
    def twitter_username(self):
        return self.config.get('TWITTER', 'username')

    @property
    def twitter_email(self):
        return self.config.get('TWITTER', 'email')

    @property
    def twitter_password(self):
        return self.config.get('TWITTER', 'password')

    @property
    def min_delay(self):
        return int(self.config.get('RATE_LIMITS', 'min_delay_between_requests'))

    @property
    def max_requests_per_hour(self):
        return int(self.config.get('RATE_LIMITS', 'max_requests_per_hour'))

    @property
    def max_posts_per_day(self):
        return int(self.config.get('RATE_LIMITS', 'max_posts_per_day'))

    @property
    def min_post_spacing_minutes(self):
        return int(self.config.get('RATE_LIMITS', 'min_post_spacing_minutes'))
import os
import re
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

import requests
import simplepush
from bs4.element import Tag
from bs4 import BeautifulSoup

APP_DIR = Path('~/.footy').expanduser()
APP_DIR.mkdir(exist_ok=True)
GAMES_PATH = APP_DIR / 'games.log'
LOG_PATH = APP_DIR / 'check-footy.log'
GAME_TITLE = "7 a side football @ St Thomas'"
URL = 'https://www.openplay.co.uk/booking/class/690'

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(),
    ],
)


class Class:
    def __init__(self, tag: Tag):
        self.tag = tag
        self.title = tag.h3.text
        self.sport, self.location = self.title.split(' @ ')

    def __repr__(self) -> str:
        string = f'{self.title}'
        date = self.date
        if date is not None:
            string = f'{string} on {self.date_string}'
        return string

    @property
    def date(self) -> Optional[datetime]:
        date_line = list(self.tag.stripped_strings)[3]
        pattern = r'^(\w+) (\d+)\w\w (\w+)'
        match = re.match(pattern, date_line)
        if match is None:
            return None
        dw, dm, mo = match.groups()
        this_year = datetime.today().year
        date_string = f'{dw} {dm} {mo} {this_year}'
        date_format = '%a %d %b %Y'
        date = datetime.strptime(date_string, date_format)
        return date

    @property
    def date_string(self):
        date = self.date
        suffix = self.get_day_suffix(date)
        return date.strftime(f'%a %d{suffix} %b')

    def get_day_suffix(self, date: datetime) -> str:
        unit = date.day % 10
        if unit == 1:
            return 'st'
        elif unit == 2:
            return 'nd'
        elif unit == 3:
            return 'rd'
        else:
            return 'th'

    def has_been_notified(self) -> bool:
        log_filepath = APP_DIR / GAMES_PATH
        if not log_filepath.is_file():
            return False
        return str(self) in log_filepath.read_text().splitlines()

    def get_key(self) -> str:
        return get_simplepush_key()

    def notify(self, dry_run: bool = False):
        if self.has_been_notified():
            logging.warning(f'Already notified: {self}')
            return
        logging.info(f'Sending push notification for {self} at {self.now()}')
        if not dry_run:
            simplepush.send(
                self.get_key(),
                self.title,
                self.date_string,
                'Football',
            )
            self.log()

    def log(self):
        log_filepath = APP_DIR / GAMES_PATH
        with log_filepath.open(mode='a') as f:
            f.write(f'Sending push notification at {self.now()}:\n')
            f.write(f'{self}\n\n')

    def now(self) -> datetime:
        return datetime.now().replace(microsecond=0)


class Web:
    def __init__(self, url):
        self.soup = self.get_web_soup(url)
        self.classes = self.get_all_classes()
        self.games = self.get_7_football_games()

    def get_web_soup(self, url: str) -> BeautifulSoup:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    def get_all_classes(self) -> List[Class]:
        classes = [
            Class(tag)
            for tag in self.soup.find_all('div', class_='class-other-details')
        ]
        return classes

    def get_7_football_games(self) -> List[Tag]:
        return [class_ for class_ in self.classes if class_.title == GAME_TITLE]

    def notify(self, dry_run: bool = False):
        if not self.games:
            logging.warning(f'No games found now: {datetime.now()}')
            return
        for game in self.games:
            game.notify(dry_run=dry_run)


def get_simplepush_key() -> str:
    key = os.environ.get('SIMPLEPUSH')
    if key is None:
        raise KeyError('Environment variable "SIMPLEPUSH" not found')
    return key


def main():
    web = Web(URL)
    web.notify()
    return web


if __name__ == "__main__":
    web = main()

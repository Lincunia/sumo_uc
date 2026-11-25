'''
SUMO_UC
Copyright (C) 2026  Universidad Central

This file is part of SUMO_UC.

SUMO_UC is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SUMO_UC is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import gettext
from os import path

DOMAIN = 'messages'
LOCALE_DIR = path.join(
    path.dirname(path.dirname(path.abspath(__file__))),
    'locale'
)


class Translator:
    def __init__(self):
        self.current_lang = 'en'
        self.translation = None

    def setup(self, lang='es'):
        self.current_lang = lang
        gettext.bindtextdomain(DOMAIN, LOCALE_DIR)
        gettext.textdomain(DOMAIN)

        language = gettext.translation(
            DOMAIN,
            localedir=LOCALE_DIR,
            languages=[lang],
        )
        language.install()
        self.translation = language
        return self.translation

    def gettext_str(self, message):
        if self.translation is None:
            return message
        return self.translation.gettext(message)

    def get_language(self):
        return self.current_lang


translator = Translator()

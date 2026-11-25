# SUMO_UC
# Copyright (C) 2026  Universidad Central
# 
# This file is part of SUMO_UC.
# 
# SUMO_UC is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# SUMO_UC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

venv: requirements.txt
	test -d env || python -m venv env
	. env/bin/activate; pip install -r requirements.txt
	touch env/touchfile

run: venv compile_langs
	. env/bin/activate; python3 sumo_uc.py

build: venv compile_langs
	. env/bin/activate; pyinstaller --onefile --add-data "locale:locale" --hidden-import='PIL._tkinter_finder' sumo_uc.py

gen_langs:
	xgettext -d mesages \
		--keyword=gettext_str\
		-o locale/messages.pot \
		$$(ls src/*.py) \
		--from-code=UTF-8
	msginit --input=locale/messages.pot \
        --locale=es_ES.UTF8 \
        --output-file=locale/es/LC_MESSAGES/messages.po \
        --no-translator
	msginit --input=locale/messages.pot \
		--locale=en_US.UTF8 \
        --output-file=locale/en/LC_MESSAGES/messages.po \
        --no-translator

compile_langs:
	msgfmt locale/es/LC_MESSAGES/messages.po \
		-o locale/es/LC_MESSAGES/messages.mo
	msgfmt locale/en/LC_MESSAGES/messages.po \
		-o locale/en/LC_MESSAGES/messages.mo

clean:
	find -iname "*.pyc" -delete
	rm -rf ./build/ ./dist/

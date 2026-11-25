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
from os import environ
from tkinter import Tk, messagebox
from .i18n import translator
from .gui import TkinterWindow


def run():
    translator.setup('en')

    if not environ.get("SUMO_HOME"):
        messagebox.showerror('Error', 'SUMO_HOME variable not found')
        raise EnvironmentError('SUMO_HOME variable not set')

    app_gui = TkinterWindow(Tk())
    app_gui.root.mainloop()

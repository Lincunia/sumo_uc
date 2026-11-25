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
import tkinter as tk

from threading import Thread
from tkinter import ttk
from .tmethods import TkinterMethods
from .i18n import translator


class TkinterWindow:
    def __init__(self, root):
        self.root = root
        self.app_methods = TkinterMethods(self)
        self.translatable_str = []
        ###############################
        # MAIN FRAME
        ###############################
        self.root.title('SUMO Universidad Central -  (post-sim)')
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill='both', expand=1)

        self.sec = tk.Frame(self.main_frame)
        self.sec.pack(fill='x', side='bottom')

        self.my_canvas = tk.Canvas(self.main_frame)
        self.my_canvas.pack(side='left', fill='both', expand=1)

        self.x_scrollbar = tk.Scrollbar(
            self.sec,
            orient='horizontal',
            command=self.my_canvas.xview
        )
        self.x_scrollbar.pack(side='bottom', fill='x')

        self.y_scrollbar = tk.Scrollbar(
            self.main_frame,
            orient='vertical',
            command=self.my_canvas.yview
        )
        self.y_scrollbar.pack(side='right', fill='y')

        self.my_canvas.configure(xscrollcommand=self.x_scrollbar.set)
        self.my_canvas.configure(yscrollcommand=self.y_scrollbar.set)

        self.my_canvas.bind(
            '<Configure>',
            lambda e: self.my_canvas.config(
                scrollregion=self.my_canvas.bbox('all')
            )
        )

        self.second_frame = tk.Frame(self.my_canvas)
        self.my_canvas.create_window(
            (0, 0),
            window=self.second_frame,
            anchor='nw'
        )
        self.root.geometry("850x570")
        ###############################
        # ENTRIES AND CHECKBOXES FRAME
        ###############################
        self.frame_entries = tk.Frame(self.second_frame)
        self.frame_entries.pack(pady=8, padx=8, anchor='w')

        self.lbl_sim_name = tk.Label(self.frame_entries)
        self.lbl_sim_name.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.register_widget(
            self.lbl_sim_name,
            'text',
            translator.gettext_str('Simulation name:')
        )

        self.entry_sim_name = tk.Entry(self.frame_entries)
        self.entry_sim_name.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.entry_sim_name.insert(0, 'simulation')

        self.lbl_sim_steps = tk.Label(self.frame_entries)
        self.lbl_sim_steps.grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.register_widget(
            self.lbl_sim_steps,
            'text',
            translator.gettext_str('Number maximum of steps:')
        )

        self.entry_steps = tk.Entry(self.frame_entries)
        self.entry_steps.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.entry_steps.insert(0, '500')

        self.lbl_interval_steps = tk.Label(self.frame_entries)
        self.lbl_interval_steps.grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.register_widget(
            self.lbl_interval_steps,
            'text',
            translator.gettext_str('Interval steps (seconds):')
        )

        self.entry_interval = tk.Entry(self.frame_entries)
        self.entry_interval.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.entry_interval.insert(0, '10.05')

        self.use_sumo_gui = tk.BooleanVar(value=True)
        self.chkbtn_sumo_gui = tk.Checkbutton(
            self.frame_entries,
            variable=self.use_sumo_gui
        )
        self.chkbtn_sumo_gui.grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.register_widget(
            self.chkbtn_sumo_gui,
            'text',
            translator.gettext_str('Use sumo-gui')
        )

        self.display_chart = tk.BooleanVar(value=True)
        self.chkbtn_display_chart = tk.Checkbutton(
            self.frame_entries,
            variable=self.display_chart
        )
        self.chkbtn_display_chart.grid(row=1, column=2, padx=5, pady=5, sticky='w')
        self.register_widget(
            self.chkbtn_display_chart,
            'text',
            translator.gettext_str('Display charts after finishing')
        )

        self.auto_analize_map = tk.BooleanVar(value=False)
        self.chkbtn_auto_analize_map = tk.Checkbutton(
            self.frame_entries,
            #text='Analize automatically after Web Wizard',
            variable=self.auto_analize_map
        )
        self.chkbtn_auto_analize_map.grid(row=2, column=2, padx=5, pady=5, sticky='w')
        self.register_widget(
            self.chkbtn_auto_analize_map,
            'text',
            translator.gettext_str('Analize automatically after Web Wizard')
        )

        self.lbl_language = tk.Label(self.frame_entries)
        self.lbl_language.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        self.register_widget(
            self.lbl_language,
            'text',
            translator.gettext_str('Language:')
        )

        self.combobox_var = tk.StringVar()
        self.combobox = ttk.Combobox(
            self.frame_entries,
            textvariable=self.combobox_var
        )
        self.combobox.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        self.combobox['values'] = ('en', 'es')
        self.combobox['state'] = 'readonly'
        self.combobox.bind('<<ComboboxSelected>>', self.translate_widgets)
        ###############################
        # BUTTONS AND LOG FRAME
        ###############################
        self.frame_bottom = tk.Frame(self.second_frame)
        self.frame_bottom.pack(pady=8, padx=8, anchor='w', fill='both', expand=True)

        self.frame_chkbox = tk.Frame(self.frame_bottom)
        self.frame_chkbox.grid(row=0, column=0, padx=5, pady=5)

        self.btn_osm = tk.Button(
            self.frame_chkbox,
            command=self.run_oww_thread
        )
        self.btn_osm.grid(row=1, column=0, padx=5, pady=5)
        self.register_widget(
            self.btn_osm,
            'text',
            translator.gettext_str('Create with OSM Web Wizard')
        )

        self.btn_analize = tk.Button(
            self.frame_chkbox,
            command=self.analize_sumocfg_map_thread,
        )
        self.btn_analize.grid(row=2, column=0, padx=5)
        self.register_widget(
            self.btn_analize,
            'text',
            translator.gettext_str('Analize map (.net)')
        )

        self.btn_res = tk.Button(
            self.frame_chkbox,
            command=self.load_results_thread
        )
        self.btn_res.grid(row=3, column=0, padx=5, pady=5)
        self.register_widget(
            self.btn_res,
            'text',
            translator.gettext_str('Select results file')
        )

        self.btn_start_sim = tk.Button(
            self.frame_chkbox,
            command=self.run_sim_thread
        )
        self.btn_start_sim.grid(row=4, column=0, padx=5, pady=5)
        self.register_widget(
            self.btn_start_sim,
            'text',
            translator.gettext_str('Start simulation')
        )

        self.btn_compare_res = tk.Button(
            self.frame_chkbox,
            command=self.compare_res_thread
        )
        self.btn_compare_res.grid(row=5, column=0, padx=5, pady=5)
        self.register_widget(
            self.btn_compare_res,
            'text',
            translator.gettext_str('Compare results')
        )

        self.btn_eval = tk.Button(
            self.frame_chkbox,
            command=self.eval_saved_results_thread
        )
        self.btn_eval.grid(row=6, column=0, padx=5, pady=5)
        self.register_widget(
            self.btn_eval,
            'text',
            translator.gettext_str('Evaluate traffic and\ncrosses (last results)')
        )

        ###############################
        # TEXT OUTPUT
        ###############################
        self.frame_text = tk.Frame(self.frame_bottom)
        self.frame_text.grid(row=0, column=1, columnspan=7, sticky="nsew")

        self.text_output = tk.Text(self.frame_text, wrap='none')

        self.x_text_scrollbar = tk.Scrollbar(
            self.frame_text,
            orient='horizontal',
            command=self.text_output.xview
        )
        self.x_text_scrollbar.pack(side='bottom', fill='x')

        self.y_text_scrollbar = tk.Scrollbar(
            self.frame_text,
            orient='vertical',
            command=self.text_output.yview
        )
        self.y_text_scrollbar.pack(side='right', fill='y')

        self.text_output.pack(side='left', fill='both', expand=True)
        self.text_output.configure(
            yscrollcommand=self.y_text_scrollbar.set,
            xscrollcommand=self.x_text_scrollbar.set
        )
        self.apply_translations()

    def apply_translations(self):
        for widget, attr, msgid in self.translatable_str:
            try:
                widget.config(**{attr: translator.gettext_str(msgid)})
            except tk.TclError:
                pass

    def register_widget(self, widget, attr, msgid):
        self.translatable_str.append((widget, attr, msgid))

    def translate_widgets(self, event=None):
        lang = self.combobox.get()
        translator.setup(lang)
        self.apply_translations()
        self.app_methods.log_str(
            translator.gettext_str(
                '=== LANGUAGE CHANGED TO {lang} ==='
            ).format(lang=lang)
        )

    def run_oww_thread(self):
        self.thread = Thread(target=self.app_methods.run_oww, daemon=True)
        self.thread.start()

    def analize_sumocfg_map_thread(self):
        self.thread = Thread(target=self.app_methods.analize_sumocfg_map, daemon=True)
        self.thread.start()

    def load_results_thread(self):
        self.thread = Thread(target=self.app_methods.load_results, daemon=True)
        self.thread.start()

    def run_sim_thread(self):
        self.thread = Thread(target=self.app_methods.run_sim, daemon=True)
        self.thread.start()

    def compare_res_thread(self):
        self.thread = Thread(target=self.app_methods.compare_res, daemon=True)
        self.thread.start()

    def eval_saved_results_thread(self):
        self.thread = Thread(target=self.app_methods.eval_saved_results, daemon=True)
        self.thread.start()

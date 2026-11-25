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
import glob
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import re
import subprocess
import sys
import threading
import traceback

from datetime import datetime
from sumolib import net
from tkinter import filedialog, messagebox
from . import sim, misc
from .i18n import translator


class TkinterMethods:
    def __init__(self, app_gui):
        self.app_gui = app_gui
        self.data_imported = {}
        # Dataframes
        self.last_df_steps = None
        self.last_df_vehicles = None
        self.last_df_edges = None

    ###############################
    # WEB WIZARD SECTION
    ###############################
    def run_oww(self):
        self.data_imported = self.set_dict_var()

        wizard_path = os.path.join(
            os.environ.get('SUMO_HOME', ''),
            'tools',
            'osmWebWizard.py'
        )
        if not os.path.isfile(wizard_path):
            messagebox.showerror(
                translator.gettext_str('Error'),
                translator.gettext_str('Not found {wizard_path}').format(
                    wizard_path=wizard_path
                )
            )
            return

        proc = getattr(self, 'wizard_proc', None)
        if proc is not None and proc.poll() is None:
            messagebox.showinfo(
                translator.gettext_str('Info'),
                translator.gettext_str('OSM Web Wizard is already open'))
            return

        os.makedirs(misc.MAPS_DIR, exist_ok=True)
        maps_dir = os.path.abspath(misc.MAPS_DIR)
        before = self._find_sumocfgs(maps_dir)

        try:
            self.wizard_proc = subprocess.Popen(
                [sys.executable, wizard_path],
                cwd=maps_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
        except Exception as ex:
            self.log_ex(ex)
            return

        self.app_gui.btn_osm.config(state='disabled')
        self.log_str(
            translator.gettext_str(
                'OSM Web Wizard open. The maps will be saved at: {maps_dir}'
            ).format(maps_dir=maps_dir)
        )
        self.log_str(
            translator.gettext_str(
                'Press "Generate Scenario" in the wizard to create the map'
            )
        )
        threading.Thread(
            target=self._watch_wizard,
            args=(maps_dir, before),
            daemon=True
        ).start()

    @staticmethod
    def _find_sumocfgs(maps_dir):
        return set(glob.glob(
            os.path.join(maps_dir, '**', '*.sumocfg'),
            recursive=True
        ))

    def _watch_wizard(self, maps_dir, before):
        root = self.app_gui.root

        if not misc.has_internet():
            root.after(
                0,
                self.log_str,
                translator.gettext_str(
                    'WARNING: Couldn\'t connect with Overpass (OSM);' +
                    'the wizard might fail while downloading data'
                )
            )

        for line in self.wizard_proc.stdout:
            root.after(
                0,
                self.log_str,
                translator.gettext_str('[wizard] {linestr}').format(
                    linestr=line.rstrip()
                )
            )
        code = self.wizard_proc.wait()
        root.after(0, lambda: self.app_gui.btn_osm.config(state='normal'))

        new = self._find_sumocfgs(maps_dir) - before
        if not new:
            root.after(
                0,
                self.log_str,
                translator.gettext_str(
                    'The wizard ended (code {code}) ' +
                    'without generating any .sumocfg'
                ).format(code=code)
            )
            return

        cfg = max(new, key=os.path.getmtime)
        root.after(
            0,
            self.log_str,
            translator.gettext_str('Map generated: {cfg}').format(cfg=cfg)
        )
        if self.data_imported.get('auto-analize?'):
            root.after(0, lambda: self.analize_sumocfg_map(cfg))

    ###############################
    # SIMULATION SECTION
    ###############################
    def run_sim(self):
        self.data_imported = self.set_dict_files()
        if not bool(self.data_imported):
            return

        if len(self.data_imported['src_path']) != 1:
            self.log_str(
                translator.gettext_str('Choose only one simluation file')
            )
            return

        try:
            self.last_df_steps, self.last_df_vehicles, self.last_df_edges = sim.main(
                self.data_imported,
                self.last_df_steps,
                self.last_df_vehicles,
                self.last_df_edges,
                self.log_str,
                self.save_file
            )
            if self.data_imported['plot-chart?']:
                self.app_gui.root.after(100, lambda: self.plot_analysis_chart())
        except Exception as ex:
            self.log_ex(ex)

    def plot_analysis_chart(self):
        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.plot(
            self.last_df_steps['Step'],
            self.last_df_steps['Active_vehicles'],
            label=translator.gettext_str('Active vehicles'),
            linewidth=2
        )
        ax1.set_xlabel(translator.gettext_str('Step'))
        ax1.set_ylabel(translator.gettext_str('Active vehicles'))
        ax1.grid(True)
        ax2 = ax1.twinx()
        ax2.plot(
            self.last_df_steps['Step'],
            self.last_df_steps['Avg_wait_step'],
            label=translator.gettext_str('Average wait (s)'),
            linewidth=2,
            linestyle='--',
            color='C1'
        )
        ax2.set_ylabel(translator.gettext_str('Mean wait (s)'))
        fig.suptitle(
            translator.gettext_str(
                'Evolution Vehieles vs wait - {sim_name}'
            ).format(sim_name=self.data_imported['sim_name'])
        )
        fig.tight_layout()
        plt.show()

        if not self.last_df_vehicles.empty:
            plt.figure(figsize=(8, 4))
            plt.hist(
                self.last_df_vehicles['final_wait_s'].astype(float).dropna(),
                bins=30
            )
            plt.title(
                translator.gettext_str(
                    'Time of wait distribution per vehicle (final)'
                )
            )
            plt.xlabel(translator.gettext_str('Time wait (s)'))
            plt.ylabel(translator.gettext_str('Amount of vehicles'))
            plt.tight_layout()
            plt.show()

        if not self.last_df_edges.empty:
            top10 = self.last_df_edges.sort_values(
                'congestion_score',
                ascending=False
            ).head(10)
            plt.figure(figsize=(10, 5))
            plt.barh(top10['edge_id'].astype(str), top10['congestion_score'])
            plt.gca().invert_yaxis()
            plt.title(
                translator.gettext_str(
                    'Top 10 edges per congestion_score'
                )
            )
            plt.xlabel(translator.gettext_str('congestion_score'))
            plt.tight_layout()
            plt.show()

    ###############################
    # ANALISIS SECTION
    ###############################
    def analize_sumocfg_map(self):
        self.data_imported = self.set_dict_files()
        if not bool(self.data_imported):
            return

        self.log_str(
            translator.gettext_str(
                'Starting .sumocfg analysis: {src_path}'
            ).format(src_path=self.data_imported['src_path'][0])
        )
        netfile = misc._find_netfile_from_sumocfg(self.data_imported['src_path'][0])
        netf = None
        if netfile:
            netf = net.readNet(netfile)
        if netf is None:
            self.log_str('Invalid netfile')
            return

        os.makedirs(misc.RESULTS_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.splitext(
            os.path.basename(self.data_imported['src_path'][0])
        )[0]
        csv_edges = os.path.join(
            misc.RESULTS_DIR,
            '{base}_edges_info_{timestamp}.csv'.format(
                base=base,
                timestamp=timestamp
            )
        )

        try:
            rows = self.analize_per_edge(netf)
        except Exception as ex:
            self.log_ex(ex)

        df_edges_info = pd.DataFrame(rows)
        df_edges_info.to_csv(csv_edges, index=False)
        self.log_str(
            translator.gettext_str(
                'Map analysis finished. CSV edges: {csv_edges}'
            ).format(csv_edges=csv_edges)
        )
        top10 = df_edges_info.sort_values('length_m', ascending=False).head(10)
        plt.figure(figsize=(10, 5))
        plt.barh(top10['edge_id'].astype(str), top10['length_m'])
        plt.gca().invert_yaxis()
        plt.title(translator.gettext_str('Top 10 edges per length'))
        plt.xlabel(translator.gettext_str('Length (m)'))
        plt.tight_layout()
        plt.show()

    def analize_per_edge(self, netf):
        rows = []
        for edge in netf.getEdges():
            eid = edge.getID()
            length = float(edge.getLength()) if hasattr(edge, 'getLength') else 0.0
            lane_count = edge.getLaneNumber()

            from_node = ''
            to_node = ''

            fn = edge.getFromNode()
            tn = edge.getToNode()
            from_node = fn.getID() if fn is not None else ''
            to_node = tn.getID() if tn is not None else ''
            rows.append({
                'edge_id': eid,
                'length_m': length,
                'lane_count': lane_count,
                'from_node': from_node,
                'to_node': to_node
            })
        return rows

    ###############################
    # RESULTS LOADING SECTION
    ###############################
    def load_results(self):
        selected_files = self.browse_files([('CSV Files', '*.csv')])
        if len(selected_files) != 1:
            self.log_str('Choose only one simluation file')
            return

        file = selected_files[0]
        df = pd.read_csv(file)
        plt.figure(figsize=(10, 5))
        if 'Step' in df.columns and 'Average_speed' in df.columns:
            plt.plot(
                df['Step'],
                df['Average_speed'],
                label=translator.gettext_str('Average speed (m/s)')
            )
        if 'Step' in df.columns and 'Active_vehicles' in df.columns:
            plt.plot(
                df['Step'],
                df['Active_vehicles'],
                label=translator.gettext_str('Active vehicles')
            )
        plt.title(
            translator.gettext_str('Simulation loaded: {base}').format(
                base=os.path.basename(file)
            )
        )
        plt.xlabel(translator.gettext_str('Step'))
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    ###############################
    # COMPARISON SECTION
    ###############################
    def compare_res(self):
        files = self.browse_files([('CSV Files', '*.csv')])
        if len(files) < 2:
            messagebox.showerror(
                translator.gettext_str('Error'),
                translator.gettext_str(
                    'Select at least two CSV files to compare'
                )
            )
            return
        plt.figure(figsize=(10, 5))
        for file in files:
            df = pd.read_csv(file)
            if 'Step' in df.columns and 'Average_speed' in df.columns:
                plt.plot(
                    df['Step'],
                    df['Average_speed'],
                    label=os.path.basename(file)
                )
            else:
                messagebox.showwarning(
                    translator.gettext_str('Warning'),
                    translator.gettext_str(
                        '{file} file does\'t contain the columns' +
                        '(Step/Average_speed)'
                    ).format(file=file)
                )
        plt.title(
            translator.gettext_str(
                'Comparison between simulations (Average speed)'
            )
        )
        plt.xlabel(translator.gettext_str('Step'))
        plt.ylabel(translator.gettext_str('Average speed (m/s)'))
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    ###############################
    # EVALUATION SECTION
    ###############################
    def eval_saved_results(self):
        if self.last_df_steps is None or self.last_df_edges is None or self.last_df_vehicles is None:
            messagebox.showwarning(
                translator.gettext_str('Warning'),
                translator.gettext_str(
                    'No previous results loaded. Run simulation first.'
                )
            )
            return
        global_speed_m_s = self.last_df_steps['Average_speed'].mean()\
            if 'Average_speed' in self.last_df_steps.columns\
            else np.nan
        traffic_class = misc.classify_traffic_speed(global_speed_m_s)
        summary = translator.gettext_str(
            '\nEvaluation (Last results):' +
            '\nTraffic classificatoin: {traffic_class}\n' +
            'Total steps: {len_lds}\n' +
            'Top 5 problematic edges:\n'
        ).format(
            traffic_class=traffic_class,
            len_lds=len(self.last_df_steps)
        )
        top = self.last_df_edges.sort_values(
            'congestion_score',
            ascending=False
        ).head(5)
        summary += top[
            [
                'edge_id',
                'mean_vehicle_number',
                'mean_occupancy',
                'mean_speed',
                'congestion_score'
            ]].to_string(index=False)
        self.log_str(summary)

    ###############################
    # FUNDAMENTAL METHODS SECTION
    ###############################
    def set_dict_var(self):
        steps_amnt_str = self.app_gui.entry_steps.get()
        chk_re = re.match('^\\d*$', steps_amnt_str)
        steps_amnt = int(steps_amnt_str) if chk_re else 0

        interval_str = self.app_gui.entry_interval.get()
        chk_re = re.match('^[-+]?\\d+(\\.\\d+)?$', interval_str)
        steps_interval = float(interval_str) if chk_re else 0.0

        data_dict = {
            'steps_amnt': steps_amnt,
            'steps_interval': steps_interval,
            'auto-analize?': self.app_gui.auto_analize_map.get(),
            'sumo-gui?': self.app_gui.use_sumo_gui.get(),
            'plot-chart?': self.app_gui.display_chart.get()
        }

        self.log_str(translator.gettext_str('Varibles captured:'))
        for key, value in data_dict.items():
            self.log_str(' * {key}: {value}'.format(key=key, value=value))

        return data_dict

    def set_dict_files(self):
        src_path = self.browse_files([('SUMO config', '*.sumocfg')])
        if not src_path:
            messagebox.showerror(
                translator.gettext_str('Error'),
                translator.gettext_str('No .sumocfg file selected')
            )
            return {}

        sim_name = self.app_gui.entry_sim_name.get().strip()
        if not sim_name:
            messagebox.showerror(
                translator.gettext_str('Error'),
                translator.gettext_str('No simulation name set')
            )
            return {}

        data_dict = {
            'src_path': src_path,
            'sim_name': sim_name,
        }

        self.log_str(
            translator.gettext_str('Files defined:')
        )
        for key, value in data_dict.items():
            self.log_str(' * {key}: {value}'.format(key=key, value=value))

        data_dict.update(self.set_dict_var())
        return data_dict

    def browse_files(self, ft):
        filenames = filedialog.askopenfilenames(
            initialdir=os.getcwd(),
            title=translator.gettext_str('Select a File'),
            filetypes=ft
        )
        self.log_str(translator.gettext_str('Files selected:'))
        for file in filenames:
            self.log_str(' * {file}'.format(file=file))
        return list(filenames)

    def ask_for_file(self, ft):
        file_path = filedialog.asksaveasfilename(
            title=translator.gettext_str('Save as'),
            defaultextension='.sumocfg',
            filetypes=ft
        )
        return file_path if file_path else ''

    def save_file(self, file_path, content):
        try:
            with open(file_path, 'w') as file:
                file.write(content)
            self.log_str(
                translator.gettext_str('{file_path} saved').format(
                    file_path=file_path
                )
            )
        except Exception as ex:
            messagebox.showerror(
                translator.gettext_str('Error'),
                translator.gettext_str('Error saving file: {ex}').format(ex=ex)
            )

    def log_str(self, content):
        self.app_gui.text_output.insert(
            'end',
            '{out}\n'.format(out=str(content))
        )

    def log_ex(self, ex):
        self.log_str(
            translator.gettext_str(
                '\n---- TRACEBACK ----\n{tr}\n---- EXCEPTION ----\n{ex_str}'
            ).format(tr=traceback.format_exc(), ex_str=str(ex))
        )

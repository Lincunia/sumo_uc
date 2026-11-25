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
import matplotlib.pyplot as plt
import numpy as np
import sumolib
import os
import traci

from datetime import datetime
from json import dump
from pandas import DataFrame, Series
from sklearn.linear_model import LinearRegression
from . import misc
from .i18n import translator
from .hoard_struct import hs


def build_df_edges(csv_edges_path):
    df_edges = DataFrame(columns=[
        'edge_id',
        'mean_vehicle_number',
        'max_vehicle_number',
        'mean_occupancy',
        'mean_speed',
        'congestion_score'
    ])
    edges_summary = []
    for edge_id in hs.edge_accum_vehicle_number.keys():
        vehnums = hs.edge_accum_vehicle_number[edge_id]

        occs = []
        if edge_id in hs.edge_accum_occupancy:
            occs = hs.edge_accum_occupancy[edge_id]

        speeds = []
        if edge_id in hs.edge_accum_speed:
            speeds = hs.edge_accum_speed[edge_id]

        mean_vehicle_number = 0.0
        if len(vehnums) > 0:
            mean_vehicle_number = float(np.mean(vehnums))

        max_vehicle_number = 0
        if len(vehnums) > 0:
            max_vehicle_number = int(np.max(vehnums))

        mean_occupancy = 0.0
        if len(occs) > 0:
            mean_occupancy = float(np.mean(occs))

        mean_speed = 0.0
        if len(speeds) > 0:
            mean_speed = float(np.mean(speeds))

        score = 0.0
        if mean_speed < misc.CONGESTION_SPEED_THRESHOLD:
            score += 3.0
        if mean_vehicle_number >= misc.HIGH_VEHICLE_COUNT_THRESHOLD:
            score += 2.0
        if mean_occupancy >= misc.OCCUPANCY_HIGH:
            score += 3.0

        edges_summary.append(
            {
                'edge_id': edge_id,
                'mean_vehicle_number': mean_vehicle_number,
                'max_vehicle_number': max_vehicle_number,
                'mean_occupancy': mean_occupancy,
                'mean_speed': mean_speed,
                'congestion_score': score
            }
        )
    df_edges = DataFrame(edges_summary)
    df_edges.to_csv(csv_edges_path, index=False)
    return df_edges


def build_df_steps(csv_steps_path):
    df_steps = DataFrame(
        {
            'Step': hs.steps,
            'Active_vehicles': hs.vehicles,
            'Average_speed': hs.speeds,
            'Avg_wait_step': hs.avg_waits,
            'Total_wait_step': hs.total_waits,
            'Max_wait_step': hs.max_waits
        }
    )
    df_steps.to_csv(csv_steps_path, index=False)
    return df_steps


def build_df_vehicles(csv_vehicles_path):
    df_vehicles = DataFrame(columns=['veh_id', 'final_wait_s'])
    for vid, wt in hs.vehicle_final_wait.items():
        df_vehicles = DataFrame([{'veh_id': vid, 'final_wait_s': wt}])
    df_vehicles.to_csv(csv_vehicles_path, index=False)
    return df_vehicles


def chk_sumo(ref_str):
    bin_path = sumolib.checkBinary(ref_str)
    if ref_str == bin_path:
        return ''
    return bin_path


# Linear regresion according to the total number of vehicles, giving a tendency
def check_hoard_tendency(last_df_steps, log_str):
    x = np.array(range(len(last_df_steps))).reshape(-1, 1)
    y = last_df_steps['Active_vehicles'].astype(float).values.reshape(-1, 1)
    model = LinearRegression()
    model.fit(x, y)
    slope = float(model.coef_[0][0])
    intercept = float(model.intercept_[0])
    log_str(
        translator.gettext_str(
            'Tendency (lineal regresion) vehicles per step: ' +
            'slope={slope:.4f}' +
            'vehicles/step, intercept={intercept}'
        ).format(slope=slope, intercept=intercept)
    )

    # Predict the next ten steps
    future_X = np.array(range(
        len(last_df_steps),
        len(last_df_steps)+10
    )).reshape(-1, 1)

    predictions = model.predict(future_X).flatten().tolist()
    log_str(
        translator.gettext_str(
            'Prediction for the next 10 steps (active steps):'
        )
    )
    for p in predictions:
        log_str(' * {pr}'.format(pr=round(p)))


def export_edges_csv(last_df_edges, log_str, basename, timestamp):
    last_df_edges['density_label'] = last_df_edges['mean_vehicle_number'].apply(
            lambda mvn: misc.classify_edge_density(mvn)
    )
    last_df_edges['intersection_status'] = last_df_edges.apply(
        lambda r: misc.evaluate_cross_status(r),
        axis=1
    )
    csv_edges_path_enriched = '{basename}_edges_enriched_{timestamp}.csv'.format(
        basename=basename,
        timestamp=timestamp
    )
    last_df_edges.to_csv(os.path.join(
        misc.RESULTS_DIR,
        csv_edges_path_enriched
    ), index=False)

    log_str(
        translator.gettext_str(
            'CSV edges enriched saved at: {csv_epe}'
        ).format(csv_epe=csv_edges_path_enriched)
    )


def export_json(json_path, last_df_edges, log_str):
    edges_json = last_df_edges.sort_values(
        'congestion_score',
        ascending=False
    ).to_dict(orient='records')
    with open(json_path, 'w', encoding='utf-8') as f:
        dump(edges_json, f, indent=2)
    log_str(
        translator.gettext_str(
            'JSON edges saved at: {json_path}'
        ).format(json_path=json_path)
    )


def export_txt(last_df_steps, last_df_edges, save_file, txt_path):
    content = translator.gettext_str(
        '{lang}: - SIMULATION SUMARY\n' +
        'FINAL ANALISIS\n' +
        'Executed steps: {len_lds}\n' +
        'Average vehicles (per step): {mean_lds_vehicles:.2f}\n' +
        'Mean speed (m/s): {mean_lds_speed:.2f}\n' +
        'Top edges per congestion_score:\n\n'
    ).format(
        lang=translator.get_language,
        len_lds=len(last_df_steps),
        mean_lds_vehicles=last_df_steps['Active_vehicles'].mean(),
        mean_lds_speed=last_df_steps['Average_speed'].mean()
    )
    top = last_df_edges.sort_values(
        'congestion_score',
        ascending=False
    ).head(20)
    content += top[[
        'edge_id',
        'mean_vehicle_number',
        'mean_occupancy',
        'mean_speed',
        'congestion_score'
    ]].to_string(index=False)
    save_file(txt_path, content)


def give_recommendations(last_df_edges, log_str):
    problematic = last_df_edges[
        (last_df_edges['mean_vehicle_number'] >= misc.HIGH_VEHICLE_COUNT_THRESHOLD) |
        (last_df_edges['mean_occupancy'] >= misc.OCCUPANCY_HIGH) |
        (last_df_edges['mean_speed'] < misc.CONGESTION_SPEED_THRESHOLD)
    ]
    problematic = problematic.sort_values(
        ['congestion_score', 'mean_vehicle_number'],
        ascending=[False, False]
    ).head(30)
    recomendations = []
    for _, r in problematic.iterrows():
        recomendations.extend(misc.set_suggestions_top_edge(r))
    # Removing duplicates
    recomendations = list(set(recomendations))
    if recomendations:
        log_str(
            translator.gettext_str('Recomendations (heuristics):')
        )
        for rec in recomendations[:50]:
            log_str(' - {rec}'.format(rec=rec))
    else:
        log_str(
            translator.gettext_str('Automatic tips were not generated')
        )


def give_post_analysis(last_df_edges, last_df_vehicles, log_str):
    log_str(
        translator.gettext_str('\n=== POST-SIMULATION ANALISIS ===')
    )
    if not last_df_vehicles.empty:
        final_waits = last_df_vehicles['final_wait_s'].astype(float)
    else:
        final_waits = Series(dtype=float)
    n_veh_final = len(final_waits)

    mean_wait = 0.0
    if n_veh_final > 0:
        mean_wait = float(final_waits.mean())

    median_wait = 0.0
    if n_veh_final > 0:
        median_wait = float(final_waits.median())

    std_wait = 0.0
    if n_veh_final > 0:
        std_wait = float(final_waits.std())

    pct90_wait = 0.0
    if n_veh_final > 0:
        pct90_wait = float(final_waits.quantile(0.9))

    log_str(
        translator.gettext_str(
            'Vehicles with final register: {n_veh_final}\n'
            'Mean wait: {mean_wait:.2f}s |' +
            'Median wait: {median_wait:.2f}s |' +
            'Standard wait: {std_wait:.2f} |' +
            '90pct: {pct90_wait:.2f}s'
        ).format(
            n_veh_final=n_veh_final,
            mean_wait=mean_wait,
            median_wait=median_wait,
            std_wait=std_wait,
            pct90_wait=pct90_wait
        )
    )
    df_edges_sorted = last_df_edges.sort_values('congestion_score', ascending=False)
    top10_congested = df_edges_sorted.head(10)
    log_str(
        translator.gettext_str('Top 10 edges per congestion_score:')
    )
    log_str(
        top10_congested[[
            'edge_id',
            'mean_vehicle_number',
            'mean_occupancy',
            'mean_speed',
            'congestion_score'
        ]].to_string(index=False)
        if not top10_congested.empty
        else ' - No edge set'
    )


# Get coordinates on every edge (using net if it is available)
def set_heatmap(heatmap_png_path, last_df_edges, log_str, net):
    log_str(
        translator.gettext_str(
            'Generating heatmap and exporting PNG/CSV/JSON...'
        )
    )
    coords = []
    weights = []
    for _, r in last_df_edges.iterrows():
        edge_id = r['edge_id']
        mean_v = r['mean_vehicle_number']
        mean_occ = r['mean_occupancy']
        mean_sp = r['mean_speed']
        x = None
        y = None
        try:
            edge_obj = net.getEdge(edge_id)
        except KeyError:
            edge_obj = None
            continue
        # obtain mean coordinatesin the nodes edge
        fn = edge_obj.getFromNode()
        tn = edge_obj.getToNode()
        fx, fy = None, None
        fx, fy = fn.getCoord()
        tx, ty = None, None
        tx, ty = tn.getCoord()
        if not (fx is None or tx is None):
            x = float((fx + tx) / 2.0)
            y = float((fy + ty) / 2.0)
        else:
            # fallback: if edge has shape (polyline)
            shape = edge_obj.getShape()
            if shape and len(shape) > 0:
                # shape is list of (x,y)
                xs = [p[0] for p in shape]
                ys = [p[1] for p in shape]
                x = float(np.mean(xs))
                y = float(np.mean(ys))

        # fallback random coords (if net unavailable) - avoid generating heatmap if no net coords
        if not (x is None or y is None):
            coords.append((x, y))
            weight = mean_v * (1.0 + mean_occ) / (mean_sp + 0.1)
            weights.append(weight)

    if not (coords and weights):
        log_str(
            translator.gettext_str(
                'Invalid netfile coordinates to generate the heatmap.'
            )
        )
        return
    xs = np.array([c[0] for c in coords])
    ys = np.array([c[1] for c in coords])
    ws = np.array(weights)
    # Normalize weights plotting
    ws_norm = ws / (np.max(ws) if np.max(ws) > 0 else 1.0)

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # scatter with proportional weight
    sizes = (ws_norm * 300) + 10
    sc = ax.scatter(xs, ys, s=sizes, c=ws_norm, cmap='hot', alpha=0.7)
    fig.colorbar(
        sc,
        ax=ax,
        label=translator.gettext_str(
            '({lan}) Relative level of load (normalized)'
        ).format(lan=translator.get_language())
    )
    ax.set_title(
        translator.gettext_str('Load heatmap (center of edges)')
    )
    ax.set_xlabel(
        translator.gettext_str('X network coordinates')
    )
    ax.set_ylabel(
        translator.gettext_str('Y network coordinates')
    )
    fig.tight_layout()
    fig.savefig(heatmap_png_path, dpi=150)
    log_str(
        translator.gettext_str(
            'Heatmap saved at: {heatmap_png_path}'
        ).format(heatmap_png_path=heatmap_png_path)
    )

    plt.show()


def sim_steps(data_imported, log_str, step):
    traci.simulationStep()

    current_vehicle_ids = traci.vehicle.getIDList()
    n = traci.vehicle.getIDCount()
    v_prom = 0.0

    velocities_step = []
    if n > 0:
        for vid in current_vehicle_ids:
            s = traci.vehicle.getSpeed(vid)
            if isinstance(s, (int, float)):
                velocities_step.append(s)
        if velocities_step:
            v_prom = float(np.mean(velocities_step))

    waiting_times = []
    for vid in current_vehicle_ids:
        wt = float(traci.vehicle.getWaitingTime(vid))
        hs.vehicle_last_seen[vid] = wt
        waiting_times.append(wt)

    total_wait_step = 0.0
    avg_wait_step = 0.0
    max_wait_step = 0.0

    if waiting_times:
        total_wait_step = sum(waiting_times)
        avg_wait_step = np.mean(waiting_times)
        max_wait_step = max(waiting_times)

    departed = hs.prev_vehicle_set - set(current_vehicle_ids)
    for dv in departed:
        hs.vehicle_final_wait[dv] = 0.0
        if dv in hs.vehicle_last_seen:
            hs.vehicle_final_wait[dv] = hs.vehicle_last_seen.get(dv, 0.0)

    hs.prev_vehicle_set = set(current_vehicle_ids)

    # edges list and stats per edge
    edges_list = traci.edge.getIDList()

    for edge in edges_list:
        veh_num = traci.edge.getLastStepVehicleNumber(edge)
        occ = traci.edge.getLastStepOccupancy(edge)
        mean_speed_edge = traci.edge.getLastStepMeanSpeed(edge)

        hs.edge_accum_vehicle_number[edge].append(int(veh_num))
        hs.edge_accum_occupancy[edge].append(float(occ))
        hs.edge_accum_speed[edge].append(float(mean_speed_edge))

    hs.steps.append(step)
    hs.vehicles.append(int(n))
    hs.speeds.append(v_prom)
    hs.avg_waits.append(avg_wait_step)
    hs.total_waits.append(total_wait_step)
    hs.max_waits.append(max_wait_step)

    # Live analysis: Only log every N steps
    steps_n = data_imported['steps_amnt'] // data_imported['steps_interval']
    if step % max(1, steps_n) == 0:
        log_str(
            translator.gettext_str(
                'Progress: step {step}/{steps_amnt} - ' +
                'Vehicles: {n} - ' +
                'Average speed: {v_prom:.2f} m/s'
            ).format(
                step=step,
                steps_amnt=data_imported['steps_amnt'],
                n=n,
                v_prom=v_prom
            )
        )


def tls_traffic_lights(log_str, net):
    tls_info = []
    tls_list = []
    tls_list = net.getTrafficLights()
    for tls in tls_list:
        tls_info.append(tls.getID())
    if tls_info:
        log_str(
            translator.gettext_str(
                'Traffic lights detected in the network: {len_tls_info} ' +
                '(ex: {tls_detected})'
            ).format(
                len_tls_info=len(tls_info),
                tls_detected=tls_info[:5]
            )
        )
        return
    log_str(
        translator.gettext_str(
            'No traffic lights detected in the network, ' +
            'or netfile does not contain accesible TLS'
        )
    )


def main(
    data_imported,
    last_df_steps,
    last_df_vehicles,
    last_df_edges,
    log_str,
    save_file
):
    os.makedirs(misc.RESULTS_DIR, exist_ok=True)

    sumo_binary = chk_sumo('sumo-gui')\
        if data_imported['sumo-gui?']\
        else chk_sumo('sumo-gui')

    if not sumo_binary:
        log_str(
            translator.gettext_str(
                '{sumo_binary} is not properly installed'
            ).format(sumo_binary=sumo_binary)
        )
        return

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    basename = '{sim_name}_{timestamp}'.format(
        sim_name=data_imported['sim_name'],
        timestamp=timestamp
    )
    csv_steps_path = os.path.join(
        misc.RESULTS_DIR,
        '{basename}_steps.csv'.format(basename=basename)
    )
    csv_vehicles_path = os.path.join(
        misc.RESULTS_DIR,
        '{basename}_vehicles.csv'.format(basename=basename)
    )
    csv_edges_path = os.path.join(
        misc.RESULTS_DIR,
        '{basename}_edges_raw_{timestamp}.csv'.format(
            basename=basename,
            timestamp=timestamp
        )
    )
    txt_path = os.path.join(
        misc.RESULTS_DIR,
        '{basename}_summary.txt'.format(basename=basename)
    )
    json_path = os.path.join(
        misc.RESULTS_DIR,
        '{basename}_edges_summary.json'.format(basename=basename)
    )
    heatmap_png_path = os.path.join(
        misc.RESULTS_DIR,
        '{basename}_heatmap.png'.format(basename=basename)
    )

    # Start running traci
    traci.start([
        sumo_binary,
        '-c',
        data_imported['src_path'][0],
        '--step-length',
        str(data_imported['steps_interval'])
    ])
    log_str(
        translator.gettext_str(
            'Start SUMO ({sumo_binary}) with {src_path}'
        ).format(sumo_binary=sumo_binary, src_path=data_imported['src_path'][0])
    )

    # Arrange the netfile
    netfile = misc._find_netfile_from_sumocfg(data_imported['src_path'][0])
    net = None
    if netfile:
        net = sumolib.net.readNet(netfile)
    if net is None:
        log_str('Invalid netfile')
        return

    step = 0
    while step <= data_imported['steps_amnt']:
        sim_steps(data_imported, log_str, step)
        step += data_imported['steps_interval']

    # Building Dataframes
    for veh_id, last_w in hs.vehicle_last_seen.items():
        if veh_id not in hs.vehicle_final_wait:
            hs.vehicle_final_wait[veh_id] = last_w

    last_df_steps = build_df_steps(csv_steps_path)
    last_df_vehicles = build_df_vehicles(csv_vehicles_path)
    last_df_edges = build_df_edges(csv_edges_path)

    give_post_analysis(last_df_edges, last_df_vehicles, log_str)
    give_recommendations(last_df_edges, log_str)
    tls_traffic_lights(log_str, net)
    set_heatmap(heatmap_png_path, last_df_edges, log_str, net)
    export_json(json_path, last_df_edges, log_str)
    check_hoard_tendency(last_df_steps, log_str)
    export_txt(last_df_steps, last_df_edges, save_file, txt_path)
    export_edges_csv(last_df_edges, log_str, basename, timestamp)

    log_str(translator.gettext_str('Analysis finished.'))

    traci.close(False)
    return last_df_steps, last_df_vehicles, last_df_edges

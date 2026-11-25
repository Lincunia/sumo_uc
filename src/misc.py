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
from math import isnan
from os import path
from re import search
from shutil import copy2
from urllib import request
from xml.etree import ElementTree
from .i18n import translator

CONGESTION_SPEED_THRESHOLD = 5.0  # m/s
HIGH_VEHICLE_COUNT_THRESHOLD = 15
OCCUPANCY_HIGH = 0.6
OCCUPANCY_MEDIUM = 0.3
URL_CHK = 'https://www.google.com'
MAPS_DIR = path.join(
    path.dirname(path.dirname(path.abspath(__file__))),
    'saved_maps'
)
RESULTS_DIR = path.join(
    path.dirname(path.dirname(path.abspath(__file__))),
    'results'
)


def has_internet():
    try:
        request.urlopen(URL_CHK, timeout=5)
        return True
    except Exception:
        return False


def set_suggestions_top_edge(edge_row):
    suggestions = []
    edge_id = edge_row.get('edge_id')
    mean_v = edge_row.get('mean_vehicle_number', 0.0)
    mean_occ = edge_row.get('mean_occupancy', 0.0)
    mean_speed = edge_row.get('mean_speed', 0.0)
    if mean_v >= HIGH_VEHICLE_COUNT_THRESHOLD:
        suggestions.append(
            translator.gettext_str(
                'Increase capacity at {edge_id} ' +
                '(ex. additional lane or alternative roads)'
            ).format(edge_id=edge_id)
        )
    if mean_occ >= OCCUPANCY_HIGH:
        suggestions.append(
            translator.gettext_str(
                'Check time signal at edges close to {edge_id}'
            ).format(edge_id=edge_id)
        )
    if mean_speed < CONGESTION_SPEED_THRESHOLD:
        suggestions.append(
            translator.gettext_str(
                'Analize blockage/obstacles at {edge_id} and alternative roads'
            ).format(edge_id=edge_id)
        )
    if not suggestions:
        suggestions.append(
            translator.gettext_str(
                'Monitor {edge_id}, possible adjustment of traffic lights'
            ).format(edge_id=edge_id)
        )
    return suggestions


def classify_traffic_speed(speed_m_s):
    if speed_m_s is None or\
       (isinstance(speed_m_s, float) and isnan(speed_m_s)):
        return 'N/A'
    kmh = float(speed_m_s) * 3.6
    if kmh < 15:
        return translator.gettext_str(
            'Slow (congestion) - {kmh:.1f} km/h'
        ).format(kmh=kmh)
    if kmh < 40:
        return translator.gettext_str('Normal - {kmh:.1f} km/h').format(kmh=kmh)
    return translator.gettext_str('Fast - {kmh:.1f} km/h').format(kmh=kmh)


def classify_edge_density(mean_vehicle_number):
    if mean_vehicle_number >= HIGH_VEHICLE_COUNT_THRESHOLD:
        return 'High'
    if mean_vehicle_number >= 5:
        return 'Middle'
    return 'Low'


def evaluate_cross_status(edge_row):
    mv = 0.0
    occ = 0.0

    mv = float(edge_row.get('mean_vehicle_number', 0.0))
    occ = float(edge_row.get('mean_occupancy', 0.0))

    if mv > HIGH_VEHICLE_COUNT_THRESHOLD or occ > OCCUPANCY_HIGH:
        return translator.gettext_str('Not prepared (high risk)')
    if mv >= 5 or occ >= OCCUPANCY_MEDIUM:
        return translator.gettext_str('At the limit (possible saturation)')
    return translator.gettext_str('Ready')


def _copy_map_if_requested(src_path, dest_path):
    dest_dir_path = path.dirname(dest_path)
    copy2(src_path, dest_path)
    # heuristical way
    with open(src_path, 'r', encoding='utf-8') as f:
        text = f.read()

    for ext in [
        '.net.xml',
        '.rou.xml',
        '.add.xml',
        '.edge.xml',
        '.nod.xml',
        '.type.xml',
    ]:
        idx = 0
        while True:
            idx = text.find(ext, idx)
            if idx == -1:
                break
            start = text.rfind('"', 0, idx)
            if start == -1:
                start = text.rfind('\'', 0, idx)
                idx += len(ext)
                continue
            candidate = text[start+1:idx+len(ext)]
            candidate = candidate.strip().strip('"').strip('\'')
            if path.exists(candidate):
                copy2(
                    candidate,
                    path.join(dest_dir_path, path.basename(candidate))
                )
            else:
                posible = path.join(path.dirname(src_path), candidate)
                if path.exists(posible):
                    copy2(
                        posible,
                        path.join(dest_dir_path, path.basename(posible))
                    )
            idx += len(ext)


def _find_netfile_from_sumocfg(src_path):
    tree = ElementTree.parse(src_path)
    root = tree.getroot()
    for input_tag in root.findall('./input'):
        netfile = input_tag.find('net-file')
        if netfile is None or 'value' not in netfile.attrib:
            continue
        candidate = netfile.attrib['value']
        if path.exists(candidate):
            return candidate
        possible = path.join(path.dirname(src_path), candidate)
        if path.exists(possible):
            return possible

        return path.abspath(possible)

    # fallback: find the first .net.xml
    with open(src_path, "r", encoding="utf-8") as f:
        text = f.read()
    exp_mtch = search(r'["\']([^"\']+\.net\.xml)["\']', text)
    if exp_mtch:
        posible = path.join(path.dirname(src_path), exp_mtch.group(1))
        return posible if path.exists(posible) else path.abspath(posible)

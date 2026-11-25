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
from collections import defaultdict


class HoardStructures:
    def __init__(self):
        self.steps = []
        self.vehicles = []
        self.speeds = []
        self.avg_waits = []
        self.total_waits = []
        self.max_waits = []

        self.vehicle_last_seen = dict()
        self.vehicle_final_wait = dict()

        self.edge_accum_vehicle_number = defaultdict(list)
        self.edge_accum_occupancy = defaultdict(list)
        self.edge_accum_speed = defaultdict(list)

        self.prev_vehicle_set = set()


hs = HoardStructures()

import sys
uuid = sys.argv[1]
import json

GOAL_DISTANCE = float(sys.argv[2])
START = (45.47544724397924, -122.75669108867837)
STAR_COUNT = 3



import requests
from collections import defaultdict
import random

query = """
[out:json][timeout:60];
(
  way["highway"](around:19312,45.47545731173852,-122.7565044394363);
);
out geom;
"""

# response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
# print(response.status_code)
# data = response.json()
# with open(f"data.json", "w") as f:
#     json.dump(data, f, indent=2)

with open("data.json", "r") as f:
    data = json.load(f)

import math

EDGES = set()

def get_star(lat, lon, distance_miles, direction):
    R = 3959

    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing = math.radians(direction)

    new_lat = math.asin(math.sin(lat_rad) * math.cos(distance_miles / R) +
                        math.cos(lat_rad) * math.sin(distance_miles / R) * math.cos(bearing))

    new_lon = lon_rad + math.atan2(math.sin(bearing) * math.sin(distance_miles / R) * math.cos(lat_rad),
                                math.cos(distance_miles / R) - math.sin(lat_rad) * math.sin(new_lat))

    new_lat = math.degrees(new_lat)
    new_lon = math.degrees(new_lon)

    return (new_lat, new_lon)

def is_safe_road(tags):
    safe = True
    if tags.get("highway", "") == "residential":
        return True
    if int(tags.get("maxspeed", "0 mph").split(" ")[0]) > 25 and tags.get("sidewalk", "yes") == "no":
        safe = False
    if int(tags.get("maxspeed", "0 mph").split(" ")[0]) > 35:
        safe = False
    return safe

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return (R * c)

nodes = set()

for way in data['elements']:
    for i in range(len(way["nodes"]) - 1):
        lat1 = way["geometry"][i]["lat"]
        lon1 = way["geometry"][i]["lon"]
        lat2 = way["geometry"][i + 1]["lat"]
        lon2 = way["geometry"][i + 1]["lon"]

        miles = haversine(lat1, lon1, lat2, lon2)

        if "name" in way["tags"] and is_safe_road(way["tags"]):
            EDGES.add((way["nodes"][i], way["nodes"][i + 1], miles, (lat1, lon1), (lat2, lon2), way["tags"].get("name", "UNKNOWN NAME"), way["type"], way["tags"].get("maxspeed", "Unknown Speed Limit")))

            if i == 0:
                if (way["nodes"][i], lat1, lon1) not in nodes:
                    nodes.add((way["nodes"][i], lat1, lon1))
            
            if (way["nodes"][i + 1], lat2, lon2) not in nodes:
                nodes.add((way["nodes"][i + 1], lat2, lon2))

start_node, start_lat, start_lon = min(nodes, key=lambda c: haversine(c[1], c[2], START[0], START[1]))

G = {}
for edge in EDGES:
    node1, node2, miles, c1, c2, name, street_type, speed = edge

    if node1 in G:
        if (node2, miles, c2, name, street_type, speed) not in G[node1]:
            G[node1].add((node2, miles, c2, name, street_type, speed))
    else:
        G[node1] = set([(node2, miles, c2, name, street_type, speed)])

    if node2 in G:
        if (node1, miles, c1, name, street_type, speed) not in G[node2]:
            G[node2].add((node1, miles, c1, name, street_type, speed))
    else:
        G[node2] = set([(node1, miles, c1, name, street_type, speed)])

visited = []
star_lat, star_lon = get_star(start_lat, start_lon, 100, random.randint(1, 360))

total_distance = 0
current_node = start_node
moves = []
moves.append(current_node)

def get_node(nodeId):
    for node in nodes:
        if node[0] == nodeId:
            return node

while total_distance < (GOAL_DISTANCE/2):
    options = list(G[current_node])
    options = [option for option in options if option[0] not in visited]
    visited.append(current_node)

    if len(options) == 0:
        last_node = moves[-2]

        distance = [a for a in list(G[current_node]) if a[0] == last_node][0][1]
        total_distance -= distance

        moves.remove(current_node)

        current_node = last_node

        continue

    best_option = min(options, key=lambda c: haversine(c[2][0], c[2][1], star_lat, star_lon))
    total_distance += best_option[1]
    current_node = best_option[0]
    moves.append(current_node)

for i in range(len(moves)):
    mnode = moves[i]
    moves[i] = get_node(mnode)

import json

data = []

dist_so_far = 0
for i in range(len(moves)):
    move = moves[i]
    if i == 0:
        old = moves[i]
    else:
        old = moves[i - 1]
    dist = haversine(move[1], move[2], old[1], old[2])
    if (dist_so_far//1) != ((dist_so_far + dist)//1):
        data.append({ "lat": float(move[1]), "lon": float(move[2]), "marker": str((dist_so_far + dist)//1) })
    else:
        data.append({ "lat": float(move[1]), "lon": float(move[2]) })
    dist_so_far += dist

with open(f"data/{uuid}.json", "w") as f:
    json.dump(data, f, indent=2)

with open(f"mileage.json", "w") as f:
    json.dump({"mileage":total_distance}, f, indent=2)

print(total_distance)

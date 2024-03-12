import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime, timezone
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

output_file = os.environ.get('AIS_OUTPUT_FILE', './output.json')

def serialize_datetime(obj): 
    if isinstance(obj, datetime): 
        return obj.isoformat() 
    raise TypeError("Type not serializable") 

def write_ship_geosjon(ships_data_array):
  features = []
  for ship_id, ship_properties in ships_data_array.items():
    ship_data = ship_properties["data"]
    if len(ship_data) > 1:
      geom_type = "LineString"
      coords = list(map(lambda x: [x["lon"], x["lat"]], ship_data))
    else:
      geom_type = "Point"
      coords = list(map(lambda x: [x["lon"], x["lat"]], ship_data))[0]
    features.append({
      "type": "Feature",
      "geometry": {
        "type": geom_type,
        "coordinates": coords
      },
      "properties": {
        "ship_id": f"{ship_properties['ship_id']}",
        "timestamps": list(map(lambda x: x["dateTime"], ship_data))
      }
    })
  gj = {
    "type": "FeatureCollection",
    "features": features
  }
  with open(output_file, 'w') as f:
    f.write(json.dumps(gj, default=serialize_datetime))


async def connect_ais_stream():
    ship_data = {}
    if "AIS_BBOX" in os.environ:
      bbox = json.loads(os.environ.get("AIS_BBOX"))
      print(f"bbox loaded: {bbox}")
    else:
      bbox = [[11.603304207355961, # min lat
              30.40921772695401 # min lon
              ],
              [31.844734608073395, # max lat
              44.75088774620332 # max long
            ]]

    with open(f"{output_file}_bbox.json", 'w') as f:
      # geojson is [lon, lat]
      bottom_left = [bbox[0][1], bbox[0][0]]
      top_right = [bbox[1][1], bbox[1][0]]
      print(bottom_left)
      print(top_right)
      bbox_gj = {
        "type": "Feature",
        "properties": {},
        "geometry": {
          "type": "Polygon",
          "coordinates": [[
            bottom_left,
            [bottom_left[0], top_right[1]],
            top_right,
            [top_right[0], bottom_left[1]],
            bottom_left
          ]]
        }
      }
      f.write(json.dumps(bbox_gj))

    async with websockets.connect("wss://stream.aisstream.io/v0/stream") as websocket:
        subscribe_message = {
          "APIKey": os.environ.get('AISSTREAM_API_KEY', ''),
          "BoundingBoxes": [bbox],
          # "FiltersShipMMSI": ["368207620", "367719770", "211476060"],
          "FilterMessageTypes": ["PositionReport"]
        }

        subscribe_message_json = json.dumps(subscribe_message)
        await websocket.send(subscribe_message_json)

        async for message_json in websocket:
            message = json.loads(message_json)
            message_type = message["MessageType"]

            if message_type == "PositionReport":
                # the message parameter contains a key of the message type which contains the message itself
                ais_message = message['Message']['PositionReport']
                
                # store data in memory
                if ais_message['UserID'] not in ship_data:
                  ship_data[ais_message['UserID']] = {
                    "ship_id": ais_message['UserID'],
                    "data": []
                  }
                
                ship_data[ais_message['UserID']]["data"].append({
                  "lat": ais_message['Latitude'],
                  "lon": ais_message['Longitude'],
                  "dateTime": datetime.now()
                })

                # dump current in memory data to output file
                write_ship_geosjon(ship_data)

if __name__ == "__main__":
    asyncio.run(asyncio.run(connect_ais_stream()))


import math
import requests
from PIL import Image
import numpy as np
from io import BytesIO
import logging

"""
This module provides utilities for fetching and processing digital elevation model (DEM) data 
from the Geospatial Information Authority of Japan (GSI).

Functions:
  get_elevation(lat: float, lng: float) -> float

Usage:
  Run this module from the command line to get the elevation of a specific latitude and longitude.
  Command line arguments: 
    lat (float): Latitude of the location
    lng (float): Longitude of the location
    --log (str): Logging level, one of ['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'], default is 'ERROR'.

Example:
  python dem_module.py 35.681167 139.767052 --log DEBUG

See also:
  https://www.jstage.jst.go.jp/article/geoinformatics/26/4/26_155/_pdf
  https://maps.gsi.go.jp/help/pdf/demapi.pdf
"""

pow2_8 = pow(2, 8)
pow2_16 = pow(2, 16)
pow2_23 = pow(2, 23)
pow2_24 = pow(2, 24)

def _get_dem_url_list():
    """
    Returns a list of dictionaries, each representing a type of DEM data and its properties.
    """
    return [
        {
            "title": "DEM5A",
            "url": "https://cyberjapandata.gsi.go.jp/xyz/dem5a_png/{z}/{x}/{y}.png",
            "minzoom": 15,
            "maxzoom": 15,
            "fixed": 1
        },
        {
            "title": "DEM5B",
            "url": "https://cyberjapandata.gsi.go.jp/xyz/dem5b_png/{z}/{x}/{y}.png",
            "minzoom": 15,
            "maxzoom": 15,
            "fixed": 1
        },
        {
            "title": "DEM5C",
            "url": "https://cyberjapandata.gsi.go.jp/xyz/dem5c_png/{z}/{x}/{y}.png",
            "minzoom": 15,
            "maxzoom": 15,
            "fixed": 1
        },
        {
            "title": "DEM10B",
            "url": "https://cyberjapandata.gsi.go.jp/xyz/dem_png/{z}/{x}/{y}.png",
            "minzoom": 14,
            "maxzoom": 14,
            "fixed": 0
        }
    ]

def _make_url_list():
    """
    Returns a list of dictionaries, each representing a type of DEM data to be fetched,
    sorted by decreasing priority.
    """    
    list = []
    for dem_url in _get_dem_url_list():
        if dem_url["maxzoom"] < dem_url["minzoom"]:
            buff = dem_url["maxzoom"]
            dem_url["maxzoom"] = dem_url["minzoom"]
            dem_url["minzoom"] = buff

        minzoom = dem_url["minzoom"]

        for z in range(dem_url["maxzoom"], minzoom - 1, -1):
            list.append({
                "title": dem_url["title"],
                "zoom": z,
                "url": dem_url["url"],
                "fixed": dem_url["fixed"]
            })
    
    return list

def _make_url(url, tile_info):
    """
    Returns a URL string by replacing the placeholders {x}, {y}, {z} in the URL pattern with
    the corresponding values from the tile_info dictionary.

    Args:
        url (dict): A dictionary containing the URL pattern and other properties of the DEM data.
        tile_info (dict): A dictionary containing the x, y, z coordinates of the DEM tile.

    Returns:
        str: A URL
    """   
    result = url['url'].replace("{x}", str(tile_info['x']))
    result = result.replace("{y}", str(tile_info['y']))
    result = result.replace("{z}", str(url['zoom']))
    return result


def _get_tile_info(lat, lng, z):
    """
    Returns a dictionary representing the tile coordinates of a specific geographic location
    at a given zoom level.

    Args:
        lat (float): The latitude of the location.
        lng (float): The longitude of the location.
        z (int): The zoom level.

    Returns:
        dict: A dictionary with keys 'x', 'y', 'pX', 'pY', representing the tile coordinates.
    """   
    lng_rad = lng * math.pi / 180
    R = 128 / math.pi
    world_coord_x = R * (lng_rad + math.pi)
    pixel_coord_x = world_coord_x * pow(2, z)
    tile_coord_x = math.floor(pixel_coord_x / 256)
    lat_rad = lat * math.pi / 180
    world_coord_y = -R / 2 * math.log((1 + math.sin(lat_rad)) / (1 - math.sin(lat_rad))) + 128
    pixel_coord_y = world_coord_y * pow(2, z)
    tile_coord_y = math.floor(pixel_coord_y / 256)
    return {
        'x': tile_coord_x,
        'y': tile_coord_y,
        'pX': math.floor(pixel_coord_x - tile_coord_x * 256),
        'pY': math.floor(pixel_coord_y - tile_coord_y * 256)
    }

def get_elevation(lat, lng):
    """
    Returns the elevation of a specific geographic location by fetching and processing
    DEM data from the GSI.

    Args:
        lat (float): The latitude of the location.
        lng (float): The longitude of the location.

    Returns:
        float: The elevation of the location, in meters. If the elevation data is not available,
        it will return 0.
    """
    tileInfo = _get_tile_info(lat, lng, 15)
    logging.debug(f"tileInfo: {tileInfo}")

    urls = _make_url_list()

    while len(urls) > 0:
        url= urls.pop(0)
        imageurl = _make_url(url, tileInfo)

        try:
            response = requests.get(imageurl)
            response.raise_for_status()  # Raises stored HTTPError, if one occurred.
        except requests.exceptions.HTTPError as err:
            if response.status_code == 404:  # Not found error
                logging.debug(f"HTTP error occurred for {imageurl}: {err}")
                continue  # Skip to next iteration
            else:
                raise  # Re-raise the exception if it is not a 404 error

        # open the image with PIL
        img = Image.open(BytesIO(response.content))

        # convert the image data to a numpy array
        img_array = np.array(img)

        # specify the coordinates (x, y)
        x, y = tileInfo['pX'], tileInfo['pY']

        # get the pixel value
        r, g, b = img_array[y, x]
        h = 0

        # 海は無視する
        if r != 128 or g != 0 or b != 0:
            d = r * pow2_16 + g * pow2_8 + b
            h = d if d < pow2_23 else d - pow2_24
            if h == -pow2_23:
                h = 0
            else:
                h *= 0.01

        return h

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("lat", help="Latitude", type=float)
    parser.add_argument("lng", help="Longitude", type=float)
    parser.add_argument("--log", choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'], default='ERROR', help="ログレベルの設定")
    args = parser.parse_args()

    # ログレベル設定
    log_level = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=log_level)

    print(get_elevation(args.lat, args.lng))
    
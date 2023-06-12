# pyele

`pyele` is a Python module for fetching and processing digital elevation model (DEM) data from the Geospatial Information Authority of Japan (GSI).

## Installation

You can install `pyele` with pip:

```bash
pip3 install git+https://github.com/udawtr/pyele.git
```


## Usage

You can use pyele to get the elevation of a specific latitude and longitude:

```python
import pyele

lat = 35.681167
lng = 139.767052

elevation = pyele.get_elevation(lat, lng)
print(elevation)
```

## License

This project is licensed under the terms of the MIT license. See the LICENSE file for details.

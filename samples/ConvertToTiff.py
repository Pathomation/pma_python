# Uncomment below to download the required GDAL library
# from IPython import get_ipython
# # Download the required GDAL package from the [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/)
# import sys
# is_64bits = sys.maxsize > 2**32
# gdalDownloadLink = "https://download.lfd.uci.edu/pythonlibs/s2jqpv5t/GDAL-3.0.4-cp{0}-cp{0}m-{1}.whl".format(str(sys.version_info.major) + str(sys.version_info.minor), "win_amd64" if is_64bits else "win32")
# get_ipython().system('pip install {gdalDownloadLink}')

from pma_python import *
import os
import numpy as np
from osgeo import gdal
import math
import tqdm

_pmaCoreUrl = "http://localhost:54001/"

# what slide do you want to convert?
slidePath = "C:/Slides/Slide.svs"
# set the target TIFF quality 0-100
target_quality = 100
# set the target scale factor to download. One of [1, 2, 4, 8, 16, 32, 64, 128]
downscale_factor = 1

# Get the slide information and information about each zoomlevel available

print("Fetching image info for {0}".format(slidePath))
slideInfo = core.get_slide_info(slidePath)
print(slideInfo)
zoomLevelsInfo = core.get_zoomlevels_dict(slidePath)
maxLevel = max(zoomLevelsInfo)
tileSize = slideInfo["TileSize"]
print("Horizontal Tiles | Vertical Tiles | Total Tiles")
for level in zoomLevelsInfo:
    tilesX, tilesY, totalTiles = zoomLevelsInfo[level]
    print("{:>16} |{:>15} |{:>12}".format(tilesX, tilesY, totalTiles))

filename = slidePath.rpartition("/")[-1]
xresolution = 10000 / slideInfo["MicrometresPerPixelX"]
yresolution = 10000 / slideInfo["MicrometresPerPixelY"]

# Create new TIFF file using the GDAL TIFF driver
# The width and height of the final tiff is based on number of tiles horizontally and vertically.

# Validate the parameters
if target_quality is None or target_quality < 0 or target_quality > 90:
    target_quality = 80
if downscale_factor not in [1, 2, 4, 8, 16, 32, 64, 128]:
    downscale_factor = 1


maxLevel = max(zoomLevelsInfo)
powerof2 = int(math.log2(downscale_factor))

level = maxLevel - powerof2
level = min(max(level, 0), maxLevel)
tilesX, tilesY, totalTiles = zoomLevelsInfo[level]

# We set the region of the image we want to read to set the final tif size accordingly
tileRegionX = (0, tilesX)
tileRegionY = (0, tilesY)

tileSize = 512
tiff_drv = gdal.GetDriverByName("GTiff")
# Set the final size
ds = tiff_drv.Create(
    filename.split('.')[0] + '.tif',
    int((tileRegionX[1] - tileRegionX[0]) * 512),
    int((tileRegionY[1] - tileRegionY[0]) * 512),
    3,
    options=['BIGTIFF=YES',
        'COMPRESS=JPEG', 'TILED=YES', 'BLOCKXSIZE=' + str(tileSize), 'BLOCKYSIZE=' + str(tileSize),
        'JPEG_QUALITY=90', 'PHOTOMETRIC=RGB'
    ])
descr = "ImageJ=\nhyperstack=true\nimages=1\nchannels=1\nslices=1\nframes=1"
ds.SetMetadata({ 'TIFFTAG_RESOLUTIONUNIT': '3', 'TIFFTAG_XRESOLUTION': str(int(xresolution / downscale_factor)), 'TIFFTAG_YRESOLUTION': str(int(yresolution / downscale_factor)), 'TIFFTAG_IMAGEDESCRIPTION': descr })


print("Maximum level = ", maxLevel, ", level = ", level, ", power of 2 = ", powerof2)
filename.split('.')[0] + '.tif'

# We read each tile of the final zoomlevel (1:1 resolution) from the server and write it to the resulting TIFF file
# Then we create the pyramid of the file using BuildOverviews function of GDAL
tilesX, tilesY, totalTiles = zoomLevelsInfo[level]
print("Requesting level {}".format(level))

pbar = tqdm.tqdm(total= int((tileRegionX[1] - tileRegionX[0])*(tileRegionY[1] - tileRegionY[0]))) 
for x in range(tileRegionX[0], tileRegionX[1]):
    for y in range(tileRegionY[0],tileRegionY[1], 1):  # range of y-axis in which we are interested for this slide
        pbar.update()
        tile = core.get_tile(slidePath, x, y , level, quality=target_quality)
        arr = np.array(tile, np.uint8)

        # calculate startx starty pixel coordinates based on tile indexes (x,y)
        # for the final tif we want the first tile, i.e. (tileRegionX[0], tileRegionY[0]) ,to be at (0,0) so we need to transform the coordinates
        sx = (x - tileRegionX[0]) * tileSize
        sy = (y - tileRegionY[0]) * tileSize

        ds.GetRasterBand(1).WriteArray(arr[..., 0], sx, sy)
        ds.GetRasterBand(2).WriteArray(arr[..., 1], sx, sy)
        ds.GetRasterBand(3).WriteArray(arr[..., 2], sx, sy)

pbar.close()
print("Please wait while building the pyramid")
ds.BuildOverviews('average', [pow(2, l) for l in range(1, level)])
ds = None
print("Done")



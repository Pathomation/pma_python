# pma-python
PMA-python is a Python wrapper library for PMA.start, 
a universal viewier for whole slide imaging and microscopy.

If you're working with

* microscopy data and are you tired of having to use a different 
library for each vendor specific digital slide format
* image analysis software and are you looking for a way to have 
complete control over your algorithms (and not just be able to 
select those provided for you)
* novel evaluation methods for histology / pathology and do you 
just wish there was a way to now automatically evaluate it on 
100s of slides (batch processing)

and you're doing all of this in Python, then PMA.start and 
PMA-python are for you!

With PMA-python, you can inspect and navigate any type of 
microscopic imaging file format available. Whether you have 
macroscopic observations, whole slide imaging data, or fluorescent 
snapshot observations, we can bring it all into Python now.

The following vendor formats are currently supported:

* TIFF (.tif, .tiff) with JPEG, JPEG2000, LZW, Deflate, Raw, RLE		
* JPEG (.jpeg, .jpg)
* JPEG 2000 (.jp2)
* PNG (.png)
* Olympus VSI (.vsi) with lossless JPEG, JPEG, Raw
* Ventana / Roche BIF (.bif)
* Hamamatsu (.vms, .ndpi, .dcm) with JPEG, JPEG2000
* Huron Technologies (.tif)
* 3DHistech (.mrxs) with JPEG, PNG, BMP
* Aperio / Leica (.svs, .cws, .scn, .lif, DICOMDIR) with JPEG, JPEG2000
* Carl Zeiss (.zvi, .czi, .lsm) with Raw, PNG, JPEG, LZW, Deflate, JPEG2000	
* Open Microscopy Environment OME-TIFF (.tf2, .tf8, .btf, .ome.tif)
* Nikon (.nd2, .tiff) with Deflate, JPEG, JPEG2000, LZW, Deflate, Raw, RLE	
* Philips (.tif) with JPEG, JPEG2000, LZW, Deflate, Raw, RLE		
* Sakura (.svslide) with JPEG(sqlite2, sqlite3, mssql)
* Menarini (.ini) with Raw
* Motic (.mds) 
* Zoomify (.zif) with JPEG, JPEG2000, LZW, Deflate, Raw, RLE
* SmartZoom	(.szi) with JPEG, BMP
* Objective Imaging / Glissano (.sws)

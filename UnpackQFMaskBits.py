"""
Created on Fri Mar 17 10:51:55 2023

Unpack QF Mask layer for a given bit range from the NASA's Black Marble VNP46A1/A2 Products.

@author: Ranjay M. Shrestha, NASA's Black Marble Science Team, NASA Goddard Space Flight Center
"""

try:
    import gdal
except ImportError:
    from osgeo import gdal

import numpy as np
import os

def processHD5(inputHD5, layer, outputRaster):
    
    ## Open HDF file
    hdflayer = gdal.Open(inputHD5, gdal.GA_ReadOnly)
    subhdflayer = hdflayer.GetSubDatasets()[layer][0]
    print(subhdflayer)
    rlayer = gdal.Open(subhdflayer, gdal.GA_ReadOnly)
    
    HorizontalTileNumber = int(rlayer.GetMetadata_Dict()["HorizontalTileNumber"])
    VerticalTileNumber = int(rlayer.GetMetadata_Dict()["VerticalTileNumber"])
    
    WestBoundCoord = (10*HorizontalTileNumber) - 180
    NorthBoundCoord = 90-(10*VerticalTileNumber)
    
    EastBoundCoord = WestBoundCoord + 10
    SouthBoundCoord = NorthBoundCoord - 10
    
    EPSG = "-a_srs EPSG:4326" #WGS84
    
    translateOptionText = EPSG+" -a_ullr " + str(WestBoundCoord) + " " + str(NorthBoundCoord) + " " + str(EastBoundCoord) + " " + str(SouthBoundCoord)
    translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine(translateOptionText))
    gdal.Translate(outputRaster,rlayer, options=translateoptions)

def save_image(f,in_geo,projref,data_type,out):
    #create New Raster
    driver = gdal.GetDriverByName('GTiff')
    if driver == None:
        print ("Failed to find the gdal driver")
        exit()
    newRaster = driver.Create(out, f.shape[1], f.shape[0], 1, data_type)
    newRaster.SetProjection(projref)
    newRaster.SetGeoTransform(in_geo)
    
    outBand = newRaster.GetRasterBand(1)
    outBand.SetNoDataValue(255)
    outBand.WriteArray(f, 0, 0)
    driver = None
    outBand = None
    newRaster = None


def unpackCloud(num, upper, lower):
    start = 15 - upper
    length = (upper - lower) +1 
    bit = int('{0:016b}'.format(num)[start:][:length], 2)
    return bit

def get_arry_geo(inputImage, band):
    ds = gdal.Open(inputImage, gdal.GA_ReadOnly)
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    arry = ds.GetRasterBand(band).ReadAsArray(0,0,cols,rows)

    geo = ds.GetGeoTransform()
    proj = ds.GetProjectionRef()
    ds = None
    return arry, geo, proj

##Input Black Marble VNP46A1/A2 Product###
##Change this to your input file##
inputImage = "./VNP46A2.A2021003.h09v05.001.2021103041024.h5"

#Output Unpack Cloud Mask##
##Change this to your unpack cloud mask bit output GeoTiff file###

outputCloud = "./VNP46A2.A2021003.h09v05.001.2021103041024_Cloud_Mask_V2.tif"

temp = "./tempMaskFile.tif"

## Open HDF file
#Specify Band nuber you want to unpack bits#
#For QF_Cloud_Mask in VNP46A1, band = 11 and in VNP46A2, band = 5
#Refer to Black Marble user guide for full description##

band = 5
processHD5(inputImage, band, temp)

##Read File##
arry, geo, proj = get_arry_geo(temp, 1)

#Extract Bits
#Specify bit range
#Eg: for bit range 6-7 ((Cloud Detection Results & Confidence Indicators)) on QF_Cloud_Mask
upper = 7
lower = 6

addBitCloud = np.vectorize(unpackCloud)
unpack_arry = addBitCloud(arry, upper, lower)

#Save Image
save_image(unpack_arry, geo, proj, gdal.GDT_Byte, outputCloud)

# Delete the temp       
os.remove(temp)









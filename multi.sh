#!/usr/bin/env bash

./draw.py ~/input/ECMWF2/download.nc 0 8&
./draw.py ~/input/ECMWF2/download.nc 1 8&
./draw.py ~/input/ECMWF2/download.nc 2 8&
./draw.py ~/input/ECMWF2/download.nc 3 8&
./draw.py ~/input/ECMWF2/download.nc 4 8&
./draw.py ~/input/ECMWF2/download.nc 5 8&
./draw.py ~/input/ECMWF2/download.nc 6 8&
./draw.py ~/input/ECMWF2/download.nc 7 8
wait

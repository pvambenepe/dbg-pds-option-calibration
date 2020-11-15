import numpy as np
import pandas as pd
import datetime
import glob
pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 30)
import math
import scipy.stats as si
import statsmodels.api as sm
import matplotlib.pyplot as plt

local_data_folder = '/Users/pvamb/DBGPDS/deutsche-boerse-xetra-pds'  # do not end in /
local_data_folder_opt = '/Users/pvamb/DBGPDS/deutsche-boerse-eurex-pds'  # do not end in /
folder1 = '/Users/pvamb/DBGPDS/processed'
folder2 = '/Users/pvamb/DBGPDS/parameters'
folder3 = '/Users/pvamb/DBGPDS/XY'

opening_hours_str = "07:00"
closing_hours_str = "15:30"

stocks_list = ['DBK','EOAN', 'CBK', 'DTE', 'SVAB', 'RWE', 'IFX', 'LHA', 'DAI', 'TKA',
 'HDD', 'O2D', 'EVT', 'AIXA', 'DPW', 'SIE', 'PSM', 'BAS', 'BAYN', 'SAP', 'BMW', 'SDF',
 'VOW3', 'FRE', 'AB1', 'CEC', 'GAZ', 'VNA', 'SHA', 'B4B', 'UN01', 'ALV', 'NDX1',
 'DLG', 'ADV', 'AT1', 'NOA3', 'VODI', 'BPE5', 'HEI', 'ADS', 'KCO', 'TUI1', 'SZU',
 'DEZ', 'EVK', 'WDI', 'MRK', 'PAH3', 'G1A', 'MUV2', 'QSC', 'HEN3', 'QIA', 'TINA',
 'DWNI', 'ANO', 'ZAL', 'RKET', 'SGL', 'FME', 'IGY', '1COV', 'BVB', 'FNTN', 'DB1',
 'PBB', 'LIN', 'CON', 'UTDI', 'KGX', 'EV4', 'TEG', 'PNE3', 'OSR', 'BEI', 'LLD', 'ARL',
 'MDG1' 'LXS' 'BNR' 'GYC' 'ZIL2' 'SANT' 'AOX' 'DRI' 'TTI' 'BOSS' 'SZG'
 'RIB', 'ABR', 'DEQ', 'SOW', 'CAP', 'WAF', 'SY1', 'GBF', 'NDA', 'ADE']
stocks_list = ['SX5E', 'DAI', 'CBK', 'DBK', 'DTE', 'EOAN']
stocks_list = ['SX5E', 'DAI']


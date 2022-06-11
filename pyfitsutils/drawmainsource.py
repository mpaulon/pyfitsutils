# import astropy
# import matplotlib.pyplot as plt
# from astropy import units as u
# import aplpy
# import pylab
# from matplotlib import pyplot as plt,cm, colors as mc,patches as mpatches, colorbar as clm
# from matplotlib.colors import LogNorm
# from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
# from mpl_toolkits.axes_grid1.inset_locator import mark_inset

# from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
# import matplotlib.ticker as ticker
# from matplotlib import rc
# import numpy as np
# import os
# import re
# import csv
# import datetime

import csv
import datetime

from pathlib import Path

import aplpy
import numpy as np
import matplotlib.pyplot as plt

from .import utils

DICT_SHEET = {}
DICT_RADIUS = {"Lband" : 0.003, "Cband" : 0.0025, "Xband" : 0.002, "Kuband" : 0.0015, "Kband" : 0.001}

# position de ref du 7juin, avec erreur
TARGET = {
    "ra": 267.0210530583,
    "ra_err": 3.4002083e-05,
    "dec": -28.4738467794,
    "dec_err": 1.3663472e-05,
}

CONTOUR_COEFS = [3, 5, 10, 20, 30]


def init():
    plt.style.use('seaborn-paper')
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')
    ## commence par lecture du tableau provenant du Google Sheets
    ## il faut pouvoir récupérer max, min et rms pour chaque bande et date
    with open("XTEJ1748-288_maxminrms_Sheets.csv") as f:
        lines = csv.reader(f, delimiter = ",")
        for line in lines:
            DICT_SHEET[line[1]] = {"Lband":[line[4],line[5],line[6]], "Cband":[line[7],line[8],line[9]], "Xband":[line[10],line[11],line[12]], "Kuband":[line[13],line[14],line[15]], "Kband":[line[16],line[17],line[18]]}

def draw(date, band, sources, images_folder: Path):

    date_fmt = datetime.datetime.strptime(date, '%d%b%Y').strftime('%d/%m/%Y')
    date_save = datetime.datetime.strptime(date, '%d%b%Y').strftime('%Y-%m-%d')

    
    img_file: Path = list(images_folder.glob(f"{date}_{band}band_selfcal_rob0*"))
    
    if len(img_file) == 0:
        print(img_file, "not found")
        return None
    else:
        img_file = img_file[0]
    
    min_fichier = DICT_SHEET[date_fmt][f"{band}band"][0]
    max_fichier = DICT_SHEET[date_fmt][f"{band}band"][1]
    rms_fichier = DICT_SHEET[date_fmt][f"{band}band"][2]

    min_val_1 = float(min_fichier)
    max_val_1 = float(max_fichier)/2
    rms_1 = float(rms_fichier)

    #niveau des contours
    levels_1 = [c*rms_1 for c in CONTOUR_COEFS]

    radius = DICT_RADIUS[f"{band}band"]


    fig = plt.figure(figsize=(14, 14))

    #IMAGE FINALE
    print(img_file.as_posix())
    f1 = aplpy.FITSFigure(img_file.as_posix(), figure=fig)
    f1.recenter(TARGET["ra"],TARGET["dec"], radius)

    f1.set_theme('publication')
    f1.show_colorscale(cmap='hot',vmin=min_val_1,vmax=max_val_1) #B&W = binary

    f1.show_contour(img_file.as_posix(), levels=levels_1, colors='lime', layer='contours', linewidths = 1)

    ###pour placer une croix au coeur sans barre d'erreur, décommenter première ligne
    #f1.add_label(target_RA_ref_deg,target_DEC_ref_deg, '$\\textbf{+}$', color='magenta', size=20, layer='cross') #croix sur position target
    #f1.add_label(maxi1348_RA_ref_deg-0.005,maxi1348_DEC_ref_deg+0.003, 'MJD 58589', color='w', size=40, layer='mjd') #exemple si on veut écrire autre chose
    line_liste = [
        np.array([
            [TARGET["ra"] - TARGET["ra_err"], TARGET["ra"] + TARGET["ra_err"]],
            [TARGET["dec"], TARGET["dec"]]
        ]),
        np.array([
            [TARGET["ra"], TARGET["ra"]],
            [TARGET["dec"] - TARGET["dec_err"], TARGET["dec"] + TARGET["dec_err"]]
        ])
    ]

    f1.show_lines(line_liste,color='dodgerblue',linewidth=1.5,layer='cross')

    for i, source in enumerate(sources):
        f1.add_label(utils.ra2deg(source["ra"]),utils.dec2deg(source["dec"]), '{i}'.format(i=i), color='magenta', size=20) #croix sur position target


    f1.axis_labels.show()
    f1.tick_labels.show()
    f1.tick_labels.set_xformat('hh:mm:ss.ss')
    f1.tick_labels.set_yformat('dd:mm:ss.s')
    f1.tick_labels.set_font(size=20)
    f1.axis_labels.set_font(size=20)

    f1.set_title(f"XTE J1748-288 {date} {band} with robust=0",fontsize = 32)

    # pour la barre de 1arcsec en bas à gauche
    f1.add_scalebar(1./3600)
    f1.scalebar.set_linewidth(2)
    f1.scalebar.set_color('white')
    f1.scalebar.set_corner('bottom left')
    f1.scalebar.set_label('1 arcsec')
    f1.scalebar.set_font_size(15)



    fig.savefig(images_folder / ('XTEJ1748-288_'+date_save+'_'+band+'_rob0.png'), format='png', dpi=300, bbox_inches='tight')
    fig.savefig(images_folder / ('XTEJ1748-288_'+date_save+'_'+band+'_rob0.pdf'), bbox_inches='tight', pad_inches = 0.05)
    
    return fig



def getmain(date, band, sources, images_folder):
    fig = draw(date, band, sources, images_folder)
    if fig:
        plt.ion()
        plt.show()
        main_source = int(input("Main source: "))
        plt.close()
        for i, source in enumerate(sources):
            if i == main_source:
                source["is_main"] = 1
            else:
                source["is_main"] = 0
        return sources
    return None


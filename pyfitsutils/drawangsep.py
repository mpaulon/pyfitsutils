import datetime

import numpy as np
import matplotlib.pyplot as plt

from . import utils
# Program to calculate the angular separation between two points whose coordinates are given in DEGREES

def angsep(ra1,err_ra1,dec1,err_dec1,ra2,err_ra2,dec2,err_dec2):
    # conversion en radians
    ra1rad = ra1 * np.pi/180.0
    ra2rad = ra2 * np.pi/180.0
    dec1rad = dec1 * np.pi/180.0
    dec2rad = dec2 * np.pi/180.0

    err_ra1rad = err_ra1 * np.pi/180.0
    err_ra2rad = err_ra2 * np.pi/180.0
    err_dec1rad = err_dec1 * np.pi/180.0
    err_dec2rad = err_dec2 * np.pi/180.0

    #calcul de la séparation angulaire
    x = np.cos(ra1rad) * np.cos(dec1rad) * np.cos(ra2rad) * np.cos(dec2rad)
    y = np.sin(ra1rad) * np.cos(dec1rad) * np.sin(ra2rad) * np.cos(dec2rad)
    z = np.sin(dec1rad) * np.sin(dec2rad)

    angsep = np.arccos(x+y+z)

    angsep_deg = 180.0/np.pi * np.arccos(x+y+z)

    dd = int(angsep_deg) 
    mm = int((angsep_deg - dd)*60)
    ss = ((angsep_deg - dd)*60 - mm)*60
    
    angsep_arsec = angsep_deg*3600

    print(x,y,z)
    s = x+y+z
    coeff = 1.0/np.sqrt(1-(s)**2)
    termera1 = np.cos(dec1rad)*np.cos(dec2rad)*(np.sin(ra1rad)*np.cos(ra2rad)-np.cos(ra1rad)*np.sin(ra2rad))
    termedec1 = np.cos(ra1rad)*np.sin(dec1rad)*np.cos(ra1rad)*np.cos(dec2rad) + np.sin(ra1rad)*np.sin(dec1rad)*np.sin(ra1rad)*np.cos(dec2rad) - np.cos(dec1rad)*np.sin(dec2rad)
    termera2 = np.cos(dec1rad)*np.cos(dec2rad)*(np.cos(ra1rad)*np.sin(ra2rad)-np.sin(ra1rad)*np.cos(ra2rad))
    termedec2 = np.cos(ra1rad)*np.cos(dec1rad)*np.cos(ra1rad)*np.sin(dec2rad) + np.sin(ra1rad)*np.cos(dec1rad)*np.sin(ra1rad)*np.sin(dec2rad) - np.sin(dec1rad)*np.cos(dec2rad)

    err_angsep = coeff * ((err_ra1rad*termera1)**2 + (err_dec1rad*termedec1)**2 + (err_ra2rad*termera2)**2 + (err_dec2rad*termedec2)**2)**0.5
    err_angsep_deg = err_angsep * 180/np.pi

    de = int(err_angsep_deg) 
    me = int((err_angsep_deg - de)*60)
    se = ((err_angsep_deg - de)*60 - me)*60
    
    err_angsep_arcsec = err_angsep_deg*3600
    
    # fonction renvoie angsep en deg, puis angsep en dd mm ss, puis erreur en deg, et en dd mm ss
    #return(angsep_deg,str.zfill(str(dd),2)+":"+str.zfill(str(mm),2)+":"+str.zfill(str(ss),2),err_angsep_deg,str.zfill(str(de),2)+":"+str.zfill(str(me),2)+":"+str.zfill(str(se),2))
    
    # fonction renvoie juste angsep en arcsec puis erreur en arcsec, c'est ça dont je me sers
    return(angsep_arsec,err_angsep_arcsec)

def draw(fit_dict, band_chosen, images_folder):
    for date, bands in fit_dict.items():
        date = datetime.datetime.strptime(date, '%d%b%Y')
        for band, sourcesdata in bands.items():
            plt.figure(1)
            if band != band_chosen:
                continue
            angseps = []
            print(date, band)
            main_source = list(filter(lambda x: int(x["is_main"]) == 1, sourcesdata["sources"]))[0]
            beam_err = 0.1*np.sqrt(float(sourcesdata["data"]["minor"])*float(sourcesdata["data"]["major"]))
            for source in sourcesdata["sources"]:
                if int(source["is_main"]) == 1:
                    continue
                sep = angsep(
                    utils.ra2deg(main_source["ra"]), utils.ra2deg(main_source["ra_err"]), utils.dec2deg(main_source["dec"]), utils.dec2deg(main_source["dec_err"]),
                    utils.ra2deg(source["ra"]), utils.ra2deg(source["ra_err"]), utils.dec2deg(source["dec"]), utils.dec2deg(source["dec_err"]),
                )
                plt.errorbar(date, sep[0], yerr=np.sqrt(sep[1]**2+beam_err**2),marker="o",color="magenta", ecolor='black', linestyle='', capsize=1, elinewidth=0.5, markeredgewidth=0.3, markersize=3, markeredgecolor='black')

    plt.ylabel("Angular separation (as)")
    plt.xlabel("Date")
    plt.minorticks_on()
    plt.tick_params(axis ='both',which='both',direction = 'in', top=True, right=True)#, labelsize = 12)
    plt.savefig(images_folder / f"angsep_{band}.jpg",bbox_inches='tight',dpi=300)
    plt.savefig(images_folder / f"angsep_{band}.pdf",bbox_inches='tight')
    plt.show()



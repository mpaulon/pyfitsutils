from astropy.coordinates import Angle
import numpy as np

def convert_dec(dec: str):
    return dec.replace(".", ":", dec.count(".") -1).replace("-0", "-")


def angsep(ra1,err_ra1,dec1,err_dec1,ra2,err_ra2,dec2,err_dec2):

    #calcul de la séparation angulaire
    x = np.cos(ra1.rad) * np.cos(dec1.rad) * np.cos(ra2.rad) * np.cos(dec2.rad)
    y = np.sin(ra1.rad) * np.cos(dec1.rad) * np.sin(ra2.rad) * np.cos(dec2.rad)
    z = np.sin(dec1.rad) * np.sin(dec2.rad)

    angsep = np.arccos(x+y+z)

    s = x+y+z
    coeff = 1.0/np.sqrt(1-(s)**2)
    termera1 = np.cos(dec1.rad)*np.cos(dec2.rad)*(np.sin(ra1.rad)*np.cos(ra2.rad)-np.cos(ra1.rad)*np.sin(ra2.rad))
    termedec1 = np.cos(ra1.rad)*np.sin(dec1.rad)*np.cos(ra2.rad)*np.cos(dec2.rad) + np.sin(ra1.rad)*np.sin(dec1.rad)*np.sin(ra2.rad)*np.cos(dec2.rad) - np.cos(dec1.rad)*np.sin(dec2.rad)
    termera2 = np.cos(dec1.rad)*np.cos(dec2.rad)*(np.cos(ra1.rad)*np.sin(ra2.rad)-np.sin(ra1.rad)*np.cos(ra2.rad))
    termedec2 = np.cos(ra1.rad)*np.cos(dec1.rad)*np.cos(ra2.rad)*np.sin(dec2.rad) + np.sin(ra1.rad)*np.cos(dec1.rad)*np.sin(ra2.rad)*np.sin(dec2.rad) - np.sin(dec1.rad)*np.cos(dec2.rad)

    err_angsep = coeff * ((err_ra1.rad*termera1)**2 + (err_dec1.rad*termedec1)**2 + (err_ra2.rad*termera2)**2 + (err_dec2.rad*termedec2)**2)**0.5

    # fonction renvoie angsep en deg, puis angsep en dd mm ss, puis erreur en deg, et en dd mm ss
    #return(angsep_deg,str.zfill(str(dd),2)+":"+str.zfill(str(mm),2)+":"+str.zfill(str(ss),2),err_angsep_deg,str.zfill(str(de),2)+":"+str.zfill(str(me),2)+":"+str.zfill(str(se),2))
    
    # fonction renvoie juste angsep en arcsec puis erreur en arcsec, c'est ça dont je me sers
    return(Angle(angsep, "rad"),Angle(err_angsep,"rad"))
def convert_dec(dec: str):
    return dec.replace(".", ":", dec.count(".") -1).replace("-0", "-")

def arcsec_to_deg(arcsec):
    return arcsec

# Function to convert an RA of the form hh mm ss.ssssssss into a float in degrees
# Expects coordinates in the form HH:MM:SS.SSSSS !!!

def ra2deg(coords):
    ra=str.split(coords, ":")
    if len(ra) == 1:
        ra = [0,0,ra[0]]
    hh=float(ra[0])*15
    mm=(float(ra[1])/60)*15
    ss=(float(ra[2])/3600)*15
    return(hh+mm+ss)


# Function to convert a Dec of the form dd mm ss.ssssssss into a float in degrees
# Expects coordinates in the form DD:MM:SS.SSSSS !!!

def dec2deg(coords):
    dec=str.split(coords, ":")
    #print(dec)
    if len(dec) == 1:
        dec = [0,0, dec[0]]
    dd=abs(float(dec[0]))
    mm=float(dec[1])/60
    ss=float(dec[2])/3600
    if float(dec[0]) < 0:
        return(-(dd+mm+ss))
    else:
        return(dd+mm+ss)
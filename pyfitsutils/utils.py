def convert_dec(dec: str):
    return dec.replace(".", ":", dec.count(".") -1).replace("-0", "-")

def arcsec_to_deg(arcsec):
    return arcsec
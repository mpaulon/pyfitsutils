from astropy.coordinates import Angle
LIST_DICT_SHEET = []
DICT_RADIUS = {"Lband" : 0.003, "Cband" : 0.0025, "Xband" : 0.002, "Kuband" : 0.0015, "Kband" : 0.001}

WINDOW_SIZE = 8
LABEL_SIZE = 12
AXIS_SIZE = 10
TITLE_SIZE = 20
LEGEND_SIZE = 10

# position de ref du 7juin, avec erreur
TARGET = {
    "ra": Angle(267.0210530583, "deg"),
    "ra_err": Angle(3.4002083e-05, "deg"),
    "dec": Angle(-28.4738467794, "deg"),
    "dec_err": Angle(1.3663472e-05, "deg"),
}

CONTOUR_COEFS = [3, 5, 10, 20, 30]
COLORS = ["magenta", "green", "red", "blue"]
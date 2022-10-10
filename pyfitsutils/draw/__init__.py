import csv
import datetime
import logging

from pathlib import Path
from typing import Optional

import aplpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

from astropy.time import Time

from pyfitsutils import utils, settings

logger = logging.getLogger(__name__)

def init():
    plt.style.use('seaborn-paper')
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')

    ## commence par lecture du tableau provenant du Google Sheets
    ## il faut pouvoir récupérer max, min et rms pour chaque bande et date
    with open("XTEJ1748-288_maxminrms_Sheets.csv") as f:
        lines = csv.reader(f, delimiter = ",")
        for line in lines:
            settings.DICT_SHEET[line[1]] = {"Lband":[line[4],line[5],line[6]], "Cband":[line[7],line[8],line[9]], "Xband":[line[10],line[11],line[12]], "Kuband":[line[13],line[14],line[15]], "Kband":[line[16],line[17],line[18]]}


def load_fits(images_folder: Path, date: datetime.datetime, band: str) -> Optional[Path]:
    image_glob = f"{date.strftime('%d%b%Y').lower()}_{band}band_selfcal_rob0*"
    fits_images = list(images_folder.glob(image_glob))
    if len(fits_images) == 1:
        return fits_images[0]
    else:
        logger.warning(f"Image matching {image_glob} not found in {images_folder}")
        return None

def draw_target(fig, target, label="", cross=True):
    logger.info(f"Adding target {label} at coordinates {target}")
    line_liste = [
        np.array([
            [target["ra"].deg - target["ra_err"].deg, target["ra"].deg + target["ra_err"].deg],
            [target["dec"].deg, target["dec"].deg]
        ]),
        np.array([
            [target["ra"].deg, target["ra"].deg],
            [target["dec"].deg - target["dec_err"].deg, target["dec"].deg + target["dec_err"].deg]
        ])
    ]
    if cross:
        fig.show_lines(line_liste,color='dodgerblue',linewidth=1.5)
    if label:
        fig.add_label(target["ra"].deg, target["dec"].deg, label, color='dodgerblue', size=settings.LABEL_SIZE)

def draw_sources(date: datetime.date, band: str, sources: list, imagesfolder:Path, output: Path, contours: bool, save: bool):
    img = load_fits(imagesfolder, date, band)
    if not img:
        return

    min_val, max_val, rms = (float(x) for x in settings.DICT_SHEET[date.strftime('%d/%m/%Y')][f"{band}band"][0:3])
    max_val = max_val / 2

    levels = [c*rms for c in settings.CONTOUR_COEFS]

    radius = settings.DICT_RADIUS[f"{band}band"]

    fig = plt.figure(figsize=(8, 8)) # defines a new figure and set it's size to 8cm (inches ?)

    logger.info(f"Processing {img}")

    fig1 = aplpy.FITSFigure(img.as_posix(), figure=fig, auto_refresh=False) # not sure if auto_refresh is usefull
    logger.info("Centering image")
    fig1.recenter(settings.TARGET["ra"].deg, settings.TARGET["dec"].deg, radius) # center and zoom on the target location

    fig1.set_theme('publication')
    fig1.show_colorscale(cmap='hot',vmin=min_val,vmax=max_val) # set the colorscale of the figure

    # add contour /!\ VERY SLOW !!!
    if contours:
        logger.info("Adding contours")
        fig1.show_contour(img.as_posix(), levels=levels, colors='lime', layer='contours', linewidths = 1)

    draw_target(fig1, settings.TARGET) # show target as a blue cross with error bars on the figure

    line_27jun = np.array([
            [267.021252 - 9.58333333333e-07, 267.021252 + 9.58333333333e-07],
            [-28.4737730833, -28.4737730833]
        ]),np.array([
            [267.021252, 267.021252],
            [-28.4737730833 - 1.66944444444e-06, -28.4737730833 + 1.66944444444e-06]
        ])
        
    fig1.show_lines(line_27jun,color='pink',linewidth=1.5) #croix 27jun1999

    line_26oct = np.array([
            [267.021248292 - 4.58333333333e-06, 267.021248292 + 4.58333333333e-06],
            [-28.4737315028, -28.4737315028]
        ]),np.array([
            [267.021248292, 267.021248292],
            [-28.4737315028 - 1.18416666667e-05, -28.4737315028 + 1.18416666667e-05]
        ])
        
    fig1.show_lines(line_26oct,color='green',linewidth=1.5) #croix 26oct2000

    # add label for each source
    for i, source in enumerate(sources):
        draw_target(fig1, source, label=str(i), cross=False)

    fig1.axis_labels.show()
    fig1.tick_labels.show()
    fig1.tick_labels.set_xformat('hh:mm:ss.ss')
    fig1.tick_labels.set_yformat('dd:mm:ss.s')
    fig1.tick_labels.set_font(size=settings.AXIS_SIZE)
    fig1.axis_labels.set_font(size=settings.AXIS_SIZE)

    fig1.set_title(f"XTE J1748-288 {date.strftime('%Y-%m-%d')} {band} with robust=0",fontsize = settings.TITLE_SIZE)

    # pour la barre de 1arcsec en bas à gauche
    fig1.add_scalebar(1./3600)
    fig1.scalebar.set_linewidth(2)
    fig1.scalebar.set_color('white')
    fig1.scalebar.set_corner('bottom left')
    fig1.scalebar.set_label('1 arcsec')
    fig1.scalebar.set_font_size(settings.LEGEND_SIZE)

    if save:
        logger.info("Saving figures")
        fig.savefig(output / (f"XTEJ1748-288_{date.strftime('%Y-%m-%d')}_{band}_rob0.png"), format='png', dpi=300, bbox_inches='tight')
        fig.savefig(output / (f"XTEJ1748-288_{date.strftime('%Y-%m-%d')}_{band}_rob0.pdf"), bbox_inches='tight', pad_inches = 0.05)
    
    return fig

def draw_angsep(fit_dict: dict, band_chosen: str, output: Path, leftmost=False, rightmost=False):
    for date, bands in fit_dict.items():
        for band, sourcesdata in bands.items():
            plt.figure(1)
            if band != band_chosen:
                continue
            if leftmost:
                sourcesdata["sources"].sort(key=lambda x: x["ra"], reverse=True)
                main_source = sourcesdata["sources"][0]
            elif rightmost:
                sourcesdata["sources"].sort(key=lambda x: x["ra"])
                main_source = sourcesdata["sources"][0]
            else:
                main_source = list(filter(lambda x: int(x["is_main"]) == 1, sourcesdata["sources"]))[0]
            beam_err = 0.1*np.sqrt(float(sourcesdata["data"]["minor"])*float(sourcesdata["data"]["major"]))
            for source in sourcesdata["sources"]:
                if source == main_source:
                    continue
                sep = utils.angsep(
                    main_source["ra"], main_source["ra_err"], main_source["dec"], main_source["dec_err"],
                    source["ra"], source["ra_err"], source["dec"], source["dec_err"],
                )
                if source["ra"].arcsec > main_source["ra"].arcsec:
                    plt.errorbar(Time(date).mjd, -sep[0].arcsec, yerr=sep[1].arcsec,marker="o",color="magenta", ecolor='black', linestyle='', capsize=1, elinewidth=0.5, markeredgewidth=0.3, markersize=3, markeredgecolor='black')
                else:
                    plt.errorbar(Time(date).mjd, sep[0].arcsec, yerr=sep[1].arcsec,marker="o",color="magenta", ecolor='black', linestyle='', capsize=1, elinewidth=0.5, markeredgewidth=0.3, markersize=3, markeredgecolor='black')


    plt.ylabel("Angular separation (as)")
    plt.xlabel("Date")
    plt.minorticks_on()
    plt.tick_params(axis='both',which='both',direction = 'in', top=True, right=True)#, labelsize = 12)
    plt.xticks(rotation=90)
    plt.gca().xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x,_: f"({Time(x,format='mjd').to_value('iso', subfmt='date')}) {x}"))
    plt.savefig(output / f"angsep_{band_chosen}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{'left' if leftmost else 'right' if rightmost else ''}.jpg",bbox_inches='tight',dpi=300)
    plt.savefig(output / f"angsep_{band_chosen}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{'left' if leftmost else 'right' if rightmost else ''}.pdf",bbox_inches='tight')
    plt.show()

def draw_rasep(fit_dict: dict, band_chosen: str, output: Path, leftmost=False, rightmost=False, reference=False):
    for date, bands in fit_dict.items():
        for band, sourcesdata in bands.items():
            plt.figure(1)
            if band != band_chosen:
                continue
            if leftmost:
                sourcesdata["sources"].sort(key=lambda x: x["ra"], reverse=True)
                main_source = sourcesdata["sources"][0]
            elif rightmost:
                sourcesdata["sources"].sort(key=lambda x: x["ra"])
                main_source = sourcesdata["sources"][0]
            elif target:
                main_source = target
            else:
                main_source = list(filter(lambda x: int(x["is_main"]) == 1, sourcesdata["sources"]))[0]
            
            for source in sourcesdata["sources"]:
                if source == main_source:
                    continue
                sep = utils.rasep(
                    main_source["ra"], main_source["ra_err"],
                    source["ra"], source["ra_err"], 
                )
                if source["ra"].arcsec > main_source["ra"].arcsec:
                    plt.errorbar(Time(date).mjd, -sep[0].arcsec, yerr=sep[1].arcsec,marker="o",color="magenta", ecolor='black', linestyle='', capsize=1, elinewidth=0.5, markeredgewidth=0.3, markersize=3, markeredgecolor='black')
                else:
                    plt.errorbar(Time(date).mjd, sep[0].arcsec, yerr=sep[1].arcsec,marker="o",color="magenta", ecolor='black', linestyle='', capsize=1, elinewidth=0.5, markeredgewidth=0.3, markersize=3, markeredgecolor='black')


    plt.ylabel("RA Separation (as)")
    plt.xlabel("Date")
    plt.minorticks_on()
    plt.tick_params(axis='both',which='both',direction = 'in', top=True, right=True)#, labelsize = 12)
    plt.xticks(rotation=90)
    plt.gca().xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x,_: f"({Time(x,format='mjd').to_value('iso', subfmt='date')}) {x}"))
    plt.savefig(output / f"rasep_{band_chosen}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{'left' if leftmost else 'right' if rightmost else 'reference' if reference else ''}.jpg",bbox_inches='tight',dpi=300)
    plt.savefig(output / f"rasep_{band_chosen}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{'left' if leftmost else 'right' if rightmost else 'reference' if reference else ''}.pdf",bbox_inches='tight')
    plt.show()


def draw_flux(fit_dict: dict, band_chosen: str, output: Path, leftmost=False, rightmost=False):
    for date, bands in fit_dict.items():
        for band, sourcesdata in bands.items():
            plt.figure(1)
            if band != band_chosen:
                continue
            if leftmost:
                sourcesdata["sources"].sort(key=lambda x: x["ra"], reverse=True)
                main_source = sourcesdata["sources"][0]
            elif rightmost:
                sourcesdata["sources"].sort(key=lambda x: x["ra"])
                main_source = sourcesdata["sources"][0]
            else:
                main_source = list(filter(lambda x: int(x["is_main"]) == 1, sourcesdata["sources"]))[0]
            plt.errorbar(Time(date).mjd, main_source["flux"], yerr=main_source["flux_err"],marker="o",color="magenta", ecolor='black', linestyle='', capsize=1, elinewidth=0.5, markeredgewidth=0.3, markersize=3, markeredgecolor='black')
    plt.ylabel("Flux (mJy)")
    plt.xlabel("Date")
    plt.minorticks_on()
    plt.tick_params(axis='both',which='both',direction = 'in', top=True, right=True)#, labelsize = 12)
    plt.xticks(rotation=90)
    plt.gca().xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x,_: f"({Time(x,format='mjd').to_value('iso', subfmt='date')}) {x}"))
    plt.savefig(output / f"flux_{band_chosen}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{'left' if leftmost else 'right' if rightmost else ''}.jpg",bbox_inches='tight',dpi=300)
    plt.savefig(output / f"flux_{band_chosen}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{'left' if leftmost else 'right' if rightmost else ''}.pdf",bbox_inches='tight')
    plt.show()


def draw_angsep_brightest(fit_dict: dict, band_chosen: str, output: Path, leftmost=False, rightmost=False):
    for date, bands in fit_dict.items():
        for band, sourcesdata in bands.items():
            plt.figure(1)
            if band != band_chosen:
                continue
            if leftmost:
                sourcesdata["sources"].sort(key=lambda x: x["ra"], reverse=True)
                main_source = sourcesdata["sources"][0]
                not_main_sources = sourcesdata["sources"][1:]
            elif rightmost:
                sourcesdata["sources"].sort(key=lambda x: x["ra"])
                main_source = sourcesdata["sources"][0]
                not_main_sources = sourcesdata["sources"][1:]
            else:
                main_source = list(filter(lambda x: int(x["is_main"]) == 1, sourcesdata["sources"]))[0]
                not_main_sources = list(filter(lambda x: int(x["is_main"]) != 1, sourcesdata["sources"]))

            not_main_sources.sort(key=lambda x: x["flux"], reverse=True)
            if len(not_main_sources) == 0:
            #    continue # si tu veux juste ne rien faire
            # ou alors
                plt.errorbar(Time(date).mjd, 0, yerr=0,marker="o",color="red", ecolor='black', linestyle='', capsize=1, elinewidth=0.5, markeredgewidth=0.3, markersize=3, markeredgecolor='black') 
                continue # si tu veux mettre un point à 0
            source = not_main_sources[0]
            sep = utils.angsep(
                    main_source["ra"], main_source["ra_err"], main_source["dec"], main_source["dec_err"],
                    source["ra"], source["ra_err"], source["dec"], source["dec_err"],
                )
            plt.errorbar(Time(date).mjd, sep[0].arcsec, yerr=sep[1].arcsec,marker="o",color="magenta", ecolor='black', linestyle='', capsize=1, elinewidth=0.5, markeredgewidth=0.3, markersize=3, markeredgecolor='black')

    plt.ylabel("Angular separation vs brightest (as)")
    plt.xlabel("Date")
    plt.minorticks_on()
    plt.tick_params(axis='both',which='both',direction = 'in', top=True, right=True)#, labelsize = 12)
    plt.xticks(rotation=90)
    plt.gca().xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda x,_: f"({Time(x,format='mjd').to_value('iso', subfmt='date')}) {x}"))
    plt.savefig(output / f"angsep_brightest_{band_chosen}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{'left' if leftmost else 'right' if rightmost else ''}.jpg",bbox_inches='tight',dpi=300)
    plt.savefig(output / f"angsep_brightest_{band_chosen}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}{'left' if leftmost else 'right' if rightmost else ''}.pdf",bbox_inches='tight')
    plt.show()


def getmain(date: datetime.date, band: str, sources: list, imagesfolder:Path, output: Path, contours: bool, save: bool):
    fig = draw_sources(
        date=date, 
        band=band, 
        sources=sources,
        imagesfolder=imagesfolder, 
        output=output, 
        contours=contours, 
        save=save
    )
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


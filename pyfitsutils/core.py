import datetime
import logging
import re

from decimal import Decimal
from pathlib import Path
from typing import Any, Tuple


from astropy.coordinates import Angle
from numpy import require

from . import utils, draw #, drawangsep

logger = logging.getLogger()
logging.getLogger("matplotlib").setLevel("WARNING")
logging.getLogger("PIL").setLevel("WARNING")
stdout_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(stdout_formatter)

logger.addHandler(stdout_handler)
logger.setLevel("DEBUG")


def fit_block_to_source_dict(fit_block: list[str]) -> Tuple[dict[str, str],dict[str, str]]:
    """Take a block for a measurement in a fit file an return the corresponding dictionary"""
    source_dict = {"is_main": ""}
    band_dict = {}
    for i, line in enumerate(fit_block):
        line = line.strip()
        if line.startswith("--- ra:") and not line.endswith("pixels"):
            matches = re.search(r"(?P<value>[0-9:\.]+)\s\+\/\-\s(?P<error>[0-9\.]+)\ss", line)
            source_dict["ra"] = Angle(matches.group("value"), "hourangle")
            source_dict["ra_err"] = Angle("00:00:" + matches.group("error"), "hourangle")
        elif line.startswith("--- dec:") and not line.endswith("pixels"):
            matches = re.search(r"(?P<value>\-?[0-9\.]+)\s\+\/\-\s(?P<error>[0-9\.]+)\sarcsec", line)
            source_dict["dec"] = Angle(utils.convert_dec(matches.group("value")), "deg")
            source_dict["dec_err"] = Angle("00:00:" + matches.group("error"), "deg")
        elif line.startswith("Clean beam size"):
            matches = re.search(r"(?P<value>\-?[0-9\.]+)\sarcsec", fit_block[i+1].strip())
            band_dict["major"] = matches.group("value")
            matches = re.search(r"(?P<value>\-?[0-9\.]+)\sarcsec", fit_block[i+2].strip())
            band_dict["minor"] = matches.group("value")
        elif line.startswith("--- Integrated:"):
            matches = re.search(r"(?P<value>[0-9\.]+)\s\+\/\-\s(?P<error>[0-9\.]+\s[mu])Jy", line)
            if matches.group("error").endswith("u"):
                source_dict["flux"] = Decimal(matches.group("value"))/1000
                source_dict["flux_err"] = Decimal(matches.group("error").strip("u "))/1000
            else:                
                source_dict["flux"] = Decimal(matches.group("value"))
                source_dict["flux_err"] = Decimal(matches.group("error").strip("m "))
        elif line.startswith("--- frequency:"):
            matches = re.search(r"(?P<value>[0-9\.]+)\sGHz", line)
            band_dict["freq"] = matches.group("value")
    return source_dict, band_dict


def fit_folder_to_dict(fit_folder: Path) -> dict[str,Any]:
    """Take the path of a folder containing fit files and return the corresponding dict"""
    
    fits_dict = {}
    for fit_file in fit_folder.iterdir():
        with open(fit_file) as f:
            logger.info(f"Loading fit data from {fit_file}")
            current_block = []
            for line in f:
                line = line.strip()
                # TODO: get date
                matches = re.search(r"_(?P<date>[0-9a-zA-Z]+)_(?P<band>[A-Za-z]+)band", fit_file.as_posix())
                fit_freq = matches.group("band")
                fit_date = datetime.datetime.strptime(matches.group("date"), "%d%b%Y")

                if not fits_dict.get(fit_date):
                    fits_dict[fit_date] = {
                        fit_freq: {}
                    }

                if not fits_dict[fit_date].get(fit_freq):
                    fits_dict[fit_date][fit_freq] = {}

                if line.startswith("Fit on"):
                    if current_block:
                        s_d, b_d = fit_block_to_source_dict(current_block)
                        fits_dict[fit_date][fit_freq]["data"] = b_d
                        if not fits_dict[fit_date][fit_freq].get("sources"):
                            fits_dict[fit_date][fit_freq]["sources"] = []
                        fits_dict[fit_date][fit_freq]["sources"].append(s_d)
                        current_block = []
                    current_block.append(line)

                elif current_block:
                    current_block.append(line)

            if current_block:
                s_d, b_d = fit_block_to_source_dict(current_block)
                fits_dict[fit_date][fit_freq]["data"] = b_d
                if not fits_dict[fit_date][fit_freq].get("sources"):
                    fits_dict[fit_date][fit_freq]["sources"] = []
                fits_dict[fit_date][fit_freq]["sources"].append(s_d)

    return fits_dict

def fit_dict_to_csv(fit_dict: dict[str,Any], filename: Path):
    """Take the dict generated by fit_folder_to_dict() and write it to the specified csv"""
    logger.info(f"Saving data to {filename}")
    with open(filename, "w") as f:
        for date, bands in fit_dict.items():
            for band, data_sources in bands.items():
                line = ",".join([
                    date.strftime("%d%b%Y"),
                    band,
                    data_sources["data"]["freq"],
                    data_sources["data"]["major"],
                    data_sources["data"]["minor"],
                    *[",".join([
                        s["ra"].to_string(sep=":"),
                        s["ra_err"].to_string(sep=":"),
                        s["dec"].to_string(sep=":"),
                        s["dec_err"].to_string(sep=":"),
                        str(s["flux"]),
                        str(s["flux_err"]),
                        str(s["is_main"]),
                    ]) for s in data_sources["sources"]]
                ])
                f.write(line + "\n")

SOURCE_LEN = 7

def fit_csv_to_dict(fit_csv: Path):
    """Return a fit dict from a specified csv"""
    with open(fit_csv) as f:
        fits_dict = {}
        for line in f:
            line = line.strip().split(",")
            fit_date = datetime.datetime.strptime(line[0], '%d%b%Y')
            fit_freq = line[1]
            if not fits_dict.get(fit_date):
                fits_dict[fit_date] = {
                    fit_freq: {}
                }
            if not fits_dict[fit_date].get(fit_freq):
                fits_dict[fit_date][fit_freq] = {}
            
            fits_dict[fit_date][fit_freq] ={
                "data": dict(zip(["freq", "major", "minor"], line[2:5]))
            }
            fits_dict[fit_date][fit_freq]["sources"] = []
            for i in range(5, len(line[5:]), SOURCE_LEN):
                fits_dict[fit_date][fit_freq]["sources"].append(
                    {
                        "ra": Angle(line[i], "hourangle"),
                        "ra_err": Angle(line[i+1], "hourangle"),
                        "dec": Angle(line[i+2], "deg"),
                        "dec_err": Angle(line[i+3], "deg"),
                        "flux": Decimal(line[i+4]),
                        "flux_err": Decimal(line[i+5]),
                        "is_main": line[i+6]
                    }
                )
    return fits_dict

def are_same(d1, d2, ignore_keys=[]):
    for key, value in d1.items():
        if key in ignore_keys:
            continue
        if d2.get(key) is None:
            return False
        if isinstance(value, Angle) and value.deg == d2.get(key).deg:
            continue
        elif isinstance(value, Decimal) and not value.compare(d2.get(key)):
            continue
        elif d2.get(key) != value:
            return False
    return True

def merge_dicts(new_dict, old_dict):
    if old_dict == {}:
        return new_dict
    for date, bands in new_dict.items():
        for band, datasources in bands.items():
            new_sources = []
            for source in datasources["sources"]:
                matching_sources = list(filter(lambda x: are_same(x, source, ["is_main"]), old_dict.get(date, {}).get(band, {}).get("sources", [])))
                if len(matching_sources) == 1:

                    source["is_main"] = matching_sources[0].get("is_main", "")
                new_sources.append(source)
                new_dict[date][band]["sources"] = new_sources
    return new_dict

def cli():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fitsfolder", type=Path, help="folder containing fit files")
    parser.add_argument("--csv", type=Path, help="csv file will be saved here", required=True)
    parser.add_argument("--imagesfolder", type=Path, help="folder containing fits images")
    parser.add_argument("--output", type=Path, help="output folder")
    parser.add_argument("--contours", action="store_true", help="draw contours")
    parser.add_argument("--save", action="store_true", help="save figures")
    parser.add_argument("--drawband", type=str, help="draw only images for this specific band")
    parser.add_argument("--draw", action="store_true", help="WIP: draw figures")
    parser.add_argument("--getmain", action="store_true", help="draw figures and ask for input to get main source")
    parser.add_argument("--forcegetmain", action="store_true", help="force getmain to ignore already checked sources")
    parser.add_argument("--drawangsep", type=str, help="draw angsep for specified band")
    parser.add_argument("--leftmost", action="store_true", help="draw angsep using leftmost source as main")
    args = parser.parse_args()

    if args.fitsfolder:
        fit_dict = fit_folder_to_dict(args.fitsfolder) # generate fit_dict from fits txt files
        if args.csv.exists(): # if we have an old csv file get the is_main data
            orig_dict = fit_csv_to_dict(args.csv)
            fit_dict = merge_dicts(fit_dict, orig_dict)
        fit_dict_to_csv(fit_dict, args.csv) # save everything to the csv
    fit_dict = fit_csv_to_dict(args.csv) # just get the data from the csv

    if args.draw:
        draw.init()
        for date, bands in fit_dict.items():
            for band, datasources in bands.items():
                if args.drawband and not band == args.drawband:
                    continue
                draw.draw_sources(
                    date=date, 
                    band=band, 
                    sources=datasources["sources"], 
                    imagesfolder=args.imagesfolder, 
                    output=args.output, 
                    contours=args.contours, 
                    save=args.save
                )

    elif args.getmain or args.drawangsep:
        draw.init()
        for date, bands in fit_dict.items():
            for band, datasources in bands.items():
                if any([s["is_main"] == "" for s in datasources["sources"]]) or args.forcegetmain:
                    sources = draw.getmain(
                        date=date, 
                        band=band, 
                        sources=datasources["sources"], 
                        imagesfolder=args.imagesfolder, 
                        output=args.output, 
                        contours=args.contours, 
                        save=args.save
                    )
                sources = datasources["sources"]
                if sources is None:
                    continue
                fit_dict[date][band]["sources"] = sources
                fit_dict_to_csv(fit_dict, args.csv)
    
    if args.drawangsep:
        draw.draw_angsep(
            fit_dict,
            args.drawangsep,
            args.output,
            args.leftmost
        )

if __name__ == "__main__":
    cli()
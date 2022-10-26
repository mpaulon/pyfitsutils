import logging

from pathlib import Path

from . import draw, fits

logger = logging.getLogger()
logging.getLogger("matplotlib").setLevel("WARNING")
logging.getLogger("PIL").setLevel("WARNING")
stdout_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(stdout_formatter)

logger.addHandler(stdout_handler)
logger.setLevel("DEBUG")




def cli():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fitsfolder", type=Path, action="append", help="folder containing fit files")
    parser.add_argument("--csv", type=Path, action="append", help="csv file will be saved here", required=True)
    parser.add_argument("--imagesfolder", action="append", type=Path, help="folder containing fits images")
    parser.add_argument("--rmscsv", action="append", type=Path, help="csv file containing min/max rms values")
    parser.add_argument("--output", type=Path, help="output folder")
    parser.add_argument("--contours", action="store_true", help="draw contours")
    parser.add_argument("--save", action="store_true", help="save figures")
    parser.add_argument("--drawband", type=str, help="draw only images for this specific band")
    parser.add_argument("--draw", action="store_true", help="WIP: draw figures")
    parser.add_argument("--getmain", action="store_true", help="draw figures and ask for input to get main source")
    parser.add_argument("--forcegetmain", action="store_true", help="force getmain to ignore already checked sources [--getmain]")
    parser.add_argument("--drawangsep", type=str, help="draw angsep for specified band")
    parser.add_argument("--drawrasep", type=str, help="draw ra separation for specified band")
    parser.add_argument("--drawangsepbrightest", type=str, help="draw angsep vs brightest for specified band")
    parser.add_argument("--drawflux", type=str, help="draw flux for specified band")
    parser.add_argument("--leftmost", action="store_true", help="draw angsep using leftmost source as main [--drawangsep]")
    parser.add_argument("--rightmost", action="store_true", help="draw angsep using rightmost source as main [--drawangsep]")
    parser.add_argument("--reference", action="store_true", help="draw rasep using reference source as main [--drawrasep]")
    parser.add_argument("--maxdate", type=int, help="do not draw anything more recent than maxdate")
    parser.add_argument("--listdate", type=Path, help="draw only dates from the list")
    args = parser.parse_args()

    assert len(args.imagesfolder) == len(args.csv), "there should be the same amount of images folders and csv files"

    fit_dicts = list(fits.Fit.folders_and_csv2dict(args.csv, args.fitsfolder))

    if args.draw or args.getmain or args.drawangsep or args.drawangsepbrightest or args.drawrasep or args.drawflux:
        draw.init(args.rmscsv)

    if args.draw:
        for i, f_dict in enumerate(fit_dicts):
            for date, bands in f_dict.items():
                for band, datasources in bands.items():
                    if args.drawband and not band == args.drawband:
                        continue
                    draw.draw_sources(
                        date=date, 
                        band=band, 
                        sources=datasources["sources"], 
                        imagesfolder=args.imagesfolder[i], 
                        output=args.output, 
                        contours=args.contours, 
                        save=args.save,
                        data_index=i
                    )

    elif args.getmain or args.drawangsep or args.drawangsepbrightest or args.drawrasep or args.drawflux:
        for i, f_dict in enumerate(fit_dicts):
            for date, bands in f_dict.items():
                for band, datasources in bands.items():
                    if not (args.leftmost or args.rightmost) and (any([s["is_main"] == "" for s in datasources["sources"]]) or args.forcegetmain):
                        sources = draw.getmain(
                            date=date, 
                            band=band, 
                            sources=datasources["sources"], 
                            imagesfolder=args.imagesfolder[i], 
                            output=args.output, 
                            contours=args.contours,
                            save=args.save,
                            data_index=i
                        )
                    sources = datasources["sources"]
                    if sources is None:
                        continue
                    f_dict[date][band]["sources"] = sources
                    fits.Fit.dict2csv(f_dict, args.csv[i])
    
    if args.drawangsep:
        draw.draw_angsep(
            fit_dicts,
            args.drawangsep,
            args.output,
            args.leftmost,
            args.rightmost,
            args.maxdate,
            args.listdate
        )

    if args.drawrasep:
        draw.draw_rasep(
            fit_dicts,
            args.drawrasep,
            args.output,
            args.leftmost,
            args.rightmost,
            args.reference,
            args.maxdate,
            args.listdate
        )

    if args.drawangsepbrightest:
        draw.draw_angsep_brightest(
            fit_dicts,
            args.drawangsepbrightest,
            args.output,
            args.leftmost,
            args.rightmost,
            args.maxdate,
            args.listdate
        )

    if args.drawflux:
        draw.draw_flux(
            fit_dicts,
            args.drawflux,
            args.output,
            args.leftmost,
            args.rightmost,
            args.maxdate,
            args.listdate
        )

if __name__ == "__main__":
    cli()
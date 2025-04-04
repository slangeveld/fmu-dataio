"""Export 3D griddata with properties."""

import logging
import pathlib

import xtgeo

from fmu import dataio
from fmu.config import utilities as ut

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

CFG = ut.yaml_load("../../fmuconfig/output/global_variables.yml")

FOLDER = pathlib.Path("../output/grids")
GFILE = "gg"
GNAME = "geogrid"
PROPS_SEISMIC = ["phit", "sw"]
PROPS_OTHER = ["klogh", "facies"]


def export_geogrid_geometry():
    """Export geogrid geometry"""

    filename = (FOLDER / GFILE).with_suffix(".roff")
    grd = xtgeo.grid_from_file(filename)

    ed = dataio.ExportData(
        config=CFG,
        name=GNAME,
        content="depth",
        unit="m",
        vertical_domain="depth",
        domain_reference="msl",
        timedata=None,
        is_prediction=True,
        is_observation=False,
        tagname="",
        workflow="rms structural model",
    )

    out = ed.export(grd)
    print(f"Exported geogrid geometry to file {out}")
    return out


def export_geogrid_parameters(outgrid):
    """Export geogrid assosiated parameters based on user defined lists"""

    props = PROPS_SEISMIC + PROPS_OTHER

    for propname in props:
        filename = (FOLDER / (GFILE + "_" + propname)).with_suffix(".roff")
        prop = xtgeo.gridproperty_from_file(filename)
        ed = dataio.ExportData(
            name=propname,
            geometry=outgrid,
            config=CFG,
            content="property",
            content_metadata={"is_discrete": False},
            vertical_domain="depth",
            domain_reference="msl",
            timedata=None,
            is_prediction=True,
            is_observation=False,
            workflow="rms property model",
        )

        out = ed.export(prop)
        print(f"Exported {propname} property geogrid to file {out}")


def main():
    print("\nExporting geogrids and metadata...")
    outgrid = export_geogrid_geometry()
    export_geogrid_parameters(outgrid)
    print("Done exporting geogrids and metadata.")


if __name__ == "__main__":
    main()

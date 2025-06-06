from collections.abc import MutableMapping
from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias, Union

from pydantic import Field

if TYPE_CHECKING:
    import pathlib

    from pandas import DataFrame
    from pyarrow import Table
    from xtgeo.cube import Cube
    from xtgeo.grid3d import Grid, GridProperty
    from xtgeo.surface import RegularSurface
    from xtgeo.xyz import Points, Polygons

    from fmu.dataio._readers.tsurf import TSurfData

    from ._readers.faultroom import FaultRoomSurface

    # Local proxies due to xtgeo at the time of writing
    # not having stubs/marked itself as a typed library.
    # Ref.: https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-library-stubs-or-py-typed-marker
    class CubeProxy(Cube): ...

    class GridProxy(Grid): ...

    class GridPropertyProxy(GridProperty): ...

    class RegularSurfaceProxy(RegularSurface): ...

    class PointsProxy(Points): ...

    class PolygonsProxy(Polygons): ...

    Inferrable: TypeAlias = Annotated[
        CubeProxy
        | GridPropertyProxy
        | GridProxy
        | PointsProxy
        | PolygonsProxy
        | RegularSurfaceProxy
        | DataFrame
        | FaultRoomSurface
        | TSurfData
        | MutableMapping
        | Table
        | pathlib.Path
        | str,
        "Collection of 'inferrable' objects with metadata deduction capabilities",
    ]

VersionStr: TypeAlias = Annotated[
    str, Field(pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
]

MD5HashStr: TypeAlias = Annotated[str, Field(pattern=r"^([a-f\d]{32}|[A-F\d]{32})$")]

Parameters: TypeAlias = Annotated[
    MutableMapping[str, Union[str, float, int, None, "Parameters"]],
    "Nested or flat configurations for dynamically structured parameters.",
]

Efolder: TypeAlias = Literal[
    "maps",
    "polygons",
    "points",
    "cubes",
    "grids",
    "tables",
    "dictionaries",
]

Layout: TypeAlias = Literal[
    "regular",
    "unset",
    "cornerpoint",
    "table",
    "dictionary",
    "faultroom_triangulated",
]

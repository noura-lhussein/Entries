"""Re-exports of the real sector models under the names master_data used.

Before the merge these were `managed = False` mirrors: report_moe could not import
moeds' models, so it declared its own copies pointing at the same tables. One
backend makes that unnecessary — the registry now works on the real models, and
these aliases exist only so `registry.py` and the views keep their vocabulary.

The alias names differ from the model names on purpose: `OilField` reads better in
a cross-sector catalog than a bare `Field`.
"""

from datasets.models import Dataset, DatasetResource
from electricity.operational_models import (
    FuelTankStation,
    HydroDam,
    LoadGovernorate,
    PowerPlant,
    Substation,
    TransmissionLine,
)
from geology.models import OreProduct
from oil_gas.operational_models import (
    Facility as OilFacility,
)
from oil_gas.operational_models import (
    Field as OilField,
)
from oil_gas.operational_models import (
    Pipeline as OilPipeline,
)
from oil_gas.operational_models import (
    Refinery as OilRefinery,
)
from oil_gas.operational_models import (
    Well as OilWell,
)
from projects.models import ProjectGovernorate, ProjectOrganization
from water.models import (
    Dam,
    DrinkingWaterStation,
    RainfallBasin,
    RainfallStation,
)

__all__ = [
    "Dam",
    "Dataset",
    "DatasetResource",
    "DrinkingWaterStation",
    "FuelTankStation",
    "HydroDam",
    "LoadGovernorate",
    "OilFacility",
    "OilField",
    "OilPipeline",
    "OilRefinery",
    "OilWell",
    "OreProduct",
    "PowerPlant",
    "ProjectGovernorate",
    "ProjectOrganization",
    "RainfallBasin",
    "RainfallStation",
    "Substation",
    "TransmissionLine",
]

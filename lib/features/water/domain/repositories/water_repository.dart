import 'water_dams_repository.dart';
import 'water_drinking_repository.dart';
import 'water_euphrates_repository.dart';
import 'water_files_repository.dart';
import 'water_lookups_repository.dart';
import 'water_rainfall_repository.dart';

abstract class WaterRepository
    implements
        WaterLookupsRepository,
        WaterFilesRepository,
        WaterDamsRepository,
        WaterRainfallRepository,
        WaterEuphratesRepository,
        WaterDrinkingRepository {}

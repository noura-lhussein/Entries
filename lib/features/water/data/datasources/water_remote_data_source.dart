import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';
import '../../../../core/network/api_constants.dart';
import '../models/water_lookups_model.dart';

part 'water_remote_data_source.g.dart';

@RestApi()
abstract class WaterRemoteDataSource {
  factory WaterRemoteDataSource(Dio dio, {String baseUrl}) = _WaterRemoteDataSource;

  @GET(ApiConstants.waterLookups)
  Future<WaterLookupsModel> getWaterLookups();
}

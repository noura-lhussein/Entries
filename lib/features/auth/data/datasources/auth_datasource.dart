import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';
import '../../../../core/network/api_constants.dart';
import '../models/login_response.dart';

part 'auth_datasource.g.dart';

@RestApi(baseUrl: ApiConstants.apiBaseUrl)
abstract class AuthRemoteDataSource {
  factory AuthRemoteDataSource(Dio dio, {String baseUrl}) = _AuthRemoteDataSource;

  @POST(ApiConstants.login)
  Future<LoginResponse> login(@Body() Map<String, dynamic> body);

  @POST(ApiConstants.refresh)
  Future<LoginResponse> refreshToken(@Body() Map<String, dynamic> body);

  @POST(ApiConstants.logout)
  Future<void> logout();

  @GET(ApiConstants.me)
  Future<UserResponse> getMe();
}

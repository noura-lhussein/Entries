import '../../domain/utils/parse_oil_gas_number.dart';

String fmtDate(DateTime d) => oilGasIsoDate(d);

double? parseNum(String text) => parseOilGasNumber(text);

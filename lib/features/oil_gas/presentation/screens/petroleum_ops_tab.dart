import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/network/user_facing_error.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../data/datasources/oil_gas_remote_data_source.dart';
import '../utils/petroleum_form_utils.dart';
import '../utils/petroleum_master_parser.dart';
import '../widgets/models/petroleum_data.dart';
import '../widgets/oil_fields_table.dart';
import '../widgets/petroleum_dynamic_sections.dart';
import '../widgets/refineries_table.dart';

class PetroleumOpsTab extends StatefulWidget {
  const PetroleumOpsTab({super.key});
  @override
  State<PetroleumOpsTab> createState() => _PetroleumOpsTabState();
}

class _PetroleumOpsTabState extends State<PetroleumOpsTab> {
  DateTime _date = DateTime.now();
  bool _saving = false;
  bool _publish = true;
  bool _masterLoading = true;
  String? _masterError;
  List<OilField> _fields = const [];
  List<String> _refineries = const [];
  List<String> _depots = const [];
  Map<String, String> _powerFacilities = const {};
  final _fuelKey = GlobalKey<FuelStockSectionState>();
  final _exportsKey = GlobalKey<ExportsSectionState>();
  final _lossKey = GlobalKey<ProductionLossSectionState>();
  final _supplyKey = GlobalKey<GasSupplySectionState>();
  final _reqKey = GlobalKey<GasSupplySectionState>();
  Map<String, TextEditingController> _oilC = {};
  Map<String, TextEditingController> _gasC = {};
  Map<String, TextEditingController> _refC = {};

  @override
  void initState() {
    super.initState();
    _loadMaster();
  }

  void _rebuildControllers() {
    _oilC = {for (final f in _fields) f.code: TextEditingController()};
    _gasC = {for (final f in _fields) f.code: TextEditingController()};
    _refC = {
      for (final r in _refineries)
        for (final k in ['benzin', 'diesel', 'fuel', 'lpg'])
          '${r}_$k': TextEditingController(),
    };
  }

  Future<void> _loadMaster() async {
    setState(() {
      _masterLoading = true;
      _masterError = null;
    });
    try {
      final ds = getIt<OilGasRemoteDataSource>();
      final fieldsRaw = await ds.listFields();
      final refsRaw = await ds.listRefineries();
      final facilitiesRaw = await ds.listFacilities();
      final fields =
          fieldsRaw.map(parseField).where((f) => f.code.isNotEmpty).toList();
      final refs =
          refsRaw.map(parseRefinery).where((r) => r.isNotEmpty).toList();

      final power = <String, String>{};
      final depots = <String>[];
      for (final raw in facilitiesRaw) {
        if (raw is! Map) continue;
        final m = Map<String, dynamic>.from(raw);
        final f = parseFacility(m);
        if (f.code.isEmpty) continue;
        if (isPowerFacility(m)) {
          power[f.label] = f.code;
        }
        if (isDepotFacility(m)) {
          depots.add(f.label);
        }
      }
      // If API doesn't classify, keep all facilities as power options.
      if (power.isEmpty) {
        for (final raw in facilitiesRaw) {
          final f = parseFacility(raw);
          if (f.code.isNotEmpty) power[f.label] = f.code;
        }
      }

      if (!mounted) return;
      for (final c in [..._oilC.values, ..._gasC.values, ..._refC.values]) {
        c.dispose();
      }
      setState(() {
        _fields = fields;
        _refineries = refs;
        _powerFacilities = power;
        _depots = depots;
        _rebuildControllers();
        _masterLoading = false;
        if (fields.isEmpty && refs.isEmpty) {
          _masterError = 'لم يُرجع الخادم حقولاً أو مصافٍ. تحقق من بيانات السجل.';
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _masterLoading = false;
        _fields = const [];
        _refineries = const [];
        _powerFacilities = const {};
        _depots = const [];
        _masterError = userFacingErrorMessage(
          e,
          fallback: 'تعذر تحميل بيانات الحقول والمصافي',
        );
      });
    }
  }

  @override
  void dispose() {
    for (final c in [..._oilC.values, ..._gasC.values, ..._refC.values]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    final production = <Map<String, dynamic>>[];
    for (final f in _fields) {
      final oil = parseNum(_oilC[f.code]?.text ?? '');
      final gas = parseNum(_gasC[f.code]?.text ?? '');
      if (oil != null || gas != null) {
        production.add({
          'field_code': f.code,
          'crude_oil_bbl': oil ?? 0,
          'natural_gas_mmscf': gas ?? 0,
        });
      }
    }

    final refineryOutputs = <Map<String, dynamic>>[];
    for (final r in _refineries) {
      final gasoline = parseNum(_refC['${r}_benzin']?.text ?? '');
      final diesel = parseNum(_refC['${r}_diesel']?.text ?? '');
      final fuel = parseNum(_refC['${r}_fuel']?.text ?? '');
      final lpg = parseNum(_refC['${r}_lpg']?.text ?? '');
      if (gasoline != null || diesel != null || fuel != null || lpg != null) {
        refineryOutputs.add({
          'refinery_name': r,
          'gasoline_ton': gasoline ?? 0,
          'diesel_ton': diesel ?? 0,
          'fuel_oil_ton': fuel ?? 0,
          'lpg_ton': lpg ?? 0,
        });
      }
    }

    final inventory = _fuelKey.currentState?.collect() ?? [];
    final exports = _exportsKey.currentState?.collect() ?? [];
    final losses = _lossKey.currentState?.collect() ?? [];
    final supply = _supplyKey.currentState?.collect() ?? [];
    final requirement = _reqKey.currentState?.collect() ?? [];

    if (production.isEmpty &&
        refineryOutputs.isEmpty &&
        inventory.isEmpty &&
        exports.isEmpty &&
        losses.isEmpty &&
        supply.isEmpty &&
        requirement.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('لا توجد بيانات للحفظ',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
        backgroundColor: AppColors.red2,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
      ));
      return;
    }

    setState(() => _saving = true);
    try {
      final payload = <String, dynamic>{
        'production_date': fmtDate(_date),
        'publish': _publish,
        if (production.isNotEmpty) 'production': production,
        if (refineryOutputs.isNotEmpty) 'refinery_outputs': refineryOutputs,
        if (inventory.isNotEmpty) 'inventory': inventory,
        if (exports.isNotEmpty) 'exports': exports,
        if (losses.isNotEmpty) 'losses': losses,
        if (supply.isNotEmpty) 'power_gas_supply': supply,
        if (requirement.isNotEmpty) 'power_gas_requirement': requirement,
      };
      await getIt<OilGasRemoteDataSource>().upsertDailyOperations(payload);
      if (_publish) {
        await getIt<OilGasRemoteDataSource>().publishDay(fmtDate(_date));
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(
            _publish
                ? 'تم حفظ ونشر البيانات التشغيلية بنجاح'
                : 'تم حفظ البيانات التشغيلية كمسودة',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
        backgroundColor: AppColors.forest1,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
      ));
      for (final c in [..._oilC.values, ..._gasC.values, ..._refC.values]) {
        c.clear();
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(
            userFacingErrorMessage(e, fallback: 'فشل حفظ البيانات التشغيلية'),
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp)),
        backgroundColor: AppColors.red2,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8.r)),
      ));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.all(14.r),
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        GradientHeaderCard(
            title: 'إدخال البيانات التشغيلية',
            subtitle: 'البيانات الفعلية اليومية للحقول والمصافي',
            icon: Icons.analytics_outlined),
        SizedBox(height: 12.h),
        if (_masterLoading) const LinearProgressIndicator(minHeight: 2),
        if (_masterError != null) ...[
          Material(
            color: AppColors.red2.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(10.r),
            child: Padding(
              padding: EdgeInsets.all(12.r),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: AppColors.red2, size: 20.r),
                  SizedBox(width: 8.w),
                  Expanded(
                    child: Text(
                      _masterError!,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 12.sp,
                        color: AppColors.red2,
                      ),
                    ),
                  ),
                  TextButton(onPressed: _loadMaster, child: const Text('إعادة')),
                ],
              ),
            ),
          ),
          SizedBox(height: 12.h),
        ],
        FormCard(
            child: DatePickerField(
                label: 'تاريخ الإنتاج',
                initialDate: _date,
                onDateChanged: (d) => setState(() => _date = d))),
        SizedBox(height: 12.h),
        if (_fields.isNotEmpty)
          OilFieldsTable(oilCtrls: _oilC, gasCtrls: _gasC, fields: _fields),
        if (_fields.isNotEmpty) SizedBox(height: 12.h),
        if (_refineries.isNotEmpty)
          RefineriesTable(controllers: _refC, refineries: _refineries),
        if (_refineries.isNotEmpty) SizedBox(height: 12.h),
        FuelStockSection(key: _fuelKey, depots: _depots),
        SizedBox(height: 12.h),
        ExportsSection(key: _exportsKey),
        SizedBox(height: 12.h),
        if (_fields.isNotEmpty)
          ProductionLossSection(key: _lossKey, fields: _fields),
        if (_fields.isNotEmpty) SizedBox(height: 12.h),
        GasSupplySection(
            key: _supplyKey,
            title: 'إمداد الغاز للكهرباء',
            hint: 'أضف صفاً لكل منشأة',
            valueLabel: 'المورد',
            valueUnit: 'MMscf',
            facilities: _powerFacilities),
        SizedBox(height: 12.h),
        GasSupplySection(
            key: _reqKey,
            title: 'متطلبات غاز الكهرباء',
            hint: 'أضف صفاً لكل منشأة',
            valueLabel: 'المطلوب',
            valueUnit: 'MMscf',
            isRequirement: true,
            facilities: _powerFacilities),
        SizedBox(height: 12.h),
        FormCard(
            child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
              InkWell(
                onTap: () => setState(() => _publish = !_publish),
                borderRadius: BorderRadius.circular(6.r),
                child: Row(children: [
                  Checkbox(
                      value: _publish,
                      activeColor: AppColors.forest1,
                      onChanged: (v) => setState(() => _publish = v ?? true),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(4.r))),
                  Expanded(
                      child: Text('نشر التقرير وتحديث لوحة الوزير بعد الحفظ',
                          style: TextStyle(
                              fontFamily: 'Cairo',
                              fontSize: 12.sp,
                              color: AppColors.textPrimary))),
                ]),
              ),
              SizedBox(height: 12.h),
              SaveButton(
                  isLoading: _saving,
                  label: 'حفظ التقرير اليومي',
                  onPressed: _save),
            ])),
        SizedBox(height: 16.h),
      ]),
    );
  }
}

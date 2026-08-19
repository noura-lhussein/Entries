import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../electricity/data/datasources/electricity_remote_data_source.dart';
import '../../../oil_gas/data/datasources/oil_gas_remote_data_source.dart';
import '../../../geology/data/datasources/geology_remote_data_source.dart';
import '../../../water/data/datasources/water_admin_remote_data_source.dart';
import '../widgets/admin_target_coverage_panel.dart';

/// Generic admin registry CRUD — matches moe-portal admin-resource screens.
class AdminResourceScreen extends StatefulWidget {
  final UserDepartment sector;
  const AdminResourceScreen({super.key, required this.sector});

  @override
  State<AdminResourceScreen> createState() => _AdminResourceScreenState();
}

class _AdminResourceScreenState extends State<AdminResourceScreen> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _resources = [];
  String? _selectedSlug;
  Map<String, dynamic>? _listPayload;
  final _searchCtrl = TextEditingController();
  int _page = 1;
  int _coverageRefresh = 0;

  bool get _isOperationalTargets =>
      _selectedSlug == 'operational-targets';

  @override
  void initState() {
    super.initState();
    _loadRegistry();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<Map<String, dynamic>> _registry() async {
    switch (widget.sector) {
      case UserDepartment.water:
        return getIt<WaterAdminRemoteDataSource>().getAdminRegistry();
      case UserDepartment.petroleum:
        return getIt<OilGasRemoteDataSource>().getAdminRegistry();
      case UserDepartment.electricity:
        return getIt<ElectricityRemoteDataSource>().getAdminRegistry();
      case UserDepartment.mineral:
        return getIt<GeologyRemoteDataSource>().getAdminRegistry();
      case UserDepartment.admin:
        return getIt<WaterAdminRemoteDataSource>().getAdminRegistry();
    }
  }

  Future<Map<String, dynamic>> _list(String slug) async {
    switch (widget.sector) {
      case UserDepartment.water:
        return getIt<WaterAdminRemoteDataSource>().listAdminResource(
          slug,
          page: _page,
          search: _searchCtrl.text.trim(),
        );
      case UserDepartment.petroleum:
        return getIt<OilGasRemoteDataSource>().listAdminResource(
          slug,
          page: _page,
          search: _searchCtrl.text.trim(),
        );
      case UserDepartment.electricity:
        return getIt<ElectricityRemoteDataSource>().listAdminResource(
          slug,
          page: _page,
          search: _searchCtrl.text.trim(),
        );
      case UserDepartment.mineral:
        return getIt<GeologyRemoteDataSource>().listAdminResource(
          slug,
          page: _page,
          search: _searchCtrl.text.trim(),
        );
      case UserDepartment.admin:
        return getIt<WaterAdminRemoteDataSource>().listAdminResource(
          slug,
          page: _page,
          search: _searchCtrl.text.trim(),
        );
    }
  }

  Future<void> _delete(String slug, String pk) async {
    switch (widget.sector) {
      case UserDepartment.water:
        await getIt<WaterAdminRemoteDataSource>().deleteAdminResource(slug, pk);
        break;
      case UserDepartment.petroleum:
        await getIt<OilGasRemoteDataSource>().deleteAdminResource(slug, pk);
        break;
      case UserDepartment.electricity:
        await getIt<ElectricityRemoteDataSource>().deleteAdminResource(slug, pk);
        break;
      case UserDepartment.mineral:
        await getIt<GeologyRemoteDataSource>().deleteAdminResource(slug, pk);
        break;
      case UserDepartment.admin:
        await getIt<WaterAdminRemoteDataSource>().deleteAdminResource(slug, pk);
        break;
    }
  }

  Future<void> _create(String slug, Map<String, dynamic> body) async {
    switch (widget.sector) {
      case UserDepartment.water:
        await getIt<WaterAdminRemoteDataSource>().createAdminResource(slug, body);
        break;
      case UserDepartment.petroleum:
        await getIt<OilGasRemoteDataSource>().createAdminResource(slug, body);
        break;
      case UserDepartment.electricity:
        await getIt<ElectricityRemoteDataSource>().createAdminResource(slug, body);
        break;
      case UserDepartment.mineral:
        await getIt<GeologyRemoteDataSource>().createAdminResource(slug, body);
        break;
      case UserDepartment.admin:
        await getIt<WaterAdminRemoteDataSource>().createAdminResource(slug, body);
        break;
    }
  }

  Future<void> _update(String slug, String pk, Map<String, dynamic> body) async {
    switch (widget.sector) {
      case UserDepartment.water:
        await getIt<WaterAdminRemoteDataSource>()
            .updateAdminResource(slug, pk, body);
        break;
      case UserDepartment.petroleum:
        await getIt<OilGasRemoteDataSource>()
            .updateAdminResource(slug, pk, body);
        break;
      case UserDepartment.electricity:
        await getIt<ElectricityRemoteDataSource>()
            .updateAdminResource(slug, pk, body);
        break;
      case UserDepartment.mineral:
        await getIt<GeologyRemoteDataSource>()
            .updateAdminResource(slug, pk, body);
        break;
      case UserDepartment.admin:
        await getIt<WaterAdminRemoteDataSource>()
            .updateAdminResource(slug, pk, body);
        break;
    }
  }

  Future<void> _openEditor({
    Map<String, dynamic>? existing,
    Map<String, dynamic>? prefill,
  }) async {
    final slug = _selectedSlug;
    if (slug == null) return;

    final seed = existing ?? prefill;
    final nameCtrl = TextEditingController(
      text: seed?['name_ar']?.toString() ??
          seed?['label_ar']?.toString() ??
          seed?['name']?.toString() ??
          '',
    );
    final codeCtrl = TextEditingController(
      text: seed?['code']?.toString() ??
          seed?['scope_code']?.toString() ??
          seed?['slug']?.toString() ??
          '',
    );
    final notesCtrl = TextEditingController(
      text: seed?['notes']?.toString() ??
          seed?['description_ar']?.toString() ??
          '',
    );
    final valueCtrl = TextEditingController(
      text: seed?['target_value']?.toString() ?? '',
    );
    final isEdit = existing != null;
    final pk = existing?['id']?.toString() ??
        existing?['pk']?.toString() ??
        existing?['code']?.toString() ??
        '';

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(isEdit ? 'تعديل' : 'إضافة',
            style: const TextStyle(fontFamily: 'Cairo')),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(
                  labelText: 'الاسم / التسمية (عربي)',
                  border: OutlineInputBorder(),
                ),
              ),
              SizedBox(height: 10.h),
              TextField(
                controller: codeCtrl,
                decoration: const InputDecoration(
                  labelText: 'الرمز / نطاق الهدف',
                  border: OutlineInputBorder(),
                ),
              ),
              if (_isOperationalTargets) ...[
                SizedBox(height: 10.h),
                TextField(
                  controller: valueCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'قيمة الهدف',
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
              SizedBox(height: 10.h),
              TextField(
                controller: notesCtrl,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'ملاحظات',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('إلغاء')),
          TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: Text(isEdit ? 'حفظ' : 'إضافة')),
        ],
      ),
    );

    final body = <String, dynamic>{
      ...?prefill,
      if (nameCtrl.text.trim().isNotEmpty) ...{
        'name_ar': nameCtrl.text.trim(),
        'label_ar': nameCtrl.text.trim(),
      },
      if (codeCtrl.text.trim().isNotEmpty) ...{
        'code': codeCtrl.text.trim(),
        if (prefill != null || _isOperationalTargets)
          'scope_code': codeCtrl.text.trim(),
      },
      if (valueCtrl.text.trim().isNotEmpty)
        'target_value': num.tryParse(valueCtrl.text.trim()) ??
            valueCtrl.text.trim(),
      if (notesCtrl.text.trim().isNotEmpty) 'notes': notesCtrl.text.trim(),
    };
    nameCtrl.dispose();
    codeCtrl.dispose();
    notesCtrl.dispose();
    valueCtrl.dispose();

    if (saved != true || body.isEmpty) return;
    try {
      if (isEdit && pk.isNotEmpty) {
        await _update(slug, pk, body);
      } else if (_isOperationalTargets &&
          widget.sector == UserDepartment.petroleum &&
          !isEdit) {
        await getIt<OilGasRemoteDataSource>().createTarget(body);
      } else {
        await _create(slug, body);
      }
      await _loadList();
      if (mounted) setState(() => _coverageRefresh++);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('تعذر الحفظ')),
      );
    }
  }

  Future<void> _loadRegistry() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final reg = await _registry();
      final groups = reg['groups'] as List? ??
          reg['resources'] as List? ??
          reg['items'] as List? ??
          const [];
      final flat = <Map<String, dynamic>>[];
      for (final g in groups) {
        if (g is Map && g['resources'] is List) {
          for (final r in (g['resources'] as List).whereType<Map>()) {
            flat.add(Map<String, dynamic>.from(r));
          }
        } else if (g is Map) {
          flat.add(Map<String, dynamic>.from(g));
        }
      }
      if (!mounted) return;
      setState(() {
        _resources = flat;
        _selectedSlug ??= flat.isEmpty
            ? null
            : (flat.first['slug']?.toString() ?? flat.first['id']?.toString());
        _loading = false;
      });
      if (_selectedSlug != null) await _loadList();
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'تعذر تحميل سجل الموارد';
      });
    }
  }

  Future<void> _loadList() async {
    final slug = _selectedSlug;
    if (slug == null) return;
    setState(() => _loading = true);
    try {
      final list = await _list(slug);
      if (!mounted) return;
      setState(() {
        _listPayload = list;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = 'تعذر تحميل القائمة';
      });
    }
  }

  String _label(Map m) =>
      m['label_ar']?.toString() ??
      m['name_ar']?.toString() ??
      m['label']?.toString() ??
      m['slug']?.toString() ??
      '';

  @override
  Widget build(BuildContext context) {
    final results = (_listPayload?['results'] as List?) ??
        (_listPayload?['items'] as List?) ??
        const [];

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: Colors.transparent,
        floatingActionButton: _selectedSlug == null
            ? null
            : FloatingActionButton.extended(
                onPressed: () => _openEditor(),
                backgroundColor: AppColors.forest1,
                icon: const Icon(Icons.add),
                label: const Text('إضافة', style: TextStyle(fontFamily: 'Cairo')),
              ),
        body: Column(
        children: [
          Container(
            color: Colors.white,
            padding: EdgeInsets.all(10.r),
            child: Column(
              children: [
                DropdownButtonFormField<String>(
                  initialValue: _selectedSlug,
                  isExpanded: true,
                  decoration: InputDecoration(
                    labelText: 'المورد',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.r),
                    ),
                  ),
                  items: _resources.map((r) {
                    final slug =
                        r['slug']?.toString() ?? r['id']?.toString() ?? '';
                    return DropdownMenuItem(
                      value: slug,
                      child: Text(_label(r)),
                    );
                  }).toList(),
                  onChanged: (v) {
                    setState(() {
                      _selectedSlug = v;
                      _page = 1;
                    });
                    _loadList();
                  },
                ),
                SizedBox(height: 8.h),
                TextField(
                  controller: _searchCtrl,
                  decoration: InputDecoration(
                    hintText: 'بحث…',
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.search),
                      onPressed: () {
                        _page = 1;
                        _loadList();
                      },
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8.r),
                    ),
                  ),
                  onSubmitted: (_) {
                    _page = 1;
                    _loadList();
                  },
                ),
              ],
            ),
          ),
          if (_isOperationalTargets)
            AdminTargetCoveragePanel(
              sector: widget.sector,
              refreshToken: _coverageRefresh,
              onAddMissing: (prefill) => _openEditor(prefill: prefill),
            ),
          if (_loading) const LinearProgressIndicator(minHeight: 2),
          if (_error != null)
            Padding(
              padding: EdgeInsets.all(8.r),
              child: Text(_error!,
                  style: TextStyle(color: AppColors.red2, fontFamily: 'Cairo')),
            ),
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.all(12.r),
              itemCount: results.length,
              itemBuilder: (context, i) {
                final raw = results[i];
                if (raw is! Map) return const SizedBox.shrink();
                final m = Map<String, dynamic>.from(raw);
                final pk = m['id']?.toString() ??
                    m['pk']?.toString() ??
                    m['code']?.toString() ??
                    '';
                final title = m['name_ar']?.toString() ??
                    m['name']?.toString() ??
                    m['title_ar']?.toString() ??
                    m['label']?.toString() ??
                    pk;
                return Card(
                  child: ListTile(
                    onTap: () => _openEditor(existing: m),
                    title: Text(title,
                        style: TextStyle(
                            fontFamily: 'Cairo',
                            fontWeight: FontWeight.w700,
                            fontSize: 13.sp)),
                    subtitle: Text(
                      m.entries
                          .take(4)
                          .map((e) => '${e.key}: ${e.value}')
                          .join(' · '),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp),
                    ),
                    trailing: IconButton(
                      icon: Icon(Icons.delete_outline, color: AppColors.red2),
                      onPressed: _selectedSlug == null || pk.isEmpty
                          ? null
                          : () async {
                              final ok = await showDialog<bool>(
                                context: context,
                                builder: (ctx) => AlertDialog(
                                  title: const Text('حذف'),
                                  content: Text('حذف «$title»؟'),
                                  actions: [
                                    TextButton(
                                        onPressed: () =>
                                            Navigator.pop(ctx, false),
                                        child: const Text('إلغاء')),
                                    TextButton(
                                        onPressed: () =>
                                            Navigator.pop(ctx, true),
                                        child: const Text('حذف')),
                                  ],
                                ),
                              );
                              if (ok != true) return;
                              try {
                                await _delete(_selectedSlug!, pk);
                                await _loadList();
                              } catch (_) {}
                            },
                    ),
                  ),
                );
              },
            ),
          ),
          if ((_listPayload?['count'] as int? ?? 0) >
              ((_listPayload?['page_size'] as int?) ?? 20) * _page)
            TextButton(
              onPressed: () {
                _page++;
                _loadList();
              },
              child: const Text('المزيد'),
            ),
        ],
      ),
      ),
    );
  }
}

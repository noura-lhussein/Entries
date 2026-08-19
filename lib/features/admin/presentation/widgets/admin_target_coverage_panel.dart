import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../electricity/data/datasources/electricity_remote_data_source.dart';
import '../../../oil_gas/data/datasources/oil_gas_remote_data_source.dart';

class AdminTargetCoveragePanel extends StatefulWidget {
  final UserDepartment sector;
  final void Function(Map<String, dynamic> prefill)? onAddMissing;
  final int refreshToken;

  const AdminTargetCoveragePanel({
    super.key,
    required this.sector,
    this.onAddMissing,
    this.refreshToken = 0,
  });

  @override
  State<AdminTargetCoveragePanel> createState() =>
      _AdminTargetCoveragePanelState();
}

class _AdminTargetCoveragePanelState extends State<AdminTargetCoveragePanel> {
  bool _loading = true;
  bool _error = false;
  bool _expanded = true;
  DateTime _date = DateTime.now();
  Map<String, dynamic>? _coverage;

  String _fmtDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant AdminTargetCoveragePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.refreshToken != widget.refreshToken ||
        oldWidget.sector != widget.sector) {
      _load();
    }
  }

  Future<void> _load() async {
    if (widget.sector != UserDepartment.petroleum &&
        widget.sector != UserDepartment.electricity) {
      setState(() {
        _coverage = null;
        _loading = false;
        _error = false;
      });
      return;
    }
    setState(() {
      _loading = true;
      _error = false;
    });
    try {
      final date = _fmtDate(_date);
      final Map<String, dynamic> json;
      if (widget.sector == UserDepartment.petroleum) {
        json = await getIt<OilGasRemoteDataSource>()
            .getTargetCoverage(date: date);
      } else {
        json = await getIt<ElectricityRemoteDataSource>()
            .getTargetCoverage(date: date);
      }
      if (!mounted) return;
      setState(() {
        _coverage = json;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = true;
        _coverage = null;
      });
    }
  }

  Future<void> _pickDate() async {
    final d = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2015),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (d == null) return;
    setState(() => _date = d);
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    if (widget.sector != UserDepartment.petroleum &&
        widget.sector != UserDepartment.electricity) {
      return const SizedBox.shrink();
    }

    final summary = (_coverage?['summary'] as Map?)?.cast<String, dynamic>();
    final groups = _coverage?['groups'] as List? ?? const [];
    final pct = summary?['coverage_pct'];
    final configured = summary?['configured'];
    final required = summary?['required'];
    final missing = summary?['missing'];
    final complete = summary?['complete'] == true;

    return Container(
      margin: EdgeInsets.fromLTRB(10.w, 8.h, 10.w, 0),
      padding: EdgeInsets.all(12.r),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10.r),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'تغطية الأهداف التشغيلية',
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontWeight: FontWeight.w800,
                        fontSize: 13.sp,
                      ),
                    ),
                    Text(
                      'تحقق من اكتمال الأهداف قبل نشر التقرير',
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 10.sp,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              TextButton(
                onPressed: _pickDate,
                child: Text(
                  _fmtDate(_date),
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 11.sp,
                    fontWeight: FontWeight.w700,
                    color: AppColors.forest1,
                  ),
                ),
              ),
              IconButton(
                tooltip: _expanded ? 'طي' : 'توسيع',
                onPressed: () => setState(() => _expanded = !_expanded),
                icon: Icon(
                  _expanded ? Icons.expand_less : Icons.expand_more,
                ),
              ),
            ],
          ),
          if (_loading) const LinearProgressIndicator(minHeight: 2),
          if (_error)
            Padding(
              padding: EdgeInsets.only(top: 6.h),
              child: Text(
                'تعذر تحميل تغطية الأهداف',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 11.sp,
                  color: AppColors.errorRed,
                ),
              ),
            ),
          if (!_loading && !_error && summary != null) ...[
            SizedBox(height: 8.h),
            Row(
              children: [
                Text(
                  '${pct ?? '—'}%',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 22.sp,
                    fontWeight: FontWeight.w900,
                    color: complete
                        ? AppColors.successGreen
                        : AppColors.goldDeep,
                  ),
                ),
                SizedBox(width: 10.w),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'مُعرَّف: $configured / $required',
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      Text(
                        complete
                            ? 'مكتمل'
                            : '${missing ?? 0} هدف ناقص',
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 10.sp,
                          color: complete
                              ? AppColors.successGreen
                              : AppColors.errorRed,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            SizedBox(height: 6.h),
            ClipRRect(
              borderRadius: BorderRadius.circular(4.r),
              child: LinearProgressIndicator(
                value: ((pct is num ? pct.toDouble() : 0) / 100).clamp(0, 1),
                minHeight: 6.h,
                backgroundColor: AppColors.border,
                color: complete ? AppColors.successGreen : AppColors.goldDeep,
              ),
            ),
          ],
          if (_expanded && !_loading && !_error)
            for (final raw in groups.whereType<Map>()) ...[
              SizedBox(height: 10.h),
              _GroupBlock(
                group: Map<String, dynamic>.from(raw),
                onAddMissing: widget.onAddMissing,
              ),
            ],
        ],
      ),
    );
  }
}

class _GroupBlock extends StatelessWidget {
  final Map<String, dynamic> group;
  final void Function(Map<String, dynamic> prefill)? onAddMissing;

  const _GroupBlock({required this.group, this.onAddMissing});

  @override
  Widget build(BuildContext context) {
    final items = group['items'] as List? ?? const [];
    final label = group['label_ar']?.toString() ??
        group['label_en']?.toString() ??
        '';
    final desc = group['description_ar']?.toString() ?? '';
    final configured = group['configured'];
    final required = group['required'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontWeight: FontWeight.w800,
                      fontSize: 12.sp,
                    ),
                  ),
                  if (desc.isNotEmpty)
                    Text(
                      desc,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 10.sp,
                        color: AppColors.textSecondary,
                      ),
                    ),
                ],
              ),
            ),
            Text(
              '$configured/$required',
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.sp,
                fontWeight: FontWeight.w700,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
        SizedBox(height: 6.h),
        for (final raw in items.whereType<Map>())
          _ItemRow(
            item: Map<String, dynamic>.from(raw),
            onAddMissing: onAddMissing,
          ),
      ],
    );
  }
}

class _ItemRow extends StatelessWidget {
  final Map<String, dynamic> item;
  final void Function(Map<String, dynamic> prefill)? onAddMissing;

  const _ItemRow({required this.item, this.onAddMissing});

  @override
  Widget build(BuildContext context) {
    final missing = item['status']?.toString() == 'missing';
    final metric = item['label_ar']?.toString() ??
        item['label_en']?.toString() ??
        item['metric_key']?.toString() ??
        '';
    final scope = item['scope_type']?.toString() == 'national'
        ? ''
        : (item['scope_label_ar']?.toString() ??
            item['scope_code']?.toString() ??
            '');
    final period = item['period_hint']?.toString() == 'monthly'
        ? 'شهري'
        : 'يومي';
    final value = item['target_value'];
    final unit = item['unit']?.toString() ?? '';

    return Container(
      margin: EdgeInsets.only(bottom: 6.h),
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 8.h),
      decoration: BoxDecoration(
        color: missing
            ? AppColors.errorRed.withValues(alpha: 0.06)
            : AppColors.goldWash,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: Row(
        children: [
          Container(
            width: 8.r,
            height: 8.r,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: missing ? AppColors.errorRed : AppColors.successGreen,
            ),
          ),
          SizedBox(width: 8.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  scope.isEmpty ? metric : '$scope · $metric',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 11.5.sp,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  missing
                      ? period
                      : '$period · ${value ?? '—'} $unit',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 10.sp,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          if (missing && onAddMissing != null)
            TextButton(
              onPressed: () => onAddMissing!({
                'metric_key': item['metric_key'],
                'scope_type': item['scope_type'],
                'scope_code': item['scope_code'],
                'period_type': item['period_hint'],
                'period_start': item['period_start'],
                'unit': item['unit'],
                'label_en': item['label_en'],
                'label_ar': item['label_ar'],
              }),
              child: Text(
                'إضافة',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 11.sp,
                  fontWeight: FontWeight.w800,
                  color: AppColors.forest1,
                ),
              ),
            )
          else if (!missing)
            Text(
              'مُعرَّف',
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 10.sp,
                color: AppColors.successGreen,
                fontWeight: FontWeight.w700,
              ),
            ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../data/models/builder_models.dart';
import '../bloc/data_entry_bloc.dart';
import '../bloc/data_entry_event.dart';
import '../bloc/data_entry_state.dart';
import 'dynamic_schema_field.dart';

class DataEntryWorkspace extends StatelessWidget {
  const DataEntryWorkspace({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<DataEntryBloc, DataEntryState>(
      builder: (context, state) {
        if (state.titles.isEmpty) {
          return _EmptyHint(
            icon: Icons.inbox_outlined,
            text: 'لا توجد نماذج متاحة لهذا القسم.',
          );
        }
        return Column(
          children: [
            _TitlePicker(state: state),
            Expanded(
              child: state.loadingSchema
                  ? const _SchemaLoading()
                  : state.schema == null
                      ? _EmptyHint(
                          icon: Icons.edit_note_outlined,
                          text: 'اختر نموذجاً للبدء بالإدخال.',
                        )
                      : _SchemaForm(state: state),
            ),
            _Footer(state: state),
          ],
        );
      },
    );
  }
}

class _TitlePicker extends StatelessWidget {
  final DataEntryState state;
  const _TitlePicker({required this.state});

  @override
  Widget build(BuildContext context) {
    final total = state.titles.length;
    final done = state.progressDone;
    return Container(
      margin: EdgeInsets.only(bottom: 10.h),
      padding: EdgeInsets.all(12.r),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12.r),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  'النماذج',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 13.sp,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textPrimary,
                  ),
                ),
              ),
              Text(
                '$done / $total',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 11.sp,
                  fontWeight: FontWeight.w700,
                  color: AppColors.inkSoft,
                ),
              ),
            ],
          ),
          SizedBox(height: 8.h),
          ClipRRect(
            borderRadius: BorderRadius.circular(99),
            child: LinearProgressIndicator(
              value: total == 0 ? 0 : done / total,
              minHeight: 6.h,
              backgroundColor: AppColors.goldWash,
              color: AppColors.successGreen,
            ),
          ),
          SizedBox(height: 10.h),
          SizedBox(
            height: 40.h,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: state.titles.length,
              separatorBuilder: (_, __) => SizedBox(width: 8.w),
              itemBuilder: (context, i) {
                final t = state.titles[i];
                final current = t.id == state.selectedTitleId;
                final status =
                    state.sectionStatus[t.id] ?? SectionEntryStatus.empty;
                return ChoiceChip(
                  showCheckmark: false,
                  selected: current,
                  label: Text(
                    '${i + 1} — ${t.name}',
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 11.sp,
                      fontWeight: FontWeight.w700,
                      color: current ? Colors.white : AppColors.textPrimary,
                    ),
                  ),
                  avatar: Icon(
                    _statusIcon(status),
                    size: 14.r,
                    color: current ? Colors.white : _statusColor(status),
                  ),
                  selectedColor: AppColors.inkDeep,
                  backgroundColor: AppColors.goldWash,
                  side: BorderSide(
                    color: current ? AppColors.inkDeep : AppColors.border,
                  ),
                  onSelected: (_) =>
                      context.read<DataEntryBloc>().add(TitleSelected(t.id)),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _SchemaForm extends StatelessWidget {
  final DataEntryState state;
  const _SchemaForm({required this.state});

  @override
  Widget build(BuildContext context) {
    final s = state.schema!;
    final groups = state.groupedFields;
    return ListView(
      padding: EdgeInsets.only(bottom: 12.h),
      children: [
        FormCard(
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      s.section.titleAr,
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 16.sp,
                        fontWeight: FontWeight.w800,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    if (s.section.subtitleAr != null &&
                        s.section.subtitleAr!.trim().isNotEmpty) ...[
                      SizedBox(height: 4.h),
                      Text(
                        s.section.subtitleAr!,
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 11.sp,
                          color: AppColors.textHint,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (state.selectedTitleId != null)
                _StatusBadge(
                  status: state.sectionStatus[state.selectedTitleId] ??
                      SectionEntryStatus.empty,
                ),
            ],
          ),
        ),
        SizedBox(height: 12.h),
        for (final g in groups) ...[
          _GroupCard(group: g, collapsed: state.collapsedGroups[g.group.id] ?? false),
          SizedBox(height: 12.h),
        ],
        _HistoryCard(state: state),
      ],
    );
  }
}

class _GroupCard extends StatelessWidget {
  final GroupedSchemaFields group;
  final bool collapsed;
  const _GroupCard({required this.group, required this.collapsed});

  @override
  Widget build(BuildContext context) {
    return FormCard(
      child: Column(
        children: [
          InkWell(
            onTap: () => context
                .read<DataEntryBloc>()
                .add(GroupToggled(group.group.id)),
            child: Row(
              children: [
                Icon(
                  collapsed
                      ? Icons.chevron_left_rounded
                      : Icons.expand_more_rounded,
                  color: AppColors.inkSoft,
                ),
                SizedBox(width: 6.w),
                Expanded(
                  child: Text(
                    group.group.titleAr,
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                Text(
                  '${group.fields.length} حقول',
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 11.sp,
                    color: AppColors.textHint,
                  ),
                ),
              ],
            ),
          ),
          if (!collapsed) ...[
            SizedBox(height: 12.h),
            for (var i = 0; i < group.fields.length; i++) ...[
              DynamicSchemaField(field: group.fields[i]),
              if (i != group.fields.length - 1) SizedBox(height: 10.h),
            ],
          ],
        ],
      ),
    );
  }
}

class _HistoryCard extends StatelessWidget {
  final DataEntryState state;
  const _HistoryCard({required this.state});

  @override
  Widget build(BuildContext context) {
    final preview = state.schema?.section.previewFieldKeys ?? const <String>[];
    return FormCard(
      child: Column(
        children: [
          InkWell(
            onTap: () =>
                context.read<DataEntryBloc>().add(const HistoryToggled()),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    'آخر ${state.historyRows.isEmpty ? 5 : state.historyRows.length} سجلات لهذا القسم',
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                Icon(
                  state.historyOpen
                      ? Icons.expand_more_rounded
                      : Icons.chevron_left_rounded,
                  color: AppColors.inkSoft,
                ),
              ],
            ),
          ),
          if (state.historyOpen) ...[
            SizedBox(height: 10.h),
            if (state.historyRows.isEmpty)
              Text(
                'لا سجلات سابقة',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 12.sp,
                  color: AppColors.textHint,
                ),
              )
            else
              for (final row in state.historyRows) ...[
                _HistoryRowTile(
                  row: row,
                  previewKeys: preview,
                  expanded: state.expandedHistoryIds.contains(row.rowId),
                  schema: state.schema,
                ),
                SizedBox(height: 8.h),
              ],
          ],
        ],
      ),
    );
  }
}

class _HistoryRowTile extends StatelessWidget {
  final InfoHistoryRow row;
  final List<String> previewKeys;
  final bool expanded;
  final FormSchemaPayload? schema;
  const _HistoryRowTile({
    required this.row,
    required this.previewKeys,
    required this.expanded,
    required this.schema,
  });

  String _preview(String key) {
    final fields = row.fields;
    if (fields[key] != null && fields[key]!.isNotEmpty) return fields[key]!;
    final f = schema?.fields.where((x) => x.key == key);
    if (f != null && f.isNotEmpty) {
      final label = f.first.labelAr;
      if (fields[label] != null && fields[label]!.isNotEmpty) return fields[label]!;
    }
    return '—';
  }

  String _header(String key) {
    final f = schema?.fields.where((x) => x.key == key);
    if (f != null && f.isNotEmpty) return f.first.labelAr;
    return key;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(10.r),
      decoration: BoxDecoration(
        color: AppColors.goldWash,
        borderRadius: BorderRadius.circular(8.r),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Wrap(
            spacing: 10.w,
            runSpacing: 6.h,
            children: [
              for (final key in previewKeys)
                SizedBox(
                  width: 140.w,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _header(key),
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 10.sp,
                          color: AppColors.textHint,
                        ),
                      ),
                      Text(
                        _preview(key),
                        textDirection: TextDirection.ltr,
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                ),
              TextButton(
                onPressed: () => context
                    .read<DataEntryBloc>()
                    .add(HistoryRowToggled(row.rowId)),
                child: Text(
                  expanded ? 'طي' : 'توسيع',
                  style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
                ),
              ),
            ],
          ),
          if (expanded) ...[
            SizedBox(height: 8.h),
            Wrap(
              spacing: 10.w,
              runSpacing: 8.h,
              children: [
                for (final e in row.fields.entries)
                  if (!previewKeys.contains(e.key))
                    SizedBox(
                      width: 140.w,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            e.key,
                            style: TextStyle(
                              fontFamily: 'Cairo',
                              fontSize: 10.sp,
                              color: AppColors.textHint,
                            ),
                          ),
                          Text(
                            e.value,
                            textDirection: TextDirection.ltr,
                            style: TextStyle(
                              fontFamily: 'Cairo',
                              fontSize: 12.sp,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class _Footer extends StatelessWidget {
  final DataEntryState state;
  const _Footer({required this.state});

  @override
  Widget build(BuildContext context) {
    final saving = state.savePhase == DataEntrySavePhase.saving;
    final canSave = state.selectedSubId != null && state.schema != null;
    return Container(
      padding: EdgeInsets.fromLTRB(0, 8.h, 0, 4.h),
      decoration: BoxDecoration(
        color: AppColors.background,
        border: Border(top: BorderSide(color: AppColors.divider)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SaveButton(
            isLoading: saving,
            label: 'اعتماد والانتقال للتالي',
            onPressed: canSave && !saving
                ? () => context
                    .read<DataEntryBloc>()
                    .add(const CommitAndNextRequested())
                : null,
          ),
          SizedBox(height: 8.h),
          SizedBox(
            height: 44.h,
            child: OutlinedButton(
              onPressed: canSave && !saving
                  ? () => context
                      .read<DataEntryBloc>()
                      .add(const SaveDraftRequested())
                  : null,
              style: OutlinedButton.styleFrom(
                side: const BorderSide(color: AppColors.borderMid),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10.r),
                ),
              ),
              child: Text(
                'حفظ مسودة',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w700,
                  color: AppColors.inkMid,
                ),
              ),
            ),
          ),
          SizedBox(height: 6.h),
          Text(
            _statusText(state),
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 11.sp,
              color: state.savePhase == DataEntrySavePhase.failed
                  ? AppColors.errorRed
                  : AppColors.textHint,
            ),
          ),
        ],
      ),
    );
  }

  String _statusText(DataEntryState state) {
    switch (state.savePhase) {
      case DataEntrySavePhase.saving:
        return 'جارٍ الحفظ…';
      case DataEntrySavePhase.saved:
        return state.lastSavedAt == null
            ? (state.saveMessage ?? 'تم الحفظ')
            : '${state.saveMessage ?? 'حُفظت المسودة'}  ${state.lastSavedAt}';
      case DataEntrySavePhase.failed:
        return state.saveMessage ?? 'فشل الحفظ';
      case DataEntrySavePhase.idle:
        return state.saveMessage ?? ' ';
    }
  }
}

class _StatusBadge extends StatelessWidget {
  final SectionEntryStatus status;
  const _StatusBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 4.h),
      decoration: BoxDecoration(
        color: _statusColor(status).withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20.r),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(_statusIcon(status), size: 14.r, color: _statusColor(status)),
          SizedBox(width: 4.w),
          Text(
            _statusLabel(status),
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 11.sp,
              fontWeight: FontWeight.w700,
              color: _statusColor(status),
            ),
          ),
        ],
      ),
    );
  }
}

class _SchemaLoading extends StatelessWidget {
  const _SchemaLoading();
  @override
  Widget build(BuildContext context) {
    return ListView(
      children: const [
        FieldShimmer(label: 'تحميل النموذج'),
        SizedBox(height: 12),
        FieldShimmer(label: ''),
        SizedBox(height: 12),
        FieldShimmer(label: ''),
      ],
    );
  }
}

class _EmptyHint extends StatelessWidget {
  final IconData icon;
  final String text;
  const _EmptyHint({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: EdgeInsets.all(24.r),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 36.r, color: AppColors.inkSoft),
            SizedBox(height: 10.h),
            Text(
              text,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 13.sp,
                color: AppColors.textHint,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

IconData _statusIcon(SectionEntryStatus status) {
  switch (status) {
    case SectionEntryStatus.complete:
      return Icons.check_circle;
    case SectionEntryStatus.draft:
      return Icons.edit_note;
    case SectionEntryStatus.error:
      return Icons.error;
    case SectionEntryStatus.empty:
      return Icons.radio_button_unchecked;
  }
}

Color _statusColor(SectionEntryStatus status) {
  switch (status) {
    case SectionEntryStatus.complete:
      return AppColors.successGreen;
    case SectionEntryStatus.draft:
      return AppColors.goldDeep;
    case SectionEntryStatus.error:
      return AppColors.errorRed;
    case SectionEntryStatus.empty:
      return AppColors.inkSoft;
  }
}

String _statusLabel(SectionEntryStatus status) {
  switch (status) {
    case SectionEntryStatus.complete:
      return 'مكتمل';
    case SectionEntryStatus.draft:
      return 'مسودة';
    case SectionEntryStatus.error:
      return 'ناقص';
    case SectionEntryStatus.empty:
      return 'جديد';
  }
}

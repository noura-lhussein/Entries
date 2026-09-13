import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../data/models/builder_models.dart';
import '../bloc/info_browse_bloc.dart';
import '../bloc/info_browse_event.dart';
import '../bloc/info_browse_state.dart';
import '../widgets/info_row_edit_sheet.dart';
import '../widgets/info_filter_panel.dart';

class InfoBrowseScreen extends StatelessWidget {
  final InfoBrowseMode mode;
  final int? currentUserId;
  final bool canWrite;
  final bool canConfirm;
  final bool isAdmin;
  final String title;
  final String subtitle;
  final IconData icon;

  const InfoBrowseScreen({
    super.key,
    required this.mode,
    required this.title,
    required this.subtitle,
    required this.icon,
    this.currentUserId,
    this.canWrite = false,
    this.canConfirm = false,
    this.isAdmin = false,
  });

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<InfoBrowseBloc>()
        ..add(InfoBrowseStarted(
          mode: mode,
          currentUserId: currentUserId,
          canWrite: canWrite,
          canConfirm: canConfirm,
          isAdmin: isAdmin,
        )),
      child: _InfoBrowseView(
        title: title,
        subtitle: subtitle,
        icon: icon,
      ),
    );
  }
}

class MyDataScreen extends StatelessWidget {
  final int? currentUserId;
  final bool canWrite;
  final bool isAdmin;
  const MyDataScreen({
    super.key,
    this.currentUserId,
    this.canWrite = false,
    this.isAdmin = false,
  });

  @override
  Widget build(BuildContext context) {
    return InfoBrowseScreen(
      mode: InfoBrowseMode.myData,
      currentUserId: currentUserId,
      canWrite: canWrite,
      isAdmin: isAdmin,
      title: 'بياناتي',
      subtitle: 'عرض وإدارة البيانات التي قمت بإضافتها',
      icon: Icons.storage_outlined,
    );
  }
}

class EnteredDataScreen extends StatelessWidget {
  final bool isAdmin;
  final bool canConfirm;
  const EnteredDataScreen({
    super.key,
    this.isAdmin = false,
    this.canConfirm = false,
  });

  @override
  Widget build(BuildContext context) {
    return InfoBrowseScreen(
      mode: InfoBrowseMode.submitted,
      isAdmin: isAdmin,
      canWrite: false,
      canConfirm: canConfirm,
      title: 'البيانات المدخلة',
      subtitle: 'استعراض السجلات حسب صلاحياتك',
      icon: Icons.table_rows_outlined,
    );
  }
}

class _InfoBrowseView extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  const _InfoBrowseView({
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return BlocListener<InfoBrowseBloc, InfoBrowseState>(
      listenWhen: (p, c) =>
          p.actionMessage != c.actionMessage || p.actionError != c.actionError,
      listener: (context, state) {
        final msg = state.actionMessage ?? state.actionError;
        if (msg == null || msg.isEmpty) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              msg,
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
            ),
            backgroundColor:
                state.actionError != null ? AppColors.red2 : AppColors.forest1,
          ),
        );
        context.read<InfoBrowseBloc>().add(const InfoBrowseActionCleared());
      },
      child: ListView(
      padding: EdgeInsets.fromLTRB(12.r, 8.r, 12.r, 16.r),
      children: [
        ForestPageHeader(title: title, subtitle: subtitle, icon: icon),
        SizedBox(height: 10.h),
        const InfoFilterPanel(),
        SizedBox(height: 10.h),
        const _Body(),
      ],
    ),
    );
  }
}


class _Body extends StatelessWidget {
  const _Body();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<InfoBrowseBloc, InfoBrowseState>(
      buildWhen: (p, c) =>
          p.bootstrapping != c.bootstrapping ||
          p.loadError != c.loadError ||
          p.search != c.search ||
          p.mainId != c.mainId ||
          p.subId != c.subId ||
          p.titleCategoryId != c.titleCategoryId ||
          p.titleId != c.titleId ||
          p.titles != c.titles,
      builder: (context, state) {
        if (state.bootstrapping) {
          return Padding(
            padding: EdgeInsets.symmetric(vertical: 32.h),
            child: const Center(child: CircularProgressIndicator()),
          );
        }
        if (state.loadError != null && state.titles.isEmpty) {
          return FormCard(
            child: Column(
              children: [
                Text(
                  state.loadError!,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 13.sp,
                    color: AppColors.errorRed,
                  ),
                ),
                SizedBox(height: 10.h),
                FilledButton(
                  onPressed: () => context
                      .read<InfoBrowseBloc>()
                      .add(const InfoBrowseRefreshed()),
                  child: const Text('إعادة المحاولة'),
                ),
              ],
            ),
          );
        }
        final titles = state.visibleTitles;
        if (titles.isEmpty) {
          return FormCard(
            child: Text(
              'لا توجد معلومات',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 13.sp,
                color: AppColors.textHint,
              ),
            ),
          );
        }
        return Column(
          children: [
            for (final t in titles) ...[
              _TitleAccordion(title: t),
              SizedBox(height: 8.h),
            ],
          ],
        );
      },
    );
  }
}

class _TitleAccordion extends StatelessWidget {
  final BuilderTitle title;
  const _TitleAccordion({required this.title});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<InfoBrowseBloc, InfoBrowseState>(
      buildWhen: (p, c) {
        final open = c.expandedTitleId == title.id || p.expandedTitleId == title.id;
        return p.expandedTitleId != c.expandedTitleId ||
            p.rowCounts[title.id] != c.rowCounts[title.id] ||
            p.canWrite != c.canWrite ||
            p.canConfirm != c.canConfirm ||
            p.mode != c.mode ||
            p.attributeLabels != c.attributeLabels ||
            p.attributes != c.attributes ||
            (open &&
                (p.rows != c.rows ||
                    p.loadingRows != c.loadingRows ||
                    p.loadingMore != c.loadingMore));
      },
      builder: (context, state) {
        final open = state.expandedTitleId == title.id;
        final count = state.rowCounts[title.id];
        return FormCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              InkWell(
                onTap: () => context
                    .read<InfoBrowseBloc>()
                    .add(InfoBrowseTitleToggled(title.id)),
                child: Row(
                  children: [
                    Icon(
                      open
                          ? Icons.expand_more_rounded
                          : Icons.chevron_left_rounded,
                      color: AppColors.goldDeep,
                    ),
                    SizedBox(width: 6.w),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            title.name,
                            textAlign: TextAlign.start,
                            style: TextStyle(
                              fontFamily: 'Cairo',
                              fontSize: 13.sp,
                              fontWeight: FontWeight.w800,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          if (title.categoryName != null &&
                              title.categoryName!.trim().isNotEmpty)
                            Text(
                              title.categoryName!,
                              textAlign: TextAlign.start,
                              style: TextStyle(
                                fontFamily: 'Cairo',
                                fontSize: 11.sp,
                                color: AppColors.textHint,
                              ),
                            ),
                        ],
                      ),
                    ),
                    Container(
                      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
                      decoration: BoxDecoration(
                        color: AppColors.goldPale,
                        borderRadius: BorderRadius.circular(20.r),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Text(
                        count == null ? '…' : '$count سجل',
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 11.sp,
                          fontWeight: FontWeight.w800,
                          color: AppColors.goldDeep,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              if (open) ...[
                SizedBox(height: 10.h),
                if (state.loadingRows && state.rows.isEmpty)
                  const Center(child: CircularProgressIndicator())
                else if (state.rows.isEmpty)
                  Text(
                    'لا توجد معلومات',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 12.sp,
                      color: AppColors.textHint,
                    ),
                  )
                else ...[
                  for (final row in state.rows) ...[
                    _RowCard(
                      row: row,
                      labels: state.attributeLabels,
                      attributes: state.attributes,
                      canWrite: state.canWrite,
                      canConfirm: state.canConfirm,
                      showNotes: state.mode == InfoBrowseMode.submitted,
                    ),
                    SizedBox(height: 8.h),
                  ],
                  if (state.rows.length < state.rowsTotal)
                    TextButton(
                      onPressed: state.loadingMore
                          ? null
                          : () => context
                              .read<InfoBrowseBloc>()
                              .add(const InfoBrowseLoadMore()),
                      child: Text(
                        state.loadingMore ? 'جارٍ التحميل…' : 'عرض المزيد',
                        style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
                      ),
                    ),
                ],
              ],
            ],
          ),
        );
      },
    );
  }
}

class _RowCard extends StatelessWidget {
  final InfoRecord row;
  final Map<String, String> labels;
  final List<BuilderAttribute> attributes;
  final bool canWrite;
  final bool canConfirm;
  final bool showNotes;
  const _RowCard({
    required this.row,
    required this.labels,
    required this.attributes,
    required this.canWrite,
    this.canConfirm = false,
    this.showNotes = false,
  });

  String _labelFor(String key) {
    final mapped = labels[key]?.trim() ?? '';
    if (mapped.isNotEmpty) return mapped;
    for (final a in attributes) {
      if ('${a.id}' == key && a.label.trim().isNotEmpty) return a.label;
    }
    return key;
  }

  String _displayValue(String? raw) {
    final v = raw?.trim() ?? '';
    if (v.isEmpty || v == '—') return '—';
    return v;
  }

  /// Every title attribute, including empty cells — same as the web table.
  List<(String label, String value)> _allFields() {
    final seen = <String>{};
    final out = <(String, String)>[];
    void add(String key) {
      if (!seen.add(key)) return;
      out.add((_labelFor(key), _displayValue(row.fields[key])));
    }

    final titleId = row.titleId;
    if (titleId != null) {
      for (final a in attributes) {
        if (a.titleId == titleId && a.id > 0) add('${a.id}');
      }
    }
    for (final key in row.fields.keys) {
      add(key);
    }
    return out;
  }

  Future<void> _edit(BuildContext context) async {
    if (row.isAccepted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'لا يمكن تعديل سجل موافق عليه',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.errorRed,
        ),
      );
      return;
    }
    if (row.infoIds.isEmpty && row.fields.isEmpty) return;
    final saved = await showInfoRowEditSheet(
      context,
      row: row,
      attributes: attributes,
      labels: labels,
    );
    if (!context.mounted || !saved) return;
    context.read<InfoBrowseBloc>().add(const InfoBrowseRefreshed());
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'تم حفظ التعديلات',
          style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
        ),
        backgroundColor: AppColors.forest1,
      ),
    );
  }

  Future<void> _delete(BuildContext context) async {
    if (row.isAccepted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'لا يمكن تعديل سجل موافق عليه',
            style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
          ),
          backgroundColor: AppColors.errorRed,
        ),
      );
      return;
    }
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(
          'حذف السجل',
          style: TextStyle(fontFamily: 'Cairo', fontWeight: FontWeight.w800),
        ),
        content: Text(
          'هل تريد حذف هذا السجل؟ لا يمكن التراجع عن العملية.',
          style: TextStyle(fontFamily: 'Cairo'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('إلغاء'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(
              'حذف',
              style: TextStyle(color: AppColors.errorRed),
            ),
          ),
        ],
      ),
    );
    if (!context.mounted || ok != true) return;
    context.read<InfoBrowseBloc>().add(InfoBrowseRowDeleteRequested(row));
  }

  Future<void> _commitNote(BuildContext context) async {
    final note = await _showCommitNoteDialog(
      context,
      initial: row.commitNote,
    );
    if (!context.mounted || note == null) return;
    context.read<InfoBrowseBloc>().add(
          InfoBrowseRowCommitNoteRequested(row, note),
        );
  }

  @override
  Widget build(BuildContext context) {
    final entries = _allFields();
    final allowEdit = canWrite && !row.isAccepted;
    final hasIds = row.infoIds.isNotEmpty;
    final allowApprove = canConfirm && hasIds && !row.isAccepted;
    final allowReject = canConfirm && hasIds && !row.isRejected;
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
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (row.subMainName.isNotEmpty)
                Expanded(
                  child: Text(
                    row.subMainName,
                    textAlign: TextAlign.start,
                    softWrap: true,
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 11.sp,
                      color: AppColors.textHint,
                    ),
                  ),
                )
              else
                const Spacer(),
              SizedBox(width: 8.w),
              _StatusChip(status: row.confirmed),
            ],
          ),
          if (row.userName.isNotEmpty) ...[
            SizedBox(height: 4.h),
            Text(
              'أدخل بواسطة: ${row.userName}',
              textAlign: TextAlign.start,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 11.sp,
                color: AppColors.textHint,
              ),
            ),
          ],
          if (entries.isNotEmpty) ...[
            SizedBox(height: 8.h),
            Wrap(
              spacing: 10.w,
              runSpacing: 8.h,
              children: [
                for (final e in entries)
                  SizedBox(
                    width: 140.w,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          e.$1,
                          textAlign: TextAlign.start,
                          softWrap: true,
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            fontSize: 10.sp,
                            color: AppColors.textHint,
                          ),
                        ),
                        Text(
                          e.$2,
                          textAlign: TextAlign.start,
                          softWrap: true,
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            fontSize: 12.sp,
                            fontWeight: FontWeight.w700,
                            color: e.$2 == '—'
                                ? AppColors.textHint
                                : AppColors.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ],
          if (showNotes) ...[
            SizedBox(height: 8.h),
            _NoteField(label: 'ملاحظة متابعة', value: _displayValue(row.commitNote)),
            SizedBox(height: 8.h),
            _NoteField(
              label: 'ملاحظة التأكيد',
              value: _displayValue(row.confirmNote),
            ),
          ],
          if (canWrite) ...[
            SizedBox(height: 8.h),
            Wrap(
              spacing: 4.w,
              children: [
                TextButton.icon(
                  onPressed: allowEdit ? () => _edit(context) : null,
                  icon: Icon(Icons.edit_outlined, size: 16.r),
                  label: Text(
                    'تعديل',
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
                  ),
                ),
                TextButton.icon(
                  onPressed: allowEdit ? () => _delete(context) : null,
                  icon: Icon(
                    Icons.delete_outline,
                    size: 16.r,
                    color: allowEdit ? AppColors.errorRed : AppColors.textHint,
                  ),
                  label: Text(
                    'حذف',
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 12.sp,
                      color: allowEdit ? AppColors.errorRed : AppColors.textHint,
                    ),
                  ),
                ),
              ],
            ),
          ],
          if (canConfirm) ...[
            SizedBox(height: 8.h),
            Wrap(
              spacing: 4.w,
              runSpacing: 4.h,
              children: [
                TextButton.icon(
                  onPressed: allowApprove
                      ? () => context.read<InfoBrowseBloc>().add(
                            InfoBrowseRowConfirmRequested(row, approve: true),
                          )
                      : null,
                  icon: Icon(Icons.check_circle_outline, size: 16.r),
                  label: Text(
                    'موافقة',
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
                  ),
                ),
                TextButton.icon(
                  onPressed: allowReject
                      ? () => context.read<InfoBrowseBloc>().add(
                            InfoBrowseRowConfirmRequested(row, approve: false),
                          )
                      : null,
                  icon: Icon(
                    Icons.cancel_outlined,
                    size: 16.r,
                    color: allowReject ? AppColors.errorRed : AppColors.textHint,
                  ),
                  label: Text(
                    'إلغاء الموافقة',
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 12.sp,
                      color: allowReject ? AppColors.errorRed : AppColors.textHint,
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: hasIds ? () => _commitNote(context) : null,
                  icon: Icon(Icons.sticky_note_2_outlined, size: 16.r),
                  label: Text(
                    'ملاحظة متابعة',
                    style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp),
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

class _StatusChip extends StatelessWidget {
  final String status;
  const _StatusChip({required this.status});

  @override
  Widget build(BuildContext context) {
    final label = switch (status) {
      'accept' => 'موافق عليه',
      'reject' => 'مرفوض',
      _ => 'بانتظار التأكيد',
    };
    final color = switch (status) {
      'accept' => AppColors.successGreen,
      'reject' => AppColors.errorRed,
      _ => AppColors.goldDeep,
    };
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 3.h),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20.r),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontFamily: 'Cairo',
          fontSize: 10.sp,
          fontWeight: FontWeight.w800,
          color: color,
        ),
      ),
    );
  }
}

class _NoteField extends StatelessWidget {
  final String label;
  final String value;
  const _NoteField({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          textAlign: TextAlign.start,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 10.sp,
            color: AppColors.textHint,
          ),
        ),
        Text(
          value,
          textAlign: TextAlign.start,
          softWrap: true,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 12.sp,
            fontWeight: FontWeight.w700,
            color: value == '—' ? AppColors.textHint : AppColors.textPrimary,
          ),
        ),
      ],
    );
  }
}

Future<String?> _showCommitNoteDialog(
  BuildContext context, {
  required String initial,
}) {
  final controller = TextEditingController(text: initial);
  return showDialog<String>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(
        'ملاحظة مراجعة (دون تغيير حالة التأكيد)',
        style: TextStyle(
          fontFamily: 'Cairo',
          fontWeight: FontWeight.w800,
          fontSize: 15.sp,
        ),
      ),
      content: TextField(
        controller: controller,
        maxLines: 4,
        textAlign: TextAlign.start,
        decoration: InputDecoration(
          hintText: 'تُحفظ كمتابعة منفصلة؛ لا توافق على الصف ولا ترفضه.',
          hintStyle: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 12.sp,
            color: AppColors.textHint,
          ),
        ),
        style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx),
          child: const Text('إلغاء'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(ctx, controller.text),
          child: const Text('تطبيق'),
        ),
      ],
    ),
  ).whenComplete(controller.dispose);
}

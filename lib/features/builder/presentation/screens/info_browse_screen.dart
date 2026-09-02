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
import '../widgets/labeled_select_field.dart';

class InfoBrowseScreen extends StatelessWidget {
  final InfoBrowseMode mode;
  final int? currentUserId;
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
  });

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => getIt<InfoBrowseBloc>()
        ..add(InfoBrowseStarted(mode: mode, currentUserId: currentUserId)),
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
  const MyDataScreen({super.key, this.currentUserId});

  @override
  Widget build(BuildContext context) {
    return InfoBrowseScreen(
      mode: InfoBrowseMode.myData,
      currentUserId: currentUserId,
      title: 'بياناتي',
      subtitle: 'عرض وإدارة البيانات التي قمت بإضافتها',
      icon: Icons.storage_outlined,
    );
  }
}

class EnteredDataScreen extends StatelessWidget {
  const EnteredDataScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const InfoBrowseScreen(
      mode: InfoBrowseMode.submitted,
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
    return ListView(
      padding: EdgeInsets.fromLTRB(12.r, 8.r, 12.r, 16.r),
      children: [
        _Header(title: title, subtitle: subtitle, icon: icon),
        SizedBox(height: 10.h),
        const _Filters(),
        SizedBox(height: 10.h),
        const _Body(),
      ],
    );
  }
}

class _Header extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  const _Header({
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(14.r),
      decoration: BoxDecoration(
        gradient: AppColors.cardForestGradient,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Row(
        children: [
          Container(
            padding: EdgeInsets.all(10.r),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(8.r),
            ),
            child: Icon(icon, color: AppColors.golden1, size: 28.r),
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  textAlign: TextAlign.right,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 16.sp,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 3.h),
                Text(
                  subtitle,
                  textAlign: TextAlign.right,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 11.sp,
                    color: Colors.white70,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Filters extends StatelessWidget {
  const _Filters();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<InfoBrowseBloc, InfoBrowseState>(
      buildWhen: (p, c) =>
          p.mainSections != c.mainSections ||
          p.subSections != c.subSections ||
          p.titles != c.titles ||
          p.mainId != c.mainId ||
          p.subId != c.subId ||
          p.titleId != c.titleId ||
          p.confirmed != c.confirmed ||
          p.search != c.search,
      builder: (context, state) {
        final bloc = context.read<InfoBrowseBloc>();
        return FormCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                textAlign: TextAlign.right,
                textDirection: TextDirection.rtl,
                onChanged: (v) => bloc.add(InfoBrowseSearchChanged(v)),
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 13.sp,
                  color: AppColors.textPrimary,
                ),
                decoration: InputDecoration(
                  hintText: 'بحث العنوان أو القيمة',
                  prefixIcon: Icon(Icons.search, size: 18.r),
                ),
              ),
              SizedBox(height: 10.h),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: LabeledSelectField(
                      label: 'القسم الرئيسي',
                      hint: '-- الكل --',
                      value: state.mainId?.toString(),
                      options: [
                        const BuilderSelectOption(id: 0, value: '__all__', label: 'الكل'),
                        for (final m in state.mainSections)
                          BuilderSelectOption(id: m.id, label: m.name),
                      ],
                      onChanged: (v) => bloc.add(
                        InfoBrowseMainFilterChanged(
                          v == null || v == '__all__' ? null : int.tryParse(v),
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 10.w),
                  Expanded(
                    child: LabeledSelectField(
                      label: 'القسم الفرعي',
                      hint: '-- الكل --',
                      value: state.subId?.toString(),
                      enabled: state.mainId != null || state.visibleSubs.isNotEmpty,
                      options: [
                        const BuilderSelectOption(id: 0, value: '__all__', label: 'الكل'),
                        for (final s in state.visibleSubs)
                          BuilderSelectOption(id: s.id, label: s.displayLabel),
                      ],
                      onChanged: (v) => bloc.add(
                        InfoBrowseSubFilterChanged(
                          v == null || v == '__all__' ? null : int.tryParse(v),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(height: 10.h),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: LabeledSelectField(
                      label: 'العنوان',
                      hint: '-- الكل --',
                      value: state.titleId?.toString(),
                      options: [
                        const BuilderSelectOption(id: 0, value: '__all__', label: 'الكل'),
                        for (final t in state.titles)
                          BuilderSelectOption(id: t.id, label: t.name),
                      ],
                      onChanged: (v) => bloc.add(
                        InfoBrowseTitleFilterChanged(
                          v == null || v == '__all__' ? null : int.tryParse(v),
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 10.w),
                  Expanded(
                    child: LabeledSelectField(
                      label: 'حالة التأكيد',
                      hint: 'الجميع',
                      value: state.confirmed,
                      options: const [
                        BuilderSelectOption(id: 0, value: '__all__', label: 'الجميع'),
                        BuilderSelectOption(id: 1, value: 'waiting', label: 'بانتظار التأكيد'),
                        BuilderSelectOption(id: 2, value: 'accept', label: 'موافق عليه'),
                        BuilderSelectOption(id: 3, value: 'reject', label: 'مرفوض'),
                      ],
                      onChanged: (v) => bloc.add(
                        InfoBrowseStatusFilterChanged(
                          v == null || v == '__all__' ? null : v,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

class _Body extends StatelessWidget {
  const _Body();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<InfoBrowseBloc, InfoBrowseState>(
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
      buildWhen: (p, c) =>
          p.expandedTitleId != c.expandedTitleId ||
          p.rowCounts[title.id] != c.rowCounts[title.id] ||
          p.rows != c.rows ||
          p.loadingRows != c.loadingRows ||
          p.loadingMore != c.loadingMore,
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
                          : Icons.chevron_right_rounded,
                      color: AppColors.inkSoft,
                    ),
                    SizedBox(width: 6.w),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            title.name,
                            textAlign: TextAlign.right,
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
                              textAlign: TextAlign.right,
                              style: TextStyle(
                                fontFamily: 'Cairo',
                                fontSize: 11.sp,
                                color: AppColors.textHint,
                              ),
                            ),
                        ],
                      ),
                    ),
                    Text(
                      count == null ? '…' : '$count سجل',
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 11.sp,
                        fontWeight: FontWeight.w700,
                        color: AppColors.inkSoft,
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
                    _RowCard(row: row),
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
  const _RowCard({required this.row});

  @override
  Widget build(BuildContext context) {
    final entries = row.fields.entries
        .where((e) => e.value.trim().isNotEmpty && e.value != '—')
        .toList();
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
            children: [
              _StatusChip(status: row.confirmed),
              const Spacer(),
              if (row.subMainName.isNotEmpty)
                Expanded(
                  child: Text(
                    row.subMainName,
                    textAlign: TextAlign.right,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 11.sp,
                      color: AppColors.textHint,
                    ),
                  ),
                ),
            ],
          ),
          if (row.userName.isNotEmpty) ...[
            SizedBox(height: 4.h),
            Text(
              'أدخل بواسطة: ${row.userName}',
              textAlign: TextAlign.right,
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
                for (final e in entries.take(8))
                  SizedBox(
                    width: 140.w,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          e.key,
                          textAlign: TextAlign.right,
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            fontSize: 10.sp,
                            color: AppColors.textHint,
                          ),
                        ),
                        Text(
                          e.value,
                          textAlign: TextAlign.right,
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

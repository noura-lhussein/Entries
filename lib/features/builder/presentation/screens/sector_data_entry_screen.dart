import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../data/models/builder_models.dart';
import '../bloc/data_entry_bloc.dart';
import '../bloc/data_entry_event.dart';
import '../bloc/data_entry_state.dart';
import '../widgets/data_entry_workspace.dart';
import '../widgets/labeled_select_field.dart';

/// Dynamic data-entry shell matching report_moe builder (main → sub → titles).
class SectorDataEntryScreen extends StatelessWidget {
  final DataEntrySectorFilter sector;
  final String title;
  final String subtitle;
  final IconData icon;
  final String emptyMainsHint;

  const SectorDataEntryScreen({
    super.key,
    required this.sector,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.emptyMainsHint,
  });

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthBloc>().state;
    final isAdmin =
        auth is AuthAuthenticated && auth.user.appRole == AppRole.admin;
    final canWrite = auth is AuthAuthenticated &&
        (auth.user.appRole == AppRole.admin || auth.user.canEnterData);
    return BlocProvider(
      create: (_) => getIt<DataEntryBloc>()
        ..add(DataEntryStarted(
          sector: sector,
          isAdmin: isAdmin,
        )),
      child: canWrite
          ? _SectorEntryView(
              title: title,
              subtitle: subtitle,
              icon: icon,
              emptyMainsHint: emptyMainsHint,
            )
          : const _NoWritePermission(),
    );
  }
}

class _SectorEntryView extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final String emptyMainsHint;

  const _SectorEntryView({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.emptyMainsHint,
  });

  @override
  Widget build(BuildContext context) {
    return BlocListener<DataEntryBloc, DataEntryState>(
      listenWhen: (p, c) =>
          p.savePhase != c.savePhase ||
          p.saveMessage != c.saveMessage ||
          p.loadError != c.loadError,
      listener: (context, state) {
        final msg = state.loadError ??
            (state.savePhase == DataEntrySavePhase.saved ||
                    state.savePhase == DataEntrySavePhase.failed
                ? state.saveMessage
                : null);
        if (msg == null || msg.trim().isEmpty) return;
        if (state.savePhase == DataEntrySavePhase.saving) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              msg,
              style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
            ),
            backgroundColor: state.savePhase == DataEntrySavePhase.failed ||
                    state.loadError != null
                ? AppColors.red2
                : AppColors.forest1,
          ),
        );
      },
      child: ListView(
        padding: EdgeInsets.fromLTRB(
          12.r,
          8.r,
          12.r,
          16.r + MediaQuery.viewInsetsOf(context).bottom,
        ),
        keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
        children: [
          _Header(title: title, subtitle: subtitle, icon: icon),
          SizedBox(height: 10.h),
          _SectionPickers(emptyMainsHint: emptyMainsHint),
          SizedBox(height: 8.h),
          const _Body(),
        ],
      ),
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

class _SectionPickers extends StatelessWidget {
  final String emptyMainsHint;
  const _SectionPickers({required this.emptyMainsHint});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<DataEntryBloc, DataEntryState>(
      buildWhen: (p, c) =>
          p.mainSections != c.mainSections ||
          p.subSections != c.subSections ||
          p.selectedMainId != c.selectedMainId ||
          p.selectedSubId != c.selectedSubId ||
          p.loadingSubs != c.loadingSubs ||
          p.bootstrapping != c.bootstrapping,
      builder: (context, state) {
        return FormCard(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: LabeledSelectField(
                  label: 'القسم الرئيسي',
                  hint: state.mainSections.isEmpty
                      ? emptyMainsHint
                      : '-- اختر القسم --',
                  value: state.selectedMainId?.toString(),
                  options: [
                    for (final m in state.mainSections)
                      BuilderSelectOption(id: m.id, label: m.name),
                  ],
                  onChanged: (v) {
                    final id = int.tryParse(v ?? '');
                    context.read<DataEntryBloc>().add(MainSectionSelected(id));
                  },
                ),
              ),
              SizedBox(width: 10.w),
              Expanded(
                child: state.loadingSubs
                    ? const FieldShimmer(label: 'القسم الفرعي')
                    : LabeledSelectField(
                        label: 'القسم الفرعي',
                        hint: '-- اختر القسم الفرعي --',
                        value: state.selectedSubId?.toString(),
                        enabled: state.selectedMainId != null,
                        options: [
                          for (final s in state.subSections)
                            BuilderSelectOption(id: s.id, label: s.displayLabel),
                        ],
                        onChanged: (v) {
                          final id = int.tryParse(v ?? '');
                          context
                              .read<DataEntryBloc>()
                              .add(SubSectionSelected(id));
                        },
                      ),
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
    return BlocBuilder<DataEntryBloc, DataEntryState>(
      buildWhen: (p, c) =>
          p.bootstrapping != c.bootstrapping ||
          p.selectedSubId != c.selectedSubId ||
          p.loadError != c.loadError,
      builder: (context, state) {
        if (state.bootstrapping) {
          return Padding(
            padding: EdgeInsets.symmetric(vertical: 32.h),
            child: const Center(child: CircularProgressIndicator()),
          );
        }
        if (state.loadError != null) {
          return _LoadErrorView(message: state.loadError!);
        }
        if (state.selectedSubId == null) {
          return Padding(
            padding: EdgeInsets.symmetric(vertical: 24.h, horizontal: 12.w),
            child: Text(
              'اختر القسم الفرعي لفتح نماذج الإدخال الديناميكية.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontFamily: 'Cairo',
                fontSize: 13.sp,
                color: AppColors.textHint,
              ),
            ),
          );
        }
        return const DataEntryWorkspace();
      },
    );
  }
}

class _LoadErrorView extends StatelessWidget {
  final String message;
  const _LoadErrorView({required this.message});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(20.r),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.cloud_off_outlined, size: 40.r, color: AppColors.inkSoft),
          SizedBox(height: 12.h),
          Text(
            message,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontFamily: 'Cairo',
              fontSize: 13.sp,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          SizedBox(height: 16.h),
          FilledButton.icon(
            onPressed: () {
              final bloc = context.read<DataEntryBloc>();
              bloc.add(DataEntryStarted(
                sector: bloc.state.sector,
                isAdmin: bloc.state.isAdmin,
              ));
            },
            icon: const Icon(Icons.refresh),
            label: const Text('إعادة المحاولة'),
          ),
        ],
      ),
    );
  }
}

class _NoWritePermission extends StatelessWidget {
  const _NoWritePermission();

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.all(24.r),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.lock_outline, size: 40.r, color: AppColors.inkSoft),
              SizedBox(height: 12.h),
              Text(
                'ليس لديك صلاحية إدخال بيانات. تواصل مع المدير لمنح الصلاحية.',
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../builder/data/models/builder_models.dart';
import '../../../builder/presentation/bloc/data_entry_bloc.dart';
import '../../../builder/presentation/bloc/data_entry_event.dart';
import '../../../builder/presentation/bloc/data_entry_state.dart';
import '../../../builder/presentation/widgets/data_entry_workspace.dart';
import '../../../builder/presentation/widgets/labeled_select_field.dart';
import '../widgets/electricity_header.dart';

class ElectricityScreen extends StatelessWidget {
  const ElectricityScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.read<AuthBloc>().state;
    final isAdmin =
        auth is AuthAuthenticated && auth.user.appRole == AppRole.admin;
    return BlocProvider(
      create: (_) => getIt<DataEntryBloc>()
        ..add(DataEntryStarted(
          sector: DataEntrySectorFilter.electricity,
          isAdmin: isAdmin,
        )),
      child: const _ElectricityView(),
    );
  }
}

class _ElectricityView extends StatelessWidget {
  const _ElectricityView();

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
      child: SafeArea(
        child: Padding(
          padding: EdgeInsets.fromLTRB(16.r, 16.r, 16.r, 8.r),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const ElectricityHeader(),
              SizedBox(height: 14.h),
              const _SectionPickers(),
              SizedBox(height: 12.h),
              const Expanded(child: _Body()),
            ],
          ),
        ),
      ),
    );
  }
}

class _SectionPickers extends StatelessWidget {
  const _SectionPickers();

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
          child: Column(
            children: [
              LabeledSelectField(
                label: 'القسم الرئيسي',
                hint: state.mainSections.isEmpty
                    ? 'لا توجد أقسام كهرباء متاحة'
                    : '-- اختر القسم الرئيسي --',
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
              SizedBox(height: 12.h),
              if (state.loadingSubs)
                const FieldShimmer(label: 'القسم الفرعي')
              else
                LabeledSelectField(
                  label: 'القسم الفرعي',
                  hint: '-- اختر القسم الفرعي --',
                  value: state.selectedSubId?.toString(),
                  enabled: state.selectedMainId != null,
                  options: [
                    for (final s in state.subSections)
                      BuilderSelectOption(id: s.id, label: s.name),
                  ],
                  onChanged: (v) {
                    final id = int.tryParse(v ?? '');
                    context.read<DataEntryBloc>().add(SubSectionSelected(id));
                  },
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
          return const Center(child: CircularProgressIndicator());
        }
        if (state.selectedSubId == null) {
          return Center(
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

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/widgets/metric_entry_table.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../bloc/electricity_bloc.dart';
import '../bloc/electricity_event.dart';
import '../bloc/electricity_state.dart';
import 'dynamic_rows_section.dart';
import 'electricity_report_meta_card.dart';
import 'fuel_tanks_table.dart';
import 'governorates_consumption_table.dart';
import 'hydraulic_energy_section.dart';
import 'models/electricity_fields_data.dart';
import 'notes_section.dart';

class ElectricityDailyForm extends StatelessWidget {
  final Map<String, TextEditingController> fieldCtrls;
  final Map<String, TextEditingController> consumedCtrls;
  final Map<String, TextEditingController> allocatedCtrls;
  final Map<String, TextEditingController> tankCtrls;
  final Map<String, TextEditingController> tankMaxCtrls;
  final Map<String, TextEditingController> hydraulicCtrls;
  final TextEditingController arabicNotesCtrl;
  final TextEditingController englishNotesCtrl;
  final GlobalKey<DynamicRowsSectionState> maintKey;
  final GlobalKey<DynamicRowsSectionState> genIncKey;
  final GlobalKey<DynamicRowsSectionState> gridIncKey;
  final ValueChanged<DateTime> onDateChanged;
  final ValueChanged<ElectricityState> onSave;

  const ElectricityDailyForm({
    super.key,
    required this.fieldCtrls,
    required this.consumedCtrls,
    required this.allocatedCtrls,
    required this.tankCtrls,
    required this.tankMaxCtrls,
    required this.hydraulicCtrls,
    required this.arabicNotesCtrl,
    required this.englishNotesCtrl,
    required this.maintKey,
    required this.genIncKey,
    required this.gridIncKey,
    required this.onDateChanged,
    required this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ElectricityReportMetaCard(onDateChanged: onDateChanged),
        SizedBox(height: 14.h),
        ...kElectricityMetricSections.map(
          (section) => Padding(
            padding: EdgeInsets.only(bottom: 14.h),
            child: MetricEntryTable(
              title: section.titleAr,
              rows: [
                for (final f in section.fields)
                  MetricEntryRow(
                    label: f.label,
                    unit: f.unit,
                    controller: fieldCtrls[f.key]!,
                  ),
              ],
            ),
          ),
        ),
        GovernoratesConsumptionTable(
          consumedControllers: consumedCtrls,
          allocatedControllers: allocatedCtrls,
        ),
        SizedBox(height: 14.h),
        FuelTanksTable(
          currentStockControllers: tankCtrls,
          maxCapacityControllers: tankMaxCtrls,
        ),
        SizedBox(height: 14.h),
        HydraulicEnergySection(controllers: hydraulicCtrls),
        SizedBox(height: 14.h),
        BlocBuilder<ElectricityBloc, ElectricityState>(
          buildWhen: (p, c) => p.maintenanceRows != c.maintenanceRows,
          builder: (context, state) => DynamicRowsSection(
            key: maintKey,
            title: 'المجموعات تحت أعمال الصيانة',
            sectionType: DynamicSectionType.maintenance,
            rows: state.maintenanceRows,
            fieldLabels: const ['اسم المجموعة تحت الصيانة'],
            emptyMessage: 'لا توجد مجموعات صيانة لهذا التقرير.',
          ),
        ),
        SizedBox(height: 14.h),
        BlocBuilder<ElectricityBloc, ElectricityState>(
          buildWhen: (p, c) =>
              p.generationIncidentRows != c.generationIncidentRows,
          builder: (context, state) => DynamicRowsSection(
            key: genIncKey,
            title: 'الخطوط',
            sectionType: DynamicSectionType.generationIncidents,
            rows: state.generationIncidentRows,
            fieldLabels: const ['الوقت', 'الوصف'],
            emptyMessage: 'لا توجد حوادث لهذا التقرير.',
          ),
        ),
        SizedBox(height: 14.h),
        BlocBuilder<ElectricityBloc, ElectricityState>(
          buildWhen: (p, c) => p.lineIncidentRows != c.lineIncidentRows,
          builder: (context, state) => DynamicRowsSection(
            key: gridIncKey,
            title: 'مجموعات التوليد',
            sectionType: DynamicSectionType.lineIncidents,
            rows: state.lineIncidentRows,
            fieldLabels: const ['الوقت', 'الإجراء'],
            emptyMessage: 'لا توجد حوادث لهذا التقرير.',
          ),
        ),
        SizedBox(height: 14.h),
        NotesSection(
          arabicNotesCtrl: arabicNotesCtrl,
          englishNotesCtrl: englishNotesCtrl,
        ),
        SizedBox(height: 14.h),
        BlocBuilder<ElectricityBloc, ElectricityState>(
          buildWhen: (p, c) => p.saveStatus != c.saveStatus,
          builder: (context, state) => SaveButton(
            isLoading: state.saveStatus == SaveStatus.saving,
            label: 'حفظ التقرير اليومي',
            onPressed: () => onSave(state),
          ),
        ),
      ],
    );
  }
}

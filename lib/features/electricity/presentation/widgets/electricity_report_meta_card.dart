import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/widgets/shared_widgets.dart';
import '../bloc/electricity_bloc.dart';
import '../bloc/electricity_event.dart';
import '../bloc/electricity_state.dart';
import 'time_picker_field.dart';

class ElectricityReportMetaCard extends StatelessWidget {
  final ValueChanged<DateTime> onDateChanged;

  const ElectricityReportMetaCard({
    super.key,
    required this.onDateChanged,
  });

  @override
  Widget build(BuildContext context) {
    return FormCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: BlocBuilder<ElectricityBloc, ElectricityState>(
              buildWhen: (p, c) => p.reportDate != c.reportDate,
              builder: (context, state) => DatePickerField(
                label: 'تاريخ التقرير',
                initialDate: state.reportDate,
                onDateChanged: (d) {
                  context.read<ElectricityBloc>().add(ReportDateChanged(d));
                  onDateChanged(d);
                },
              ),
            ),
          ),
          SizedBox(width: 12.w),
          Expanded(
            child: BlocBuilder<ElectricityBloc, ElectricityState>(
              buildWhen: (p, c) => p.peakTime != c.peakTime,
              builder: (context, state) => TimePickerField(
                label: 'وقت ذروة التوليد',
                initialTime: state.peakTime,
                onTimeChanged: (t) => context
                    .read<ElectricityBloc>()
                    .add(PeakTimeChanged(t)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

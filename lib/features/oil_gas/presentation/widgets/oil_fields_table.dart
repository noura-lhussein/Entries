import 'package:flutter/material.dart' hide TableCell;
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import 'models/petroleum_data.dart';

class OilFieldsTable extends StatelessWidget {
  final Map<String, TextEditingController> oilCtrls;
  final Map<String, TextEditingController> gasCtrls;
  final List<OilField> fields;
  const OilFieldsTable({
    super.key,
    required this.oilCtrls,
    required this.gasCtrls,
    required this.fields,
  });

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'إنتاج الحقول',
      child: Container(
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(8.r), border: Border.all(color: AppColors.border)),
        clipBehavior: Clip.antiAlias,
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          TableHeaderRow(cols: [ (label: 'الحقل', flex: 3),(label: 'نفط (برميل)', flex: 3),(label: 'غاز (مليون قدم³)', flex: 3), ]),
          ...List.generate(fields.length, (i) => _row(fields[i], i)),
        ]),
      ),
    );
  }

  Widget _row(OilField f, int i) => Container(
    decoration: BoxDecoration(
      color: i.isEven ? AppColors.golden3 : Colors.white,
      border: Border(bottom: BorderSide(color: AppColors.divider, width: 0.5))),
    padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 5.h),
    child: Row(children: [
       Expanded(flex: 3, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(f.nameAr, textAlign: TextAlign.right,
          style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary)),
        Text(f.code, textAlign: TextAlign.right,
          style: TextStyle(fontFamily: 'Cairo', fontSize: 9.sp, color: AppColors.textHint, letterSpacing: 0.5)),
      ])),
      Expanded(flex: 3, child: Padding(padding: EdgeInsets.symmetric(horizontal: 3.w), child: TableCell(controller: oilCtrls[f.code]))),
     
      Expanded(flex: 3, child: Padding(padding: EdgeInsets.symmetric(horizontal: 3.w), child: TableCell(controller: gasCtrls[f.code]))),
    ]),
  );
}

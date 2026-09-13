import 'package:flutter/material.dart' hide TableCell;
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/theme/app_theme.dart';
import '../../../../../core/widgets/shared_widgets.dart';

class RefineriesTable extends StatelessWidget {
  final Map<String, TextEditingController> controllers;
  final List<String> refineries;
  const RefineriesTable({
    super.key,
    required this.controllers,
    required this.refineries,
  });

  static const _products = ['بنزين', 'ديزل', 'فيول', 'غاز'];
  static const _keys     = ['benzin','diesel','fuel','lpg'];

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: 'إنتاج المصافي',
      child: Container(
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(8.r), border: Border.all(color: AppColors.border)),
        clipBehavior: Clip.antiAlias,
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          TableHeaderRow(cols: [
         (label: 'المصفاة', flex: 3),    ..._products.map((p) => (label: p, flex: 2)),
           
          ]),
          ...List.generate(refineries.length, (i) => _row(refineries[i], i)),
        ]),
      ),
    );
  }

  Widget _row(String refinery, int i) => Container(
    decoration: BoxDecoration(
      color: i.isEven ? AppColors.golden3 : Colors.white,
      border: Border(bottom: BorderSide(color: AppColors.divider, width: 0.5))),
    padding: EdgeInsets.symmetric(horizontal: 8.w, vertical: 5.h),
    child: Row(children: [  Expanded(flex: 3, child: Text(refinery, textAlign: TextAlign.start,
        style: TextStyle(fontFamily: 'Cairo', fontSize: 11.sp, fontWeight: FontWeight.w700, color: AppColors.textPrimary))),
      ..._keys.map((k) => Expanded(flex: 2,
        child: Padding(padding: EdgeInsets.symmetric(horizontal: 2.w), child: TableCell(controller: controllers['${refinery}_$k'])))),
    
    ]),
  );
}

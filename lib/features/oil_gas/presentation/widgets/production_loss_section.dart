import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import 'models/petroleum_data.dart';
import 'petroleum_dyn_row.dart';
import 'petroleum_section_chrome.dart';

class ProductionLossSection extends StatefulWidget {
  final List<OilField> fields;
  const ProductionLossSection({super.key, required this.fields});
  @override
  State<ProductionLossSection> createState() => ProductionLossSectionState();
}

class ProductionLossSectionState extends State<ProductionLossSection> {
  final List<PetroleumDynRow> _rows = [];

  List<OilField> get _fields => widget.fields;

  List<Map<String, dynamic>> collect() {
    final out = <Map<String, dynamic>>[];
    for (final r in _rows) {
      final loss = parsePetroleumNum(r.ctrls[0].text);
      if (loss == null) continue;
      final field = _fields.where((f) => f.nameAr == r.dropVal1).toList();
      out.add({
        'field_code': field.isEmpty ? r.dropVal1 : field.first.code,
        'loss_type': r.dropVal2,
        'estimated_loss_bbl': loss,
        'reason': r.ctrls[1].text.trim(),
      });
    }
    return out;
  }

  @override
  void dispose() {
    for (final r in _rows) {
      r.dispose();
    }
    super.dispose();
  }

  void _addRow() {
    if (_fields.isEmpty) return;
    setState(() => _rows.add(PetroleumDynRow(
          '${DateTime.now().microsecondsSinceEpoch}',
          2,
          dropVal1: _fields.first.nameAr,
          dropVal2: kLossTypes.first,
        )));
  }
  void _removeRow(int i) => setState(() {
        _rows[i].dispose();
        _rows.removeAt(i);
      });

  @override
  Widget build(BuildContext context) {
    return FormCard(
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        PetroleumSectionTitle(title: 'فاقد الإنتاج', onAdd: _addRow),
        ..._rows.asMap().entries.map((e) => _buildRow(e.key, e.value)),
        if (_rows.isEmpty)
          const PetroleumEmptyHint('اضغط «إضافة صف» لإدخال بيانات الفاقد'),
      ]),
    );
  }

  Widget _buildRow(int i, PetroleumDynRow r) => PetroleumDynCard(
        onRemove: () => _removeRow(i),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
              flex: 3,
              child: PetroleumDropField(
                label: 'الحقل',
                value: r.dropVal1!,
                items: _fields.map((f) => f.nameAr).toList(),
                onChanged: (v) => setState(() => r.dropVal1 = v),
              )),
          SizedBox(width: 8.w),
          Expanded(
              flex: 2,
              child: PetroleumDropField(
                label: 'نوع الفاقد',
                value: r.dropVal2!,
                items: kLossTypes,
                onChanged: (v) => setState(() => r.dropVal2 = v),
              )),
          SizedBox(width: 8.w),
          Expanded(
              flex: 2,
              child: AppTextField(
                  label: 'فاقد (برميل)',
                  controller: r.ctrls[0],
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true))),
          SizedBox(width: 8.w),
          Expanded(
              flex: 3,
              child: AppTextField(label: 'السبب', controller: r.ctrls[1])),
        ]),
      );
}

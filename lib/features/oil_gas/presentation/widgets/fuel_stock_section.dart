import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import 'models/petroleum_data.dart';
import 'petroleum_dyn_row.dart';
import 'petroleum_section_chrome.dart';

class FuelStockSection extends StatefulWidget {
  final List<String> depots;
  const FuelStockSection({super.key, this.depots = const []});
  @override
  State<FuelStockSection> createState() => FuelStockSectionState();
}

class FuelStockSectionState extends State<FuelStockSection> {
  final List<PetroleumDynRow> _rows = [];

  List<String> get _depots =>
      widget.depots.isNotEmpty ? widget.depots : kFuelDepots;

  List<Map<String, dynamic>> collect() {
    final out = <Map<String, dynamic>>[];
    for (final r in _rows) {
      final vol = parsePetroleumNum(r.ctrls[0].text);
      if (vol == null) continue;
      out.add({
        'facility_name': r.dropVal1,
        'fuel_type': r.dropVal2,
        'current_volume': vol,
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
    if (_depots.isEmpty) return;
    setState(() => _rows.add(PetroleumDynRow(
          '${DateTime.now().microsecondsSinceEpoch}',
          1,
          dropVal1: _depots.first,
          dropVal2: kFuelTypes.first,
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
        PetroleumSectionTitle(title: 'مخزون الوقود', onAdd: _addRow),
        ..._rows.asMap().entries.map((e) => _buildRow(e.key, e.value)),
        if (_rows.isEmpty)
          const PetroleumEmptyHint('اضغط «إضافة صف» لإدخال بيانات المخزون'),
      ]),
    );
  }

  Widget _buildRow(int i, PetroleumDynRow r) => PetroleumDynCard(
        onRemove: () => _removeRow(i),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
              flex: 3,
              child: PetroleumDropField(
                label: 'المستودع',
                value: r.dropVal1!,
                items: _depots,
                onChanged: (v) => setState(() => r.dropVal1 = v),
              )),
          SizedBox(width: 8.w),
          Expanded(
              flex: 2,
              child: PetroleumDropField(
                label: 'النوع',
                value: r.dropVal2!,
                items: kFuelTypes,
                onChanged: (v) => setState(() => r.dropVal2 = v),
              )),
          SizedBox(width: 8.w),
          Expanded(
              flex: 2,
              child: AppTextField(
                  label: 'الحجم',
                  controller: r.ctrls[0],
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true))),
        ]),
      );
}

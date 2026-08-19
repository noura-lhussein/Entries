import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import 'petroleum_dyn_row.dart';
import 'petroleum_section_chrome.dart';

class ExportsSection extends StatefulWidget {
  const ExportsSection({super.key});
  @override
  State<ExportsSection> createState() => ExportsSectionState();
}

class ExportsSectionState extends State<ExportsSection> {
  final List<PetroleumDynRow> _rows = [];

  List<Map<String, dynamic>> collect() {
    final out = <Map<String, dynamic>>[];
    for (final r in _rows) {
      final crude = parsePetroleumNum(r.ctrls[1].text);
      final rev = parsePetroleumNum(r.ctrls[2].text);
      if (crude == null && rev == null) continue;
      out.add({
        'destination_country': r.ctrls[0].text.trim().isEmpty
            ? '—'
            : r.ctrls[0].text.trim(),
        'crude_bbl': crude ?? 0,
        'revenue_usd': rev ?? 0,
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

  void _addRow() => setState(() =>
      _rows.add(PetroleumDynRow('${DateTime.now().microsecondsSinceEpoch}', 3)));
  void _removeRow(int i) => setState(() {
        _rows[i].dispose();
        _rows.removeAt(i);
      });

  @override
  Widget build(BuildContext context) {
    return FormCard(
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        PetroleumSectionTitle(title: 'الصادرات', onAdd: _addRow),
        ..._rows.asMap().entries.map((e) => _buildRow(e.key, e.value)),
        if (_rows.isEmpty)
          const PetroleumEmptyHint('اضغط «إضافة صف» لإدخال بيانات الصادرات'),
      ]),
    );
  }

  Widget _buildRow(int i, PetroleumDynRow r) => PetroleumDynCard(
        onRemove: () => _removeRow(i),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
              flex: 3,
              child: AppTextField(label: 'بلد الوجهة', controller: r.ctrls[0])),
          SizedBox(width: 8.w),
          Expanded(
              flex: 3,
              child: AppTextField(
                  label: 'نفط خام (برميل)',
                  controller: r.ctrls[1],
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true))),
          SizedBox(width: 8.w),
          Expanded(
              flex: 3,
              child: AppTextField(
                  label: 'الإيرادات (دولار)',
                  controller: r.ctrls[2],
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true))),
        ]),
      );
}

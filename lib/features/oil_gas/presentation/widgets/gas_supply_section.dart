import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../../../core/widgets/shared_widgets.dart';
import 'models/petroleum_data.dart';
import 'petroleum_dyn_row.dart';
import 'petroleum_section_chrome.dart';

class GasSupplySection extends StatefulWidget {
  final String title;
  final String hint;
  final String valueLabel;
  final String valueUnit;
  final bool isRequirement;
  /// Display label → facility_code (web payload uses facility_code).
  final Map<String, String> facilities;
  const GasSupplySection({
    super.key,
    required this.title,
    required this.hint,
    required this.valueLabel,
    required this.valueUnit,
    this.isRequirement = false,
    this.facilities = const {},
  });
  @override
  State<GasSupplySection> createState() => GasSupplySectionState();
}

class GasSupplySectionState extends State<GasSupplySection> {
  final List<PetroleumDynRow> _rows = [];

  List<String> get _labels {
    if (widget.facilities.isNotEmpty) {
      return widget.facilities.keys.toList();
    }
    return kGasStations;
  }

  List<Map<String, dynamic>> collect() {
    final out = <Map<String, dynamic>>[];
    for (final r in _rows) {
      final v = parsePetroleumNum(r.ctrls[0].text);
      if (v == null) continue;
      final label = r.dropVal1 ?? '';
      final code = widget.facilities[label] ?? label;
      if (widget.isRequirement) {
        out.add({
          'facility_code': code,
          'required_mmscf': v,
        });
      } else {
        out.add({
          'facility_code': code,
          'supplied_mmscf': v,
        });
      }
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
    if (_labels.isEmpty) return;
    setState(() => _rows.add(PetroleumDynRow(
          '${DateTime.now().microsecondsSinceEpoch}',
          1,
          dropVal1: _labels.first,
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
        PetroleumSectionTitle(title: widget.title, onAdd: _addRow),
        ..._rows.asMap().entries.map((e) => _buildRow(e.key, e.value)),
        if (_rows.isEmpty) PetroleumEmptyHint(widget.hint),
      ]),
    );
  }

  Widget _buildRow(int i, PetroleumDynRow r) => PetroleumDynCard(
        onRemove: () => _removeRow(i),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
              flex: 3,
              child: PetroleumDropField(
                label: 'المنشأة',
                value: r.dropVal1!,
                items: _labels,
                onChanged: (v) => setState(() => r.dropVal1 = v),
              )),
          SizedBox(width: 8.w),
          Expanded(
              flex: 3,
              child: AppTextField(
                label: '${widget.valueLabel} (${widget.valueUnit})',
                controller: r.ctrls[0],
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
              )),
        ]),
      );
}

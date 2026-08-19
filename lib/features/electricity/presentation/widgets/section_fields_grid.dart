import 'package:flutter/material.dart';
import '../../../../core/widgets/shared_widgets.dart';
import 'models/electricity_field.dart';

/// FIX: replaced GridView (fixed aspectRatio → overflow) with FieldsWrap
/// which uses auto-height 2-column rows.
class SectionFieldsGrid extends StatelessWidget {
  final String title;
  final List<ElectricityField> fields;
  final Map<String, TextEditingController> controllers;

  const SectionFieldsGrid({super.key, required this.title, required this.fields, required this.controllers});

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: title,
      child: FieldsWrap(
        fields: fields.map((f) => AppTextField(
          label: f.label,
          controller: controllers[f.key],
          hint: '0',
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
        )).toList(),
      ),
    );
  }
}

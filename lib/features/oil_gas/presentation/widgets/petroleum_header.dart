import 'package:flutter/material.dart';

import '../../../../core/widgets/shared_widgets.dart';

class PetroleumHeader extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  const PetroleumHeader({
    super.key,
    required this.title,
    required this.subtitle,
    this.icon = Icons.oil_barrel_outlined,
  });

  @override
  Widget build(BuildContext context) {
    return ForestPageHeader(title: title, subtitle: subtitle, icon: icon);
  }
}

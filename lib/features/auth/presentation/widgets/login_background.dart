import 'package:flutter/material.dart';

import '../../../../core/theme/app_theme.dart';

class LoginBackground extends StatelessWidget {
  const LoginBackground({super.key});

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        const ColoredBox(color: Color(0xFFEDE6D8)),
        const DecoratedBox(
          decoration: BoxDecoration(
            image: DecorationImage(
              image: AssetImage('assets/images/bg0_pattern.png'),
              repeat: ImageRepeat.repeat,
              scale: 0.05,
              filterQuality: FilterQuality.medium,
              alignment: Alignment.topLeft,
            ),
          ),
        ),
        DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                AppColors.ink.withValues(alpha: 0.94),
                AppColors.inkDeep.withValues(alpha: 0.91),
                const Color(0xFF08110D).withValues(alpha: 0.95),
              ],
              stops: const [0.0, 0.5, 1.0],
            ),
          ),
        ),
      ],
    );
  }
}

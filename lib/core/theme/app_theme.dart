import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

/// ─── Design Tokens ────────────────────────────────────────────────────────────
/// Palette: Deep Forest Green × Antique Gold
/// Rule: green = structure/authority | gold = accent/highlight only
/// No mixed red-green gradients — each color serves one clear role.
class AppColors {
  // ── Forest (structure) ─────────────────────────────────────────────────────
  static const Color ink       = Color(0xFF0E1A14); // darkest – AppBar, headers
  static const Color inkDeep   = Color(0xFF1A3028); // dark panels
  static const Color inkMid    = Color(0xFF2E4A3C); // mid tones
  static const Color inkSoft   = Color(0xFF5A7A6A); // secondary text, icons
  static const Color inkTint   = Color(0xFFDCEBE4); // light hover states

  // ── Gold (accent only) ────────────────────────────────────────────────────
  static const Color goldDeep  = Color(0xFF8A6F2E); // dark gold text on light bg
  //static const Color goldMid   = Color(0xFFB8942A); // borders, strong accents
  static const Color goldMid   = Color(0xFFBAA97C); // borders, strong accents
  static const Color goldWarm  = Color(0xFFD4AA4A); // primary accent
  static const Color goldLight = Color(0xFFE8D08A); // light accents
  static const Color goldPale  = Color(0xFFF5EBC8); // chip backgrounds
  static const Color goldWash  = Color(0xFFFBF6E8); // input/field backgrounds
  static const Color cream     = Color(0xFFF8F5EE); // page background

  // ── Status ────────────────────────────────────────────────────────────────
  static const Color errorRed  = Color(0xFF9A2020);
  static const Color errorBg   = Color(0xFFFAECEC);
  static const Color successGreen = Color(0xFF1A6B3C);
  static const Color successBg    = Color(0xFFEAF5EF);

  static const Color burgundyDeep  = Color(0xFF3D0E17);
  static const Color burgundy      = Color(0xFF6E1423);
  static const Color burgundyMid   = Color(0xFF8C1F31);
  static const Color burgundyLight = Color(0xFFB9425A);
  static const Color burgundyPale  = Color(0xFFEBD3D7);
  static const Color burgundyWash  = Color(0xFFF8ECEE);

  // ── Semantic aliases (kept for backward compat) ───────────────────────────
  static const Color forest    = ink;
  static const Color forest1   = inkDeep;
  static const Color forest2   = inkMid;
  static const Color golden    = goldWarm;
  static const Color golden1   = goldLight;
  static const Color golden2   = goldPale;
  static const Color golden3   = goldWash;
  static const Color red2      = errorRed;

  // ── UI surfaces ───────────────────────────────────────────────────────────
  static const Color background     = cream;
  static const Color surface        = Color(0xFFFFFFFF);
  static const Color surfaceVariant = goldWash;
  static const Color border         = Color(0x2E8A6F2E); // goldDeep @ 18%
  static const Color borderMid      = Color(0x598A6F2E); // goldDeep @ 35%
  static const Color divider        = Color(0x1A8A6F2E); // goldDeep @ 10%
  static const Color textPrimary    = ink;
  static const Color textSecondary  = inkMid;
  static const Color textHint       = inkSoft;

  // ── Gradients ─────────────────────────────────────────────────────────────
  /// AppBar — single hue, no mixing with gold or red
  static const LinearGradient headerGradient = LinearGradient(
    begin: Alignment.topLeft, end: Alignment.bottomRight,
    colors: [ink, inkDeep, ink],
    stops: [0.0, 0.55, 1.0],
  );

  /// Section/feature header cards — forest depth
  static const LinearGradient cardForestGradient = LinearGradient(
    begin: Alignment.topLeft, end: Alignment.bottomRight,
    colors: [inkDeep, ink],
    stops: [0.0, 1.0],
  );

  /// Save button — from mid to deep green, subtle shift
  static const LinearGradient actionGradient = LinearGradient(
    begin: Alignment.topCenter, end: Alignment.bottomCenter,
    colors: [inkMid, inkDeep],
    stops: [0.0, 1.0],
  );

  /// Gold accent gradient — used ONLY for small chips, avatar, emblem
  static const LinearGradient goldGradient = LinearGradient(
    begin: Alignment.topLeft, end: Alignment.bottomRight,
    colors: [goldMid, goldWarm],
  );

  /// Login splash — deep forest, top to bottom
  static const LinearGradient splashGradient = LinearGradient(
    begin: Alignment.topCenter, end: Alignment.bottomCenter,
    colors: [ink, inkDeep, Color(0xFF122218)],
    stops: [0.0, 0.6, 1.0],
  );

  static const LinearGradient burgundyHeaderGradient = LinearGradient(
    begin: Alignment.topLeft, end: Alignment.bottomRight,
    colors: [burgundyDeep, burgundy, burgundyDeep],
    stops: [0.0, 0.55, 1.0],
  );

  static const LinearGradient burgundyAccentGradient = LinearGradient(
    begin: Alignment.topLeft, end: Alignment.bottomRight,
    colors: [burgundyMid, burgundyLight],
  );

  // legacy aliases
  static const LinearGradient cardMaroonGradient = cardForestGradient;
  static const LinearGradient cardGoldenGradient = goldGradient;
}

/// ─── Theme ────────────────────────────────────────────────────────────────────
class AppTheme {
  static ThemeData get theme => ThemeData(
    useMaterial3: true,
    colorScheme: const ColorScheme.light(
      primary:     AppColors.ink,
      onPrimary:   Colors.white,
      secondary:   AppColors.goldWarm,
      onSecondary: AppColors.ink,
      surface:     AppColors.surface,
      onSurface:   AppColors.textPrimary,
      error:       AppColors.errorRed,
    ),
    scaffoldBackgroundColor: AppColors.background,

    // AppBar
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.transparent,
      foregroundColor: Colors.white,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(
        fontSize: 15.sp, fontWeight: FontWeight.w700,
        color: AppColors.goldWarm, fontFamily: 'Cairo'),
    ),

    // Input
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.goldWash,
      isDense: true,
      contentPadding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 11.h),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8.r),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8.r),
        borderSide: const BorderSide(color: AppColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8.r),
        borderSide: const BorderSide(color: AppColors.goldMid, width: 1.5),
      ),
      hintStyle: TextStyle(
        color: AppColors.inkSoft, fontSize: 12.sp, fontFamily: 'Cairo'),
    ),

    // Elevated button (transparent — real bg set per-widget via DecoratedBox)
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.transparent,
        shadowColor: Colors.transparent,
        foregroundColor: Colors.white,
        minimumSize: Size(double.infinity, 46.h),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10.r)),
        textStyle: TextStyle(
          fontSize: 14.sp, fontWeight: FontWeight.w700, fontFamily: 'Cairo'),
      ),
    ),

    // Card
    cardTheme: CardThemeData(
      color: AppColors.surface,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12.r),
        side: const BorderSide(color: AppColors.border),
      ),
    ),

    // TabBar
    tabBarTheme: TabBarThemeData(
      labelColor: AppColors.ink,
      unselectedLabelColor: AppColors.textHint,
      indicatorColor: AppColors.goldWarm,
      indicatorSize: TabBarIndicatorSize.tab,
      labelStyle: TextStyle(fontWeight: FontWeight.w700, fontSize: 12.sp, fontFamily: 'Cairo'),
      unselectedLabelStyle: TextStyle(fontWeight: FontWeight.w400, fontSize: 12.sp, fontFamily: 'Cairo'),
      dividerColor: Colors.transparent,
    ),

    // Text
    textTheme: TextTheme(
      displayLarge:   TextStyle(fontWeight: FontWeight.w800, fontSize: 28.sp, fontFamily: 'Cairo', color: AppColors.textPrimary),
      headlineLarge:  TextStyle(fontWeight: FontWeight.w700, fontSize: 20.sp, fontFamily: 'Cairo', color: AppColors.textPrimary),
      headlineMedium: TextStyle(fontWeight: FontWeight.w600, fontSize: 17.sp, fontFamily: 'Cairo', color: AppColors.textPrimary),
      titleLarge:     TextStyle(fontWeight: FontWeight.w700, fontSize: 15.sp, fontFamily: 'Cairo', color: AppColors.textPrimary),
      titleMedium:    TextStyle(fontWeight: FontWeight.w600, fontSize: 13.sp, fontFamily: 'Cairo', color: AppColors.textPrimary),
      bodyLarge:      TextStyle(fontWeight: FontWeight.w400, fontSize: 14.sp, fontFamily: 'Cairo', color: AppColors.textPrimary),
      bodyMedium:     TextStyle(fontWeight: FontWeight.w400, fontSize: 13.sp, fontFamily: 'Cairo', color: AppColors.textPrimary),
      bodySmall:      TextStyle(fontWeight: FontWeight.w400, fontSize: 11.sp, fontFamily: 'Cairo', color: AppColors.textSecondary),
      labelLarge:     TextStyle(fontWeight: FontWeight.w600, fontSize: 12.sp, fontFamily: 'Cairo', color: AppColors.textPrimary),
      labelSmall:     TextStyle(fontWeight: FontWeight.w500, fontSize: 10.sp, fontFamily: 'Cairo', color: AppColors.textHint),
    ),

    // CheckBox
    checkboxTheme: CheckboxThemeData(
      fillColor: WidgetStateProperty.resolveWith((s) =>
        s.contains(WidgetState.selected) ? AppColors.inkMid : Colors.transparent),
      checkColor: WidgetStateProperty.all(AppColors.goldWarm),
      side: const BorderSide(color: AppColors.borderMid, width: 1.5),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4.r)),
    ),
  );
}

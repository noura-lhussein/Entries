
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/models/user_model.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../../../core/widgets/app_drawer.dart';
import '../../../../core/utils/sector_registry.dart';
import '../../../auth/presentation/bloc/auth_bloc.dart';
import '../../../home/presentation/screens/home_screen.dart';
import '../../../builder/presentation/screens/info_browse_screen.dart';
import '../../../profile/presentation/screens/profile_screen.dart';

/// ─── Main Shell ─────────────────────────────────────────────────────────────
class MainShell extends StatefulWidget {
  final UserModel? user;
  const MainShell({super.key, this.user});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  late final UserModel _user;
  UserDepartment? _activeSector;
  String _page = 'home';
  DateTime? _lastBackPress;

  @override
  void initState() {
    super.initState();
    final user = widget.user;
    if (user == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) context.go('/login');
      });
      _user = const UserModel(
        id: '',
        name: '',
        email: '',
        department: UserDepartment.admin,
        role: '',
        appRole: AppRole.dataEntry,
        sectors: [],
      );
    } else {
      _user = user;
    }
  }

  void _openSector(UserDepartment sector) {
    setState(() {
      _activeSector = sector;
      _page = 'sector';
    });
  }

  void _goHome() => setState(() {
        _activeSector = null;
        _page = 'home';
      });

  void _openMyData() => setState(() {
        _activeSector = null;
        _page = 'myData';
      });

  void _openEnteredData() => setState(() {
        _activeSector = null;
        _page = 'entered';
      });

  void _openProfile() => setState(() {
        _activeSector = null;
        _page = 'profile';
      });

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<AuthBloc, AuthState>(
      listener: (ctx, s) {
        if (s is AuthUnauthenticated) ctx.go('/login');
      },
      builder: (context, authState) {
        final user = authState is AuthAuthenticated
            ? authState.user.toUserModel()
            : _user;
        return Directionality(
          textDirection: TextDirection.rtl,
          child: PopScope(
            canPop: false,
            onPopInvokedWithResult: (didPop, result) {
              if (didPop) return;
              _handleBackPress(context);
            },
            child: Scaffold(
              drawer: AppDrawer(
                user: user,
                activeSector: _activeSector,
                activePage: _page,
                onSelectSector: _openSector,
                onHome: _goHome,
                onMyData: _openMyData,
                onEnteredData: _openEnteredData,
                onProfile: _openProfile,
                onLogout: () => _confirmLogout(context),
              ),
              appBar: MinistryAppBar(
                user: user,
                onLogout: () => _confirmLogout(context),
                onProfile: _openProfile,
                gradient: AppColors.headerGradient,
              ),
              body: Stack(
                children: [
                  Positioned.fill(
                    child: Image.asset(
                      'assets/images/bg0_s.jpg',
                      fit: BoxFit.cover,
                      scale: 60,
                    ),
                  ),
                  Positioned.fill(
                    child: Container(
                      color: AppColors.cream.withValues(alpha: 0.92),
                    ),
                  ),
                  SafeArea(
                    top: false,
                    child: _buildBody(user),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildBody(UserModel user) {
    switch (_page) {
      case 'myData':
        return KeyedSubtree(
          key: const ValueKey('myData'),
          child: MyDataScreen(
            currentUserId: int.tryParse(user.id),
            canWrite: user.canEnterData || user.isAdmin,
            isAdmin: user.isAdmin,
          ),
        );
      case 'entered':
        return KeyedSubtree(
          key: const ValueKey('entered'),
          child: EnteredDataScreen(
            isAdmin: user.isAdmin,
            canConfirm: user.isAdmin || user.canConfirmInfo,
          ),
        );
      case 'profile':
        return const KeyedSubtree(
          key: ValueKey('profile'),
          child: ProfileScreen(),
        );
      case 'sector':
        if (_activeSector == null) {
          return HomeScreen(user: user, onOpenSector: _openSector);
        }
        return KeyedSubtree(
          key: ValueKey(_activeSector),
          child: buildSectorEntryBody(_activeSector!),
        );
      default:
        return HomeScreen(user: user, onOpenSector: _openSector);
    }
  }

  void _handleBackPress(BuildContext context) {
    if (_page != 'home') {
      _goHome();
      return;
    }

    final now = DateTime.now();
    final isWithinTimeframe = _lastBackPress != null &&
        now.difference(_lastBackPress!) < const Duration(seconds: 2);

    if (isWithinTimeframe) {
      SystemNavigator.pop();
      return;
    }

    _lastBackPress = now;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('اضغط رجوع مرة أخرى للخروج',
            textAlign: TextAlign.center,
            style: TextStyle(fontFamily: 'Cairo', fontSize: 12.sp)),
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
        backgroundColor: AppColors.inkDeep,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10.r)),
        margin: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      ),
    );
  }

  void _confirmLogout(BuildContext ctx) {
    showDialog<void>(
      context: ctx,
      barrierDismissible: false,
      builder: (dialogCtx) => BlocConsumer<AuthBloc, AuthState>(
        listener: (context, state) {
          if (state is AuthUnauthenticated && Navigator.of(dialogCtx).canPop()) {
            Navigator.of(dialogCtx).pop();
          }
        },
        builder: (context, state) {
          final loading = state is AuthLoading;
          return Directionality(
            textDirection: TextDirection.rtl,
            child: AlertDialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14.r),
              ),
              title: Text(
                'تسجيل الخروج',
                style: TextStyle(
                  fontFamily: 'Cairo',
                  fontSize: 16.sp,
                  fontWeight: FontWeight.w700,
                ),
              ),
              content: Text(
                loading
                    ? 'جاري تسجيل الخروج…'
                    : 'هل تريد تسجيل الخروج من التطبيق؟',
                style: TextStyle(fontFamily: 'Cairo', fontSize: 13.sp),
              ),
              actionsPadding: EdgeInsets.all(12.r),
              actions: [
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed:
                            loading ? null : () => Navigator.pop(dialogCtx),
                        style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: AppColors.border),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8.r),
                          ),
                        ),
                        child: Text(
                          'إلغاء',
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ),
                    ),
                    SizedBox(width: 10.w),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: loading
                            ? null
                            : () => context
                                .read<AuthBloc>()
                                .add(const LogoutRequested()),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.ink,
                          foregroundColor: Colors.white,
                          disabledBackgroundColor: AppColors.ink,
                          disabledForegroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8.r),
                          ),
                        ),
                        child: loading
                            ? SizedBox(
                                height: 18.r,
                                width: 18.r,
                                child: const CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : Text(
                                'خروج',
                                style: TextStyle(
                                  fontFamily: 'Cairo',
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

part of 'app_router.dart';

enum RouteTransitions { slideWithFade, fade }

class RouteTransition extends PageRouteBuilder {
  final Widget child;
  final RouteTransitions type;
  final Curve curve;
  final TextDirection textDirection;

  RouteTransition({
    Key? key,
    required this.child,
    required this.type,
    required this.textDirection,
    this.curve = Curves.linear,
  }) : super(
          pageBuilder: (BuildContext context, Animation<double> animation,
              Animation<double> secondaryAnimation) {
            return child;
          },
          maintainState: true,
        );

  @override
  Duration get transitionDuration => const Duration(milliseconds: 300);

  @override
  Duration get reverseTransitionDuration => const Duration(milliseconds: 300);

  @override
  Widget buildTransitions(BuildContext context, Animation<double> animation,
      Animation<double> secondaryAnimation, Widget child) {
    switch (type) {
      case RouteTransitions.slideWithFade:
        Offset offset = textDirection == TextDirection.rtl
            ? const Offset(1.0, 0.0)
            : const Offset(-1.0, 0.0);
        return SlideTransition(
          position: Tween<Offset>(
            begin: offset,
            end: Offset.zero,
          ).animate(animation),
          child: FadeTransition(
            opacity: animation,
            child: SlideTransition(
              position: Tween<Offset>(
                begin: offset,
                end: Offset.zero,
              ).animate(animation),
              child: child,
            ),
          ),
        );

      case RouteTransitions.fade:
        if (Platform.isIOS) {
          return const CupertinoPageTransitionsBuilder().buildTransitions(
              this, context, animation, secondaryAnimation,
              FadeTransition(opacity: animation, child: child));
        }
        return FadeTransition(opacity: animation, child: child);
    }
  }
}

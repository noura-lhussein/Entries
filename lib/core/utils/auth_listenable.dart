import 'dart:async';
import 'package:flutter/material.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';

class AuthListenable extends ChangeNotifier {
  final AuthBloc authBloc;
  late final StreamSubscription _subscription;

  AuthListenable(this.authBloc) {
    // If the bloc already has a determined state, notify immediately
    if (authBloc.state is! AuthInitial) {
      notifyListeners();
    }
    _subscription = authBloc.stream.listen((state) {
      notifyListeners();
    });
  }

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}

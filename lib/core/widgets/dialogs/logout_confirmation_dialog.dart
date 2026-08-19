// import 'package:absher/bloc/authentication_bloc/authentication_event.dart';
// import 'package:absher/core/app_router/app_router.dart';
// import 'package:absher/core/app_router/dialog_transition_builder.dart';
// import 'package:absher/presentation/resources/color_manager.dart';
// import 'package:absher/presentation/screens/auth_screen/account_screen.dart';
// import 'package:absher/translations.dart';
// import 'package:flutter/material.dart';
// import '../../../bloc/authentication_bloc/authertication_bloc.dart';
// import '../../../core/services/services_locator.dart';
// import '../../resources/font_app.dart';
// import '../../resources/style_app.dart';
// import '../custom_button.dart';
// import 'custom_dialog.dart';
//
// class LogoutConfirmationDialog {
//   static Future<bool> handle(BuildContext context) async {
//     dialogTransitionBuilder(context, const _LogoutConfirmationDialog());
//     return false;
//   }
// }
//
// class _LogoutConfirmationDialog extends StatelessWidget {
//   const _LogoutConfirmationDialog({Key? key}) : super(key: key);
//
//   @override
//   Widget build(BuildContext context) {
//     return CustomDialog(
//       icon: Icons.logout,
//       content: Column(
//         children: [
//           Padding(
//             padding: const EdgeInsets.symmetric(
//               horizontal: 8.0,
//               vertical: 60,
//             ),
//             child: Text(
//               AppLocalizations.of(context)!.confimSignOut,
//               style: getBoldStyle(
//                 color: Colors.black,
//                 fontSize: FontSizeApp.s14,
//               ),
//             ),
//           ),
//           Padding(
//             padding: const EdgeInsets.all(16.0),
//             child: Row(
//               children: [
//                 Expanded(
//                   child: CustomButton(
//                     label:AppLocalizations.of(context)!.stay,
//                     fillColor: ColorManager.softYellow,
//                     onTap: () {
//                       AppRouter.pop(context);
//                     },
//                   ),
//                 ),
//                 const SizedBox(
//                   width: 16,
//                 ),
//                 Expanded(
//                   child: CustomButton(
//                     label: AppLocalizations.of(context)!.signOut,
//                     fillColor: Colors.redAccent,
//                     onTap: () {
//                       sl<AuthenticationBloc>().add(LoggedOut());
//                       AppRouter.pushAndRemoveAllStack(context, const AccountScreen());
//                     },
//                   ),
//                 ),
//               ],
//             ),
//           ),
//         ],
//       ),
//     );
//   }
// }

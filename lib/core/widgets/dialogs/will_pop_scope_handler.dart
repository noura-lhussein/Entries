// import 'package:absher/core/app_router/app_router.dart';
// import 'package:absher/core/app_router/dialog_transition_builder.dart';
// import 'package:absher/presentation/resources/color_manager.dart';
// import 'package:flutter/material.dart';
// import 'package:flutter/services.dart';
// import '../../../translations.dart';
// import '../../resources/font_app.dart';
// import '../../resources/style_app.dart';
// import '../custom_button.dart';
// import 'custom_dialog.dart';
//
// class WillPopScopeHandler {
//   static Future<bool> handle(BuildContext context) async {
//     dialogTransitionBuilder(context, const _ExitAppDialog());
//     return false;
//   }

// }
// class _ExitAppDialog extends StatelessWi 0dget {
//   const _ExitAppDialog({Key? key}) : super(key: key);
//
//   @override
//   Widget build(BuildContext context) {
//     return CustomDialog(
//       icon: Icons.exit_to_app_rounded,
//       content: Column(
//         children: [
//           Padding(
//             padding: const EdgeInsets.symmetric(
//               horizontal: 8.0,
//               vertical: 60,
//             ),
//             child: Text(
//               AppLocalizations.of(context)!.sureShutDown,
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
//                     label:AppLocalizations.of(context)!.exit,
//                     fillColor: Colors.redAccent,
//                     onTap: () {
//                       SystemNavigator.pop();
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

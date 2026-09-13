import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../../../core/widgets/shared_widgets.dart';
import '../../data/models/builder_models.dart';
import '../bloc/info_browse_bloc.dart';
import '../bloc/info_browse_event.dart';
import '../bloc/info_browse_state.dart';
import '../utils/filter_defaults.dart';
import 'labeled_select_field.dart';

class InfoFilterPanel extends StatelessWidget {
  const InfoFilterPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<InfoBrowseBloc, InfoBrowseState>(
      buildWhen: (p, c) =>
          p.mainSections != c.mainSections ||
          p.subSections != c.subSections ||
          p.titles != c.titles ||
          p.titleCategories != c.titleCategories ||
          p.attributes != c.attributes ||
          p.users != c.users ||
          p.mainId != c.mainId ||
          p.subId != c.subId ||
          p.titleCategoryId != c.titleCategoryId ||
          p.titleId != c.titleId ||
          p.attributeId != c.attributeId ||
          p.enteredByUserId != c.enteredByUserId ||
          p.confirmed != c.confirmed ||
          p.fromDate != c.fromDate ||
          p.toDate != c.toDate ||
          p.search != c.search ||
          p.showEnteredBy != c.showEnteredBy,
      builder: (context, state) {
        final chips = _chips(state);
        return FormCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      textAlign: TextAlign.start,
                      onChanged: (v) => context
                          .read<InfoBrowseBloc>()
                          .add(InfoBrowseSearchChanged(v)),
                      style: TextStyle(
                        fontFamily: 'Cairo',
                        fontSize: 13.sp,
                        color: AppColors.textPrimary,
                      ),
                      decoration: InputDecoration(
                        hintText: 'بحث العنوان أو القيمة',
                        prefixIcon: Icon(Icons.search, size: 18.r),
                        isDense: true,
                      ),
                    ),
                  ),
                  SizedBox(width: 8.w),
                  Material(
                    color: chips.isEmpty
                        ? AppColors.goldWash
                        : AppColors.goldPale,
                    borderRadius: BorderRadius.circular(8.r),
                    child: InkWell(
                      onTap: () => _openSheet(context),
                      borderRadius: BorderRadius.circular(8.r),
                      child: Padding(
                        padding: EdgeInsets.symmetric(
                          horizontal: 10.w,
                          vertical: 10.h,
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.tune_rounded,
                              size: 18.r,
                              color: AppColors.forest1,
                            ),
                            SizedBox(width: 4.w),
                            Text(
                              'تصفية',
                              style: TextStyle(
                                fontFamily: 'Cairo',
                                fontSize: 12.sp,
                                fontWeight: FontWeight.w700,
                                color: AppColors.forest1,
                              ),
                            ),
                            if (chips.isNotEmpty) ...[
                              SizedBox(width: 6.w),
                              Container(
                                padding: EdgeInsets.symmetric(
                                  horizontal: 6.w,
                                  vertical: 1.h,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.forest1,
                                  borderRadius: BorderRadius.circular(10.r),
                                ),
                                child: Text(
                                  '${chips.length}',
                                  style: TextStyle(
                                    fontFamily: 'Cairo',
                                    fontSize: 10.sp,
                                    fontWeight: FontWeight.w800,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              if (chips.isNotEmpty) ...[
                SizedBox(height: 8.h),
                Wrap(
                  spacing: 6.w,
                  runSpacing: 6.h,
                  alignment: WrapAlignment.start,
                  children: [
                    for (final chip in chips)
                      InputChip(
                        label: Text(
                          '${chip.$2}: ${chip.$3}',
                          style: TextStyle(
                            fontFamily: 'Cairo',
                            fontSize: 11.sp,
                          ),
                        ),
                        onDeleted: () => context
                            .read<InfoBrowseBloc>()
                            .add(InfoBrowseFilterCleared(chip.$1)),
                        deleteIconColor: AppColors.inkSoft,
                        backgroundColor: AppColors.goldWash,
                        side: const BorderSide(color: AppColors.border),
                        visualDensity: VisualDensity.compact,
                      ),
                  ],
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  void _openSheet(BuildContext context) {
    final bloc = context.read<InfoBrowseBloc>();
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16.r)),
      ),
      builder: (ctx) {
        return BlocProvider.value(
          value: bloc,
          child: Padding(
            padding: EdgeInsets.only(
              bottom: MediaQuery.viewInsetsOf(ctx).bottom,
            ),
            child: const SafeArea(child: _FilterSheetBody()),
          ),
        );
      },
    );
  }
}

class _FilterSheetBody extends StatefulWidget {
  const _FilterSheetBody();

  @override
  State<_FilterSheetBody> createState() => _FilterSheetBodyState();
}

class _FilterSheetBodyState extends State<_FilterSheetBody> {
  late int? _mainId;
  late int? _subId;
  late int? _titleCategoryId;
  late int? _titleId;
  late int? _attributeId;
  late int? _enteredByUserId;
  late String? _confirmed;
  late DateTime? _fromDate;
  late DateTime? _toDate;

  @override
  void initState() {
    super.initState();
    final s = context.read<InfoBrowseBloc>().state;
    _mainId = s.mainId;
    _subId = s.subId;
    _titleCategoryId = s.titleCategoryId;
    _titleId = s.titleId;
    _attributeId = s.attributeId;
    _enteredByUserId = s.enteredByUserId;
    _confirmed = s.confirmed;
    _fromDate = s.fromDate;
    _toDate = s.toDate;
  }

  void _clearDraft() {
    setState(() {
      _mainId = null;
      _subId = null;
      _titleCategoryId = null;
      _titleId = null;
      _attributeId = null;
      _enteredByUserId = null;
      _confirmed = null;
      _fromDate = null;
      _toDate = null;
    });
  }

  void _apply() {
    context.read<InfoBrowseBloc>().add(InfoBrowseFiltersApplied(
          mainId: _mainId,
          subId: _subId,
          titleCategoryId: _titleCategoryId,
          titleId: _titleId,
          attributeId: _attributeId,
          enteredByUserId: _enteredByUserId,
          confirmed: _confirmed,
          fromDate: _fromDate,
          toDate: _toDate,
        ));
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<InfoBrowseBloc, InfoBrowseState>(
      buildWhen: (p, c) =>
          p.mainSections != c.mainSections ||
          p.subSections != c.subSections ||
          p.titles != c.titles ||
          p.titleCategories != c.titleCategories ||
          p.attributes != c.attributes ||
          p.users != c.users ||
          p.showEnteredBy != c.showEnteredBy,
      builder: (context, state) {
        final titlesForCategory = _titleCategoryId == null
            ? state.titles
            : state.titles
                .where((t) => t.categoryId == _titleCategoryId)
                .toList();
        return ConstrainedBox(
          constraints: BoxConstraints(
            maxHeight: MediaQuery.sizeOf(context).height * 0.85,
          ),
          child: Padding(
          padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 12.h),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Text(
                    'تصفية',
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 16.sp,
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: _clearDraft,
                    child: const Text('مسح الكل'),
                  ),
                ],
              ),
              SizedBox(height: 8.h),
              Flexible(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      LabeledSelectField(
                        label: 'القسم الرئيسي',
                        hint: 'الكل',
                        clearable: true,
                        value: _mainId?.toString(),
                        options: [
                          for (final m in state.mainSections)
                            BuilderSelectOption(id: m.id, label: m.name),
                        ],
                        onChanged: (v) => setState(
                          () => _mainId = int.tryParse(v ?? ''),
                        ),
                      ),
                      SizedBox(height: 10.h),
                      LabeledSelectField(
                        label: 'القسم الفرعي',
                        hint: 'الكل',
                        clearable: true,
                        value: _subId?.toString(),
                        options: [
                          for (final s in state.subSections)
                            BuilderSelectOption(id: s.id, label: s.name),
                        ],
                        onChanged: (v) => setState(
                          () => _subId = int.tryParse(v ?? ''),
                        ),
                      ),
                      SizedBox(height: 10.h),
                      LabeledSelectField(
                        label: 'فئة المسمى',
                        hint: 'الكل',
                        clearable: true,
                        value: _titleCategoryId?.toString(),
                        options: [
                          for (final c in state.titleCategories)
                            BuilderSelectOption(id: c.id, label: c.name),
                        ],
                        onChanged: (v) {
                          final catId = int.tryParse(v ?? '');
                          final patch = applyTitleCategoryFilterChange(
                            prevTitleId: _titleId,
                            categoryId: catId,
                            titles: state.titles,
                          );
                          setState(() {
                            _titleCategoryId = patch.categoryId;
                            _titleId = patch.titleId;
                          });
                        },
                      ),
                      SizedBox(height: 10.h),
                      LabeledSelectField(
                        label: 'العنوان',
                        hint: 'الكل',
                        clearable: true,
                        value: _titleId?.toString(),
                        options: [
                          for (final t in titlesForCategory)
                            BuilderSelectOption(id: t.id, label: t.name),
                        ],
                        onChanged: (v) => setState(
                          () => _titleId = int.tryParse(v ?? ''),
                        ),
                      ),
                      SizedBox(height: 10.h),
                      LabeledSelectField(
                        label: 'الحقل',
                        hint: 'الكل',
                        clearable: true,
                        value: _attributeId?.toString(),
                        options: [
                          for (final a in state.attributes)
                            BuilderSelectOption(id: a.id, label: a.label),
                        ],
                        onChanged: (v) => setState(
                          () => _attributeId = int.tryParse(v ?? ''),
                        ),
                      ),
                      if (state.showEnteredBy) ...[
                        SizedBox(height: 10.h),
                        LabeledSelectField(
                          label: 'أدخلها',
                          hint: 'الكل',
                          clearable: true,
                          value: _enteredByUserId?.toString(),
                          options: [
                            for (final u in state.users)
                              BuilderSelectOption(id: u.id, label: u.name),
                          ],
                          onChanged: (v) => setState(
                            () => _enteredByUserId = int.tryParse(v ?? ''),
                          ),
                        ),
                      ],
                      SizedBox(height: 10.h),
                      LabeledSelectField(
                        label: 'حالة التأكيد',
                        hint: 'الكل',
                        clearable: true,
                        value: _confirmed,
                        options: const [
                          BuilderSelectOption(
                              id: 1, value: 'waiting', label: 'بانتظار التأكيد'),
                          BuilderSelectOption(
                              id: 2, value: 'accept', label: 'موافق عليه'),
                          BuilderSelectOption(
                              id: 3, value: 'reject', label: 'مرفوض'),
                        ],
                        onChanged: (v) => setState(() => _confirmed = v),
                      ),
                      SizedBox(height: 10.h),
                      Row(
                        children: [
                          Expanded(
                            child: _SheetDateField(
                              label: 'من تاريخ',
                              value: _fromDate,
                              onChanged: (d) => setState(() => _fromDate = d),
                            ),
                          ),
                          SizedBox(width: 10.w),
                          Expanded(
                            child: _SheetDateField(
                              label: 'إلى تاريخ',
                              value: _toDate,
                              onChanged: (d) => setState(() => _toDate = d),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              SizedBox(height: 14.h),
              Row(
                children: [
                  Expanded(
                    child: FilledButton(
                      onPressed: _apply,
                      child: Text(
                        'تطبيق',
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 13.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                  SizedBox(width: 8.w),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      child: Text(
                        'إلغاء',
                        style: TextStyle(
                          fontFamily: 'Cairo',
                          fontSize: 13.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        );
      },
    );
  }
}

class _SheetDateField extends StatelessWidget {
  final String label;
  final DateTime? value;
  final ValueChanged<DateTime?> onChanged;
  const _SheetDateField({
    required this.label,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          label,
          textAlign: TextAlign.start,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 11.sp,
            fontWeight: FontWeight.w600,
            color: AppColors.textHint,
          ),
        ),
        SizedBox(height: 5.h),
        Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: () async {
              final picked = await showDatePicker(
                context: context,
                initialDate: value ?? DateTime.now(),
                firstDate: DateTime(1970),
                lastDate: DateTime(2099),
                locale: const Locale('ar'),
              );
              if (picked != null) onChanged(picked);
            },
            borderRadius: BorderRadius.circular(8.r),
            child: Container(
              padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 10.h),
              decoration: BoxDecoration(
                color: AppColors.goldWash,
                borderRadius: BorderRadius.circular(8.r),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  Text(
                    value == null ? '—' : displayDate(value!),
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w600,
                      color: value == null
                          ? AppColors.textHint
                          : AppColors.textPrimary,
                    ),
                  ),
                  const Spacer(),
                  if (value != null)
                    GestureDetector(
                      onTap: () => onChanged(null),
                      child: Icon(Icons.close_rounded, size: 16.r),
                    ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

List<(String, String, String)> _chips(InfoBrowseState state) {
  String nameOf(List<BuilderNamedItem> items, int? id) {
    if (id == null) return '';
    for (final i in items) {
      if (i.id == id) return i.name;
    }
    return '$id';
  }

  String titleName(int? id) {
    if (id == null) return '';
    for (final t in state.titles) {
      if (t.id == id) return t.name;
    }
    return '$id';
  }

  String attrName(int? id) {
    if (id == null) return '';
    for (final a in state.attributes) {
      if (a.id == id) return a.label;
    }
    return '$id';
  }

  String subName(int? id) {
    if (id == null) return '';
    for (final s in state.subSections) {
      if (s.id == id) return s.name;
    }
    return '$id';
  }

  const confirmedLabel = {
    'waiting': 'بانتظار التأكيد',
    'accept': 'موافق عليه',
    'reject': 'مرفوض',
  };

  final chips = <(String, String, String)>[];
  if (state.mainId != null) {
    chips.add((
      'main_section_id',
      'القسم الرئيسي',
      nameOf(state.mainSections, state.mainId),
    ));
  }
  if (state.subId != null) {
    chips.add(('sub_main_id', 'القسم الفرعي', subName(state.subId)));
  }
  if (state.titleCategoryId != null) {
    chips.add((
      'title_category_id',
      'فئة المسمى',
      nameOf(state.titleCategories, state.titleCategoryId),
    ));
  }
  if (state.titleId != null) {
    chips.add(('title_id', 'العنوان', titleName(state.titleId)));
  }
  if (state.attributeId != null) {
    chips.add(('attribute_id', 'الحقل', attrName(state.attributeId)));
  }
  if (state.showEnteredBy && state.enteredByUserId != null) {
    chips.add(('user', 'أدخلها', nameOf(state.users, state.enteredByUserId)));
  }
  if (state.confirmed != null && state.confirmed!.isNotEmpty) {
    chips.add((
      'confirmed',
      'حالة التأكيد',
      confirmedLabel[state.confirmed] ?? state.confirmed!,
    ));
  }
  if (state.fromDate != null) {
    chips.add(('from', 'من تاريخ', displayDate(state.fromDate!)));
  }
  if (state.toDate != null) {
    chips.add(('to', 'إلى تاريخ', displayDate(state.toDate!)));
  }
  return chips;
}

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../../core/theme/app_theme.dart';
import '../../data/models/builder_models.dart';
class _TreeNode {
  final BuilderSubSection section;
  final String code;
  final List<_TreeNode> children;
  const _TreeNode({
    required this.section,
    required this.code,
    required this.children,
  });
}

List<_TreeNode> buildSubSectionTree(List<BuilderSubSection> sections) {
  if (sections.isEmpty) return const [];
  final ids = <int>{};
  for (final s in sections) {
    ids.add(s.id);
  }
  final byParent = <int?, List<BuilderSubSection>>{};
  for (final s in sections) {
    final parent =
        s.parentId != null && ids.contains(s.parentId) ? s.parentId : null;
    byParent.putIfAbsent(parent, () => []).add(s);
  }

  List<_TreeNode> walk(int? parentId, String prefix) {
    final rows = byParent[parentId] ?? const <BuilderSubSection>[];
    final nodes = <_TreeNode>[];
    for (var i = 0; i < rows.length; i++) {
      final s = rows[i];
      final code = prefix.isEmpty ? '${i + 1}' : '$prefix.${i + 1}';
      nodes.add(
        _TreeNode(
          section: s,
          code: code,
          children: walk(s.id, code),
        ),
      );
    }
    return nodes;
  }

  return walk(null, '');
}

class SubSectionTreePicker extends StatefulWidget {
  final List<BuilderSubSection> sections;
  final int? selectedId;
  final ValueChanged<int?> onSelected;
  final bool leavesOnly;
  final bool showAllOption;
  final double maxHeight;

  const SubSectionTreePicker({
    super.key,
    required this.sections,
    required this.selectedId,
    required this.onSelected,
    this.leavesOnly = false,
    this.showAllOption = false,
    this.maxHeight = 280,
  });

  @override
  State<SubSectionTreePicker> createState() => _SubSectionTreePickerState();
}

class _SubSectionTreePickerState extends State<SubSectionTreePicker> {
  final Set<int> _expanded = {};

  @override
  void initState() {
    super.initState();
    _syncExpanded();
  }

  @override
  void didUpdateWidget(covariant SubSectionTreePicker oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.sections != widget.sections ||
        oldWidget.selectedId != widget.selectedId) {
      _syncExpanded();
    }
  }

  void _syncExpanded() {
    final tree = buildSubSectionTree(widget.sections);
    final selected = widget.selectedId;
    void mark(List<_TreeNode> nodes, List<int> ancestors) {
      for (final n in nodes) {
        if (selected != null && n.section.id == selected) {
          _expanded.addAll(ancestors);
        }
        if (n.children.isNotEmpty) {
          mark(n.children, [...ancestors, n.section.id]);
        }
      }
    }

    mark(tree, const []);
    if (_expanded.isEmpty) {
      for (final n in tree) {
        if (n.children.isNotEmpty) _expanded.add(n.section.id);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final tree = buildSubSectionTree(widget.sections);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'القسم الفرعي',
          textAlign: TextAlign.start,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 11.sp,
            fontWeight: FontWeight.w600,
            color: AppColors.textHint,
          ),
        ),
        SizedBox(height: 5.h),
        Container(
          constraints: BoxConstraints(maxHeight: widget.maxHeight.h),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(10.r),
            border: Border.all(color: AppColors.border),
          ),
          child: ListView(
            padding: EdgeInsets.symmetric(vertical: 4.h),
            shrinkWrap: true,
            children: [
              if (widget.showAllOption) _allRow(),
              if (tree.isEmpty)
                Padding(
                  padding: EdgeInsets.symmetric(vertical: 16.h),
                  child: Text(
                    'لا توجد أقسام فرعية',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontFamily: 'Cairo',
                      fontSize: 12.sp,
                      color: AppColors.textHint,
                    ),
                  ),
                )
              else
                for (final node in tree) ..._rows(node, 0),
            ],
          ),
        ),
      ],
    );
  }

  Widget _allRow() {
    final selected = widget.selectedId == null;
    return InkWell(
      onTap: () => widget.onSelected(null),
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 8.h),
        child: Text(
          'الكل',
          textAlign: TextAlign.start,
          style: TextStyle(
            fontFamily: 'Cairo',
            fontSize: 13.sp,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            color: selected ? AppColors.forest1 : AppColors.textPrimary,
          ),
        ),
      ),
    );
  }

  List<Widget> _rows(_TreeNode node, int depth) {
    final hasChildren = node.children.isNotEmpty;
    final expanded = _expanded.contains(node.section.id);
    final selected = widget.selectedId == node.section.id;
        final selectable =
            !widget.leavesOnly || (!hasChildren && !node.section.isBranch);
    return [
      InkWell(
        onTap: () {
          if (hasChildren) {
            setState(() {
              if (expanded) {
                _expanded.remove(node.section.id);
              } else {
                _expanded.add(node.section.id);
              }
            });
          }
          if (selectable) widget.onSelected(node.section.id);
        },
        child: Padding(
          padding: EdgeInsets.fromLTRB(
            8.w,
            7.h,
            8.w + depth * 14.w,
            7.h,
          ),
          child: Row(
            children: [
              if (hasChildren)
                Icon(
                  expanded
                      ? Icons.expand_more_rounded
                      : Icons.chevron_left_rounded,
                  size: 18.r,
                  color: AppColors.inkSoft,
                )
              else
                SizedBox(width: 18.r),
              SizedBox(width: 4.w),
              _codeBadge(node.code),
              if (hasChildren) ...[
                SizedBox(width: 6.w),
                _branchBadge(node.children.length),
              ],
              SizedBox(width: 8.w),
              Expanded(
                child: Text(
                  node.section.name,
                  textAlign: TextAlign.start,
                  style: TextStyle(
                    fontFamily: 'Cairo',
                    fontSize: 13.sp,
                    fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
                    color: selected ? AppColors.forest1 : AppColors.textSecondary,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
      if (hasChildren && expanded)
        for (final child in node.children) ..._rows(child, depth + 1),
    ];
  }

  Widget _codeBadge(String code) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 7.w, vertical: 2.h),
      decoration: BoxDecoration(
        color: AppColors.cream,
        borderRadius: BorderRadius.circular(8.r),
        border: Border.all(color: AppColors.border),
      ),
      child: Text(
        code,
        style: TextStyle(
          fontFamily: 'Cairo',
          fontSize: 10.sp,
          fontWeight: FontWeight.w700,
          color: AppColors.inkSoft,
        ),
      ),
    );
  }

  Widget _branchBadge(int count) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 7.w, vertical: 2.h),
      decoration: BoxDecoration(
        color: AppColors.successBg,
        borderRadius: BorderRadius.circular(8.r),
      ),
      child: Text(
        '$count فرع',
        style: TextStyle(
          fontFamily: 'Cairo',
          fontSize: 10.sp,
          fontWeight: FontWeight.w700,
          color: AppColors.successGreen,
        ),
      ),
    );
  }
}

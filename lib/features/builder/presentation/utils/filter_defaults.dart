import '../../data/models/builder_models.dart';

T? soleItem<T>(List<T> items) => items.length == 1 ? items.first : null;

List<BuilderTitle> titlesForCategory(
  List<BuilderTitle> titles,
  int? categoryId,
) {
  if (categoryId == null) return titles;
  return titles.where((t) => t.categoryId == categoryId).toList();
}

/// Web `applyTitleCategoryFilterChange`: keep title if still allowed, else sole title.
({int? categoryId, int? titleId}) applyTitleCategoryFilterChange({
  required int? prevTitleId,
  required int? categoryId,
  required List<BuilderTitle> titles,
}) {
  final allowed = titlesForCategory(titles, categoryId);
  var titleId = prevTitleId;
  if (categoryId != null &&
      titleId != null &&
      !allowed.any((t) => t.id == titleId)) {
    titleId = null;
  }
  titleId ??= soleItem(allowed)?.id;
  return (categoryId: categoryId, titleId: titleId);
}

String? isoDate(DateTime? date) {
  if (date == null) return null;
  final m = date.month.toString().padLeft(2, '0');
  final d = date.day.toString().padLeft(2, '0');
  return '${date.year}-$m-$d';
}

String displayDate(DateTime date) {
  final d = date.day.toString().padLeft(2, '0');
  final m = date.month.toString().padLeft(2, '0');
  return '$d/$m/${date.year}';
}

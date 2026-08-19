/// A single labeled numeric field in one of the electricity report sections.
class ElectricityField {
  final String label;
  final String key;
  final String unit;
  const ElectricityField(this.label, this.key, [this.unit = '']);
}

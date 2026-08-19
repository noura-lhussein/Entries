/// Matches moe-portal [ORE_PRODUCT_OPTIONS].
class OreProductOption {
  final String nameAr;
  final String nameEn;
  const OreProductOption(this.nameAr, this.nameEn);
}

const List<OreProductOption> kOreProductOptions = [
  OreProductOption('الجص', 'Gypsum'),
  OreProductOption('رمال كوارتزية', 'Quartz sand'),
  OreProductOption('ملح', 'Salt'),
  OreProductOption('الاسمنت', 'Cement'),
  OreProductOption('دولوميت', 'Dolomite'),
  OreProductOption('غضار', 'Clay'),
  OreProductOption('سجيل زيتي', 'Oil shale'),
  OreProductOption('حديد', 'Iron'),
  OreProductOption('رخام', 'Marble'),
  OreProductOption('سكوريا', 'Scoria'),
  OreProductOption('حجر جيري', 'Limestone'),
  OreProductOption('اسفلت', 'Asphalt'),
  OreProductOption('فوسفات', 'Phosphate'),
  OreProductOption('بازلت', 'Basalt'),
  OreProductOption('بنتونيت', 'Bentonite'),
  OreProductOption('تراكيت', 'Trachyte'),
  OreProductOption('زيوليت', 'Zeolite'),
  OreProductOption('تريبولي', 'Tripoli'),
  OreProductOption('تورب', 'Peat'),
  OreProductOption('سيانيت نيفيليني', 'Nepheline syenite'),
];

const List<String> kProductionTypeOptions = ['ذاتي', 'معهّد'];
const List<String> kOreUnitOptions = ['طن', 'م3'];

OreProductOption? findOreProduct(String nameAr) {
  final key = nameAr.trim();
  if (key.isEmpty) return null;
  for (final opt in kOreProductOptions) {
    if (opt.nameAr == key) return opt;
  }
  return null;
}

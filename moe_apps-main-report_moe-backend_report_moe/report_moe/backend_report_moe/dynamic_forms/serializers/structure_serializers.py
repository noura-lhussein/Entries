from rest_framework import serializers

from ..models import Attribute, MainSection, Option, SubMainSection, Title, TitleCategory


class TitleCategorySerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(min_value=1)

    class Meta:
        model = TitleCategory
        fields = ("id", "name", "order")

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("اسم الفئة مطلوب.")
        name = value.strip()
        existing = TitleCategory.objects.filter(name=name)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError("فئة بهذا الاسم موجودة بالفعل.")
        return name


class TitleSerializer(serializers.ModelSerializer):
    supports_excel = serializers.SerializerMethodField()
    order = serializers.IntegerField(min_value=1)
    category = serializers.PrimaryKeyRelatedField(
        queryset=TitleCategory.objects.all(),
        allow_null=True,
        required=False,
    )
    category_name = serializers.CharField(
        source="category.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Title
        fields = (
            "id",
            "name",
            "code",
            "is_system",
            "order",
            "supports_excel",
            "category",
            "category_name",
            "subtitle",
            "entry_mode",
            "field_groups",
            "preview_field_keys",
        )
        read_only_fields = ("is_system",)

    def get_supports_excel(self, obj) -> bool:
        from ..title_excel_registry import supports_title

        return supports_title(obj.name)

    def validate_order(self, value):
        if isinstance(value, bool):
            raise serializers.ValidationError(
                "الترتيب يجب أن يكون عدداً صحيحاً أكبر من صفر")
        try:
            n = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                "الترتيب يجب أن يكون عدداً صحيحاً أكبر من صفر") from None
        if n < 1:
            raise serializers.ValidationError(
                "الترتيب يجب أن يكون أكبر من صفر")
        if isinstance(value, float) and value != n:
            raise serializers.ValidationError(
                "الترتيب يجب أن يكون عدداً صحيحاً بدون فواصل")
        return n

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "اسم المسمى مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    def validate(self, data):
        name = data.get('name')
        if name:
            existing = Title.objects.filter(name=name, deleted=False)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    "مسمى بهذا الاسم موجود بالفعل")
        if (
            self.instance
            and self.instance.is_system
            and 'code' in data
            and data['code'] != self.instance.code
        ):
            raise serializers.ValidationError(
                {"code": "لا يمكن تغيير الرمز التقني لمسمى نظامي — يعتمد عليه moeds."}
            )
        return data


class MainSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainSection
        fields = ("id", "name")

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "اسم القسم الرئيسي مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    def validate(self, data):
        name = data.get('name')
        if name:
            existing = MainSection.objects.filter(name=name, deleted=False)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    "قسم رئيسي بهذا الاسم موجود بالفعل")
        return data


class SubMainSectionSerializer(serializers.ModelSerializer):
    main_section_name = serializers.CharField(
        source="main_section.name", read_only=True)
    parent_name = serializers.CharField(
        source="parent.name", read_only=True, allow_null=True)
    is_leaf = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    district_name = serializers.CharField(
        source="location_district.name_ar", read_only=True, allow_null=True)
    governorate_name = serializers.CharField(
        source="location_district.governorate.name_ar",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = SubMainSection
        fields = (
            "id",
            "name",
            "main_section",
            "main_section_name",
            "parent",
            "parent_name",
            "is_leaf",
            "children_count",
            "location_district",
            "district_name",
            "governorate_name",
        )

    def get_is_leaf(self, obj) -> bool:
        count = getattr(obj, "children_count", None)
        if count is not None:
            return int(count) == 0
        return obj.is_leaf

    def get_children_count(self, obj) -> int:
        count = getattr(obj, "children_count", None)
        if count is not None:
            return int(count)
        return obj.children.filter(deleted=False).count()

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "اسم القسم الفرعي مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    def validate_main_section(self, value):
        if not value:
            raise serializers.ValidationError("القسم الرئيسي مطلوب")
        return value

    def validate(self, data):
        name = data.get('name', getattr(self.instance, 'name', None))
        main_section = data.get(
            'main_section', getattr(self.instance, 'main_section', None))
        if 'parent' in data:
            parent = data.get('parent')
        elif self.instance is not None:
            parent = self.instance.parent
        else:
            parent = None

        if parent is not None:
            if self.instance and parent.pk == self.instance.pk:
                raise serializers.ValidationError(
                    {"parent": "لا يمكن أن يكون القسم الفرعي أباً لنفسه."})
            if main_section and parent.main_section_id != main_section.id:
                raise serializers.ValidationError(
                    {"parent": "الأب يجب أن يكون ضمن نفس القسم الرئيسي."})
            node = parent
            seen: set[int] = set()
            while node is not None:
                if self.instance and node.pk == self.instance.pk:
                    raise serializers.ValidationError(
                        {"parent": "لا يمكن إنشاء حلقة في شجرة الأقسام."})
                if node.pk in seen:
                    break
                seen.add(node.pk)
                node = node.parent

        if name and main_section:
            existing = SubMainSection.objects.filter(
                name=name, main_section=main_section, deleted=False
            )
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    f"قسم فرعي باسم '{name}' موجود بالفعل في هذا القسم الرئيسي"
                )
        return data

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ("id", "label", "attribute")

    def validate_label(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("اسم الخيار مطلوب")
        return value.strip()

    def validate_attribute(self, value):
        if not value:
            raise serializers.ValidationError("الحقل (Attribute) مطلوب")
        if value.type != 'select':
            raise serializers.ValidationError(
                f"لا يمكن إضافة خيارات لحقل من نوع '{value.get_type_display()}'. فقط حقول 'select' تدعم الخيارات."
            )
        return value

    def validate(self, data):
        attribute = data.get('attribute')
        label = data.get('label')

        if attribute and label:
            existing = Option.objects.filter(attribute=attribute, label=label)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise serializers.ValidationError(
                    f"خيار باسم '{label}' موجود بالفعل في هذا الحقل"
                )

        return data


class AttributeSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True, read_only=True)
    title_name = serializers.CharField(
        source="title.name", read_only=True, allow_null=True)

    class Meta:
        model = Attribute
        fields = (
            "id",
            "label",
            "type",
            "required",
            "title",
            "title_name",
            "options",
            "key",
            "order",
            "group",
            "unit_ar",
            "help_ar",
            "readonly",
            "computed_from",
            "min_value",
            "max_value",
            "max_field",
            "warn_if_gt_field",
            "message_ar",
            "decimals",
            "is_measure",
            "measure_order",
            "label_en",
            "unit_en",
            "measure_status_rule",
            "is_system",
        )
        read_only_fields = ("is_system",)

    def to_representation(self, instance):
        from ..form_schema import attribute_display_label

        data = super().to_representation(instance)
        data["label"] = attribute_display_label(instance)
        return data

    def validate_label(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "اسم الحقل مطلوب ولا يمكن أن يكون فارغاً")
        return value.strip()

    def validate_type(self, value):
        from ..entity_registry import ALL_ENTITY_TYPES

        valid_types = [
            'text', 'textarea', 'number', 'date',
            'boolean', 'select', 'city', 'district',
            'sub_district', 'community', 'image', 'file',
            *ALL_ENTITY_TYPES,
        ]
        if value not in valid_types:
            raise serializers.ValidationError(
                f"نوع البيانات غير صحيح. يجب أن يكون من: {', '.join(valid_types)}")
        return value
    def validate_title(self, value):
        if not value:
            raise serializers.ValidationError("المسمى (Title) مطلوب")
        return value

    def validate(self, data):
        title = data.get('title')
        label = data.get('label')

        if title and label:
            existing = Attribute.objects.filter(title=title, label=label)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise serializers.ValidationError(
                    f"حقل باسم '{label}' موجود بالفعل في هذا المسمى"
                )

        if (
            self.instance
            and self.instance.is_system
            and 'key' in data
            and data['key'] != self.instance.key
        ):
            raise serializers.ValidationError(
                {"key": "لا يمكن تغيير المفتاح التقني لحقل نظامي — يعتمد عليه moeds."}
            )

        return data

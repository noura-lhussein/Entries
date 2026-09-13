from rest_framework import serializers

from ..models import ReqReport, ReqReportTitle


class ReqReportTitleSerializer(serializers.ModelSerializer):
    title_name = serializers.CharField(source="title.name", read_only=True)

    class Meta:
        model = ReqReportTitle
        fields = ("id", "title", "title_name")


class ReqReportSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source="user.email", read_only=True, allow_null=True)
    sub_main_name = serializers.SerializerMethodField()
    report_titles = ReqReportTitleSerializer(many=True, read_only=True)

    class Meta:
        model = ReqReport
        fields = (
            "id", "req_report_sub_main", "sub_main_name",
            "user", "user_name", "date_from", "date_to", "report_titles",
        )

    def get_sub_main_name(self, obj):
        try:
            return obj.req_report_sub_main.sub_main.name
        except Exception:
            return None

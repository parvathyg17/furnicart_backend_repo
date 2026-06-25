from django.http import HttpResponse
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.utils.permissions import IsAdminUserCustom
from orders.services.dashboard_analytics_services import (
    build_dashboard_analytics,
)
from orders.services.sales_report_export import (
    build_ledger_excel,
    build_ledger_pdf,
)


def _build_ledger_export_response(
    request,
):

    from orders.views.admin_sales_report_views import (
        _load_report_for_export,
    )

    report_data = _load_report_for_export(
        request,
    )

    export_format = (
        request.query_params.get(
            "export_format",
            "excel",
        )
        or "excel"
    ).lower()

    if export_format == "pdf":

        pdf_bytes = build_ledger_pdf(
            report_data,
        )

        filename = (
            f"FurniCart-ledger-"
            f"{report_data['date_from']}-"
            f"{report_data['date_to']}.pdf"
        )

        response = HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
        )

    elif export_format in (
        "excel",
        "xlsx",
    ):

        xlsx_bytes = build_ledger_excel(
            report_data,
        )

        filename = (
            f"FurniCart-ledger-"
            f"{report_data['date_from']}-"
            f"{report_data['date_to']}.xlsx"
        )

        response = HttpResponse(
            xlsx_bytes,
            content_type=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
        )

    else:

        raise ValidationError(
            {
                "export_format": (
                    "Supported formats: pdf, excel."
                ),
            },
        )

    response[
        "Content-Disposition"
    ] = f'attachment; filename="{filename}"'

    return response


class AdminDashboardAnalyticsView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
    ):

        if (
            request.query_params.get(
                "export",
            )
            == "ledger"
        ):

            return _build_ledger_export_response(
                request,
            )

        chart_period = (
            request.query_params.get(
                "chart_period",
                "monthly",
            )
            or "monthly"
        )

        data = build_dashboard_analytics(
            chart_period=chart_period,
        )

        return Response(
            data,
        )


class AdminLedgerExportView(
    APIView,
):

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
    ):

        return _build_ledger_export_response(
            request,
        )

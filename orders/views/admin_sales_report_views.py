from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import CustomPagination
from core.utils.permissions import IsAdminUserCustom
from orders.services.sales_report_export import (
    build_sales_report_excel,
    build_sales_report_pdf,
)
from orders.services.sales_report_services import (
    build_sales_report_for_export,
    build_sales_report_payload,
    serialize_sales_report_order,
)


def _load_report_for_export(
    request,
):

    period = (
        request.query_params.get(
            "period",
            "weekly",
        )
        or "weekly"
    )

    date_from = request.query_params.get(
        "date_from",
    )

    date_to = request.query_params.get(
        "date_to",
    )

    try:

        return build_sales_report_for_export(
            period=period,
            date_from_raw=date_from,
            date_to_raw=date_to,
        )

    except ValueError as exc:

        raise ValidationError(
            {
                "detail": str(
                    exc,
                ),
            },
        ) from exc


def _build_sales_export_response(
    request,
):

    report_data = _load_report_for_export(
        request,
    )

    export_format = (
        request.query_params.get(
            "export_format",
            "pdf",
        )
        or "pdf"
    ).lower()

    if export_format == "pdf":

        pdf_bytes = build_sales_report_pdf(
            report_data,
        )

        filename = (
            f"FurniCart-sales-report-"
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

        xlsx_bytes = build_sales_report_excel(
            report_data,
        )

        filename = (
            f"FurniCart-sales-report-"
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


def _requested_export_format(
    request,
):

    export_format = (
        request.query_params.get(
            "export_format",
        )
        or ""
    ).lower()

    if export_format in (
        "pdf",
        "excel",
        "xlsx",
    ):

        return export_format

    return None


class AdminSalesReportView(
    APIView,
):

    """
    GET /api/admin/reports/sales/

    Query params:
      - period: daily | weekly | yearly | custom (default weekly)
      - date_from, date_to: YYYY-MM-DD (required when period=custom)
      - page, page_size: paginate orders in the report window
      - export_format: pdf | excel (returns file download instead of JSON)
    """

    permission_classes = [
        IsAuthenticated,
        IsAdminUserCustom,
    ]

    def get(
        self,
        request,
    ):

        if _requested_export_format(
            request,
        ):

            return _build_sales_export_response(
                request,
            )

        period = (
            request.query_params.get(
                "period",
                "weekly",
            )
            or "weekly"
        )

        date_from = request.query_params.get(
            "date_from",
        )

        date_to = request.query_params.get(
            "date_to",
        )

        try:

            payload = build_sales_report_payload(
                period=period,
                date_from_raw=date_from,
                date_to_raw=date_to,
            )

        except ValueError as exc:

            raise ValidationError(
                {
                    "detail": str(
                        exc,
                    ),
                },
            ) from exc

        orders_qs = payload.pop(
            "orders_queryset",
        )

        paginator = CustomPagination()

        page = paginator.paginate_queryset(
            orders_qs,
            request,
            view=self,
        )

        if page is not None:

            orders_data = [
                serialize_sales_report_order(
                    order,
                )
                for order in page
            ]

            response = paginator.get_paginated_response(
                orders_data,
            )

            body = response.data

            body["period"] = payload[
                "period"
            ]

            body["date_from"] = payload[
                "date_from"
            ]

            body["date_to"] = payload[
                "date_to"
            ]

            body["breakdown_granularity"] = payload[
                "breakdown_granularity"
            ]

            body["summary"] = payload[
                "summary"
            ]

            body["breakdown"] = payload[
                "breakdown"
            ]

            return Response(
                body,
            )

        orders_data = [
            serialize_sales_report_order(
                order,
            )
            for order in orders_qs
        ]

        return Response(
            {
                **payload,
                "orders": orders_data,
            },
            status=status.HTTP_200_OK,
        )


class AdminSalesReportExportView(
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

        return _build_sales_export_response(
            request,
        )

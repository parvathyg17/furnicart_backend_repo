from django.urls import path

from orders.views.admin_dashboard_views import (
    AdminLedgerExportView,
)
from orders.views.admin_sales_report_views import (
    AdminSalesReportExportView,
    AdminSalesReportView,
)

urlpatterns = [

    path(
        "sales/export/",
        AdminSalesReportExportView.as_view(),
    ),

    path(
        "ledger/export/",
        AdminLedgerExportView.as_view(),
    ),

    path(
        "sales/",
        AdminSalesReportView.as_view(),
    ),

]

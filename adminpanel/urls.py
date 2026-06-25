from django.urls import include, path



from .views import AdminDashboardStatsView, AdminLoginView, AdminLogoutView, AdminMeView, BlockUserView, UserListView
from orders.views.admin_dashboard_views import AdminDashboardAnalyticsView, AdminLedgerExportView
from orders.views.admin_sales_report_views import AdminSalesReportExportView

urlpatterns = [
    path('login/', AdminLoginView.as_view()),
    path('users/', UserListView.as_view()),
    path('users/<int:user_id>/block/', BlockUserView.as_view()),
    path('logout/', AdminLogoutView.as_view()),
    path("me/", AdminMeView.as_view()),
    path("dashboard-stats/",AdminDashboardStatsView.as_view()),
    path(
        "dashboard/analytics/",
        AdminDashboardAnalyticsView.as_view(),
    ),
    path(
        "reports/sales/export/",
        AdminSalesReportExportView.as_view(),
    ),
    path(
        "reports/ledger/export/",
        AdminLedgerExportView.as_view(),
    ),
    path(
        "reports/",
        include(
            "orders.admin_report_urls",
        ),
    ),
]


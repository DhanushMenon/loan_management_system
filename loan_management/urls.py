from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger API schema view
schema_view = get_schema_view(
    openapi.Info(
        title="My API",
        default_version="v1",
        description="API documentation for the Loan Management System",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@myapi.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
)

# URL patterns
urlpatterns = [
    path("admin/", admin.site.urls),  # Django admin panel
    path("api/", include("loans.urls")),  # Include loan-related URLs
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),  # Swagger UI
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),  # ReDoc UI (optional)
]

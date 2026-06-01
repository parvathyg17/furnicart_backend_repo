from django.contrib import admin


from catalog.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "name",
        "parent",
        "is_active",
        "created_at",
    ]

    search_fields = [
        "name",
    ]

    list_filter = [
        "is_active",
    ]

    prepopulated_fields = {
        "slug": ("name",)
    }
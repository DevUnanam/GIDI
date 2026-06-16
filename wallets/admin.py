from django.contrib import admin

from .models import Transaction, Wallet


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "currency", "is_active", "updated_at")
    list_filter = ("currency", "is_active")
    search_fields = ("user__email", "user__username")
    autocomplete_fields = ("user",)
    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("reference", "wallet", "transaction_type", "status", "amount", "created_at")
    list_filter = ("transaction_type", "status", "created_at")
    search_fields = ("reference", "wallet__user__email", "description")
    autocomplete_fields = ("wallet", "shipment")

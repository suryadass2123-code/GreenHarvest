
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Products app
    path('', include('products.urls')),

    # Accounts app
    path('', include('accounts.urls')),

    # Orders app
    path('', include('orders.urls')),

    # Payments app
    path('', include('payments.urls')),

    # Reviews app
    path('', include('reviews.urls')),

    # Dashboard app
    path('', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

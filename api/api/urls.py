from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

from core.views import FileUploadView

from .routers import router
from .docs import schema_view


# Prefix to be used on all v1 API urls
v1_prefix = 'v1/'


def v1_url(url):
    # Prepend a url string with the v1 prefix.
    return v1_prefix + url


urlpatterns = ([
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='admin/')),

    # API urls
    path(v1_url('upload/'), FileUploadView.as_view(), name='upload'),
    path(v1_url('docs/'), schema_view.with_ui('redoc', cache_timeout=0),
         name='api-docs'),
    path(f'{v1_prefix}auth/', include('authentication.urls')),
    path(f'{v1_prefix}', include('accounts.urls')),
    # path(v1_prefix, include(router.urls)),
]
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

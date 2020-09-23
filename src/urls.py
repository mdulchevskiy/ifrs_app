from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from ifrs.funcs import (remove_chunk,
                        sync_databases, )
from ifrs.views import (home_page,
                        ifrs_page,
                        rcp_page, )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_page, name='home_page'),
    path('ifrs', ifrs_page, name='ifrs_page'),
    path('<str:rcp_name>', rcp_page, name='rcp_page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

remove_chunk()
sync_databases()

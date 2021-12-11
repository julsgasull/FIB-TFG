from django.conf import settings
from django.conf.urls import url
from django.urls import include, path
from .views import login, launch, upload, consult, get_jwks

########################################################################

urlpatterns = [
    url(r"^login/$", login, name="app-login"),
    url(r"^launch/$", launch, name="app-launch"),
    url(r"^upload/$", upload, name="app-upload"),
    url(r"^consult/$", consult, name="app-consult"),
    url(r"^jwks/$", get_jwks, name="app-jwks"),
]

########################################################################

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

########################################################################

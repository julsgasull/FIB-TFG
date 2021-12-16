from django.conf import settings
from django.conf.urls import url
from django.urls import include, path
from .views import (
    login,
    launch,
    index,
    upload,
    consult,
    get_jwks,
    consult_file_last_version,
    consult_file_version_for_date,
    consult_versions,
    delete_file,
    download_file,
)

########################################################################

urlpatterns = [
    url(r"^login/$", login, name="app-login"),
    url(r"^launch/$", launch, name="app-launch"),
    url(r"^index/$", index, name="app-index"),
    url(r"^upload/$", upload, name="app-upload"),
    url(r"^consult/$", consult, name="app-consult"),
    url(r"^jwks/$", get_jwks, name="app-jwks"),
    path(
        "consult/file/(?P<name>[\w\-]+)",
        consult_file_last_version,
        name="app-consult-file-last-version",
    ),
    path(
        "consult/versions/file/(?P<name>[\w\-]+)",
        consult_versions,
        name="app-consult-versions",
    ),
    path(
        "consult/file-version/(?P<name>[\w\-]+)/(?P<date>[\w\-]+)",
        consult_file_version_for_date,
        name="app-consult-file-version-for",
    ),
    path(
        "delete/file/(?P<name>[\w\-]+)",
        delete_file,
        name="app-delete-file",
    ),
    path(
        "download/file/(?P<name>[\w\-]+)",
        download_file,
        name="app-download-file",
    ),
]

########################################################################

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

########################################################################

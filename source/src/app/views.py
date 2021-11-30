import datetime
import os
import pprint

from django.conf import settings as django_settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.urls import reverse
from pylti1p3.contrib.django import (
    DjangoOIDCLogin,
    DjangoMessageLaunch,
    DjangoCacheDataStorage,
)
from pylti1p3.deep_link_resource import DeepLinkResource
from pylti1p3.grade import Grade
from pylti1p3.lineitem import LineItem
from pylti1p3.tool_config import ToolConfJsonFile
from pylti1p3.registration import Registration

from app.settings import PAGE_TITLE

from django.core.files.storage import FileSystemStorage


########################################################################


class ExtendedDjangoMessageLaunch(DjangoMessageLaunch):
    def validate_nonce(self):
        """
        Probably it is bug on "https://lti-ri.imsglobal.org":
        site passes invalid "nonce" value during deep links launch.
        Because of this in case of iss == http://imsglobal.org just skip nonce validation.

        """
        iss = self.get_iss()
        deep_link_launch = self.is_deep_link_launch()
        if iss == "http://imsglobal.org" and deep_link_launch:
            return self
        return super(ExtendedDjangoMessageLaunch, self).validate_nonce()


########################################################################


def get_lti_config_path():
    return os.path.join(django_settings.BASE_DIR, "..", "configs", "app.json")


########################################################################


def get_tool_conf():
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    return tool_conf


########################################################################


def get_jwk_from_public_key(key_name):
    key_path = os.path.join(django_settings.BASE_DIR, "..", "configs", key_name)
    f = open(key_path, "r")
    key_content = f.read()
    jwk = Registration.get_jwk(key_content)
    f.close()
    return jwk


########################################################################


def get_launch_data_storage():
    return DjangoCacheDataStorage()


########################################################################


def get_launch_url(request):
    target_link_uri = request.POST.get(
        "target_link_uri", request.GET.get("target_link_uri")
    )
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')
    return target_link_uri


########################################################################


def login(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()

    oidc_login = DjangoOIDCLogin(
        request, tool_conf, launch_data_storage=launch_data_storage
    )
    target_link_uri = get_launch_url(request)
    return oidc_login.enable_check_cookies().redirect(target_link_uri)


########################################################################


@require_POST
def launch(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedDjangoMessageLaunch(
        request, tool_conf, launch_data_storage=launch_data_storage
    )
    message_launch_data = message_launch.get_launch_data()
    pprint.pprint(message_launch_data)

    return render(
        request,
        "index.html",
        {
            "page_title": PAGE_TITLE,
            "is_deep_link_launch": message_launch.is_deep_link_launch(),
            "launch_data": message_launch.get_launch_data(),
            "launch_id": message_launch.get_launch_id(),
            "curr_user_name": message_launch_data.get("name", ""),
        },
    )


########################################################################


def upload(request):
    tool_conf = get_tool_conf()
    if request.method == "POST":
        uploaded_file = request.FILES["document"]
        fs = FileSystemStorage()
        fs.save(uploaded_file.name, uploaded_file)
    return render(request, "upload.html", {"page_title": PAGE_TITLE})


########################################################################


def consult(request):
    tool_conf = get_tool_conf()
    return render(request, "consult.html", {"page_title": PAGE_TITLE})


########################################################################


def get_jwks(request):
    tool_conf = get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


########################################################################

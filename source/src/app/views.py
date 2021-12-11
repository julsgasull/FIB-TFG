from datetime import datetime

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

from app.settings import MEDIA_ROOT
from app.db import *

from django.core.files.storage import FileSystemStorage

import numpy as np


########################################################################

# initialize global variables
user_name = ""
user_username = ""
course_id = -1
course_name = ""

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
    # get data for launch
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedDjangoMessageLaunch(
        request, tool_conf, launch_data_storage=launch_data_storage
    )
    message_launch_data = message_launch.get_launch_data()
    pprint.pprint(message_launch_data)

    # set velues to global variables
    global user_name, user_username, course_id, course_name
    user_name = message_launch_data.get("name", "")
    user_username = message_launch_data.get(
        "https://purl.imsglobal.org/spec/lti/claim/ext", ""
    ).get("user_username", "")
    course_id = message_launch_data.get(
        "https://purl.imsglobal.org/spec/lti/claim/context", ""
    ).get("id", "")
    course_name = message_launch_data.get(
        "https://purl.imsglobal.org/spec/lti/claim/context", ""
    ).get("title", "")

    # render index.html
    return render(
        request,
        "index.html",
        {
            "is_deep_link_launch": message_launch.is_deep_link_launch(),
            "launch_data": message_launch.get_launch_data(),
            "launch_id": message_launch.get_launch_id(),
            "user_name": user_name,
            "user_username": user_username,
            "course_id": course_id,
            "course_name": course_name,
        },
    )


########################################################################


def upload(request):
    # get data
    tool_conf = get_tool_conf()

    # code for uploading file
    if request.method == "POST":
        # get the file
        uploaded_file = request.FILES["document"]
        # compute some information
        now_string = datetime.now().strftime("%d_%m_%Y__%H_%M_%S")
        file_name = uploaded_file.name
        file_path = course_id + "/" + file_name + "/" + now_string + "/" + file_name
        # save file to media folder
        fs = FileSystemStorage()
        fs.save(MEDIA_ROOT + "/" + file_path, uploaded_file)
        uploaded_file_url = fs.url(file_name)
        # add to database
        add_file_public(course_id, user_username, now_string, file_name, file_path)

        return render(
            request,
            "upload.html",
            {
                "user_name": user_name,
                "user_username": user_username,
                "course_id": course_id,
                "course_name": course_name,
                "uploaded_file_url": uploaded_file_url,
            },
        )
    # data for before uploading
    return render(
        request,
        "upload.html",
        {
            "user_name": user_name,
            "user_username": user_username,
            "course_id": course_id,
            "course_name": course_name,
        },
    )


########################################################################


def consult(request):
    # get data
    tool_conf = get_tool_conf()

    files = get_files_first_version_public(course_id)
    print("FILES:\n")
    for file in files:
        print("\n")
        print("course_id = " + file[0])
        print("username = " + file[1])
        print("date = " + file[2])
        print("file_name = " + file[3])
        print("file_path = " + file[4])
    print("---------------------------")

    return render(
        request,
        "consult.html",
        {
            "user_name": user_name,
            "user_username": user_username,
            "course_id": course_id,
            "course_name": course_name,
            "files": files,
        },
    )


########################################################################


def consult_file(request, filename):
    # get data
    tool_conf = get_tool_conf()

    return render(
        request,
        "consult_file.html",
        {
            "user_name": user_name,
            "user_username": user_username,
            "course_id": course_id,
            "course_name": course_name,
            "file_name": filename,
        },
    )


########################################################################


def get_jwks(request):
    tool_conf = get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


########################################################################

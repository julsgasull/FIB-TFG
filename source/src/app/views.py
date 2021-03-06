from datetime import datetime

import os
import pprint

from django.conf import settings as django_settings
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    JsonResponse,
    FileResponse,
    Http404,
)

from django.http.response import Http404
from django.shortcuts import render, redirect
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

import shutil

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

    return index(request)


########################################################################


def index(request):
    # get data for launch
    tool_conf = get_tool_conf()

    # render index.html
    return render(
        request,
        "index.html",
        {
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
        uploaded_file = request.FILES.get("document", False)
        if uploaded_file != False:
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
        else:
            raise Http404("You must select a file to upload.")
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
    # print("FILES:\n")
    # for file in files:
    #     print("\n")
    #     print("course_id = " + file[0])
    #     print("username = " + file[1])
    #     print("date = " + file[2])
    #     print("file_name = " + file[3])
    #     print("file_path = " + file[4])
    # print("---------------------------")

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


def get_jwks(request):
    tool_conf = get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


########################################################################


def edit_file_last_version(request, name):
    # get data
    tool_conf = get_tool_conf()

    file_path = MEDIA_ROOT + "/" + get_file_path_last_version_public(course_id, name)

    extension = os.path.splitext(name)[1]
    print("extension = " + extension)
    if (
        extension == ".md"
        or extension == ".MD"
        or extension == ".txt"
        or extension == ".TXT"
    ):
        f = open(file_path, "r")
        file_content = f.read()
        f.close()

        # code for editing file
        if request.method == "POST":
            new_content = request.POST["content"]
            now_string = datetime.now().strftime("%d_%m_%Y__%H_%M_%S")
            # create folders if don't exist
            file_dir_path = course_id + "/" + name + "/" + now_string
            os.makedirs(MEDIA_ROOT + "/" + file_dir_path, exist_ok=False)
            # create file and fill it
            file_path = course_id + "/" + name + "/" + now_string + "/" + name
            f = open(MEDIA_ROOT + "/" + file_path, "w+")
            f.write(new_content)
            # add to database
            add_file_public(course_id, user_username, now_string, name, file_path)
            return consult_versions(request, name)
        # data for before editing
        return render(
            request,
            "edit_file.html",
            {
                "user_name": user_name,
                "user_username": user_username,
                "course_id": course_id,
                "course_name": course_name,
                "file_name": name,
                "file_path": file_path,
                "file_extension": extension,
                "file_content": file_content,
            },
        )
    else:
        raise Http404(
            "This file type ("
            + extension
            + ") cannot be edited. Try uploading the new version with the same name to modify it."
        )


########################################################################


def consult_file_last_version(request, name):
    # get data
    print("Consult_file_last_version")

    tool_conf = get_tool_conf()

    file_path = MEDIA_ROOT + "/" + get_file_path_last_version_public(course_id, name)
    print("    File path = " + file_path)
    extension = os.path.splitext(name)[1]
    print("extension = " + extension)
    if extension == ".pdf" or extension == ".PDF":
        return FileResponse(open(file_path, "rb"), content_type="application/pdf")
    elif extension == ".png" or extension == ".PNG":
        image_data = open(file_path, "rb").read()
        return HttpResponse(image_data, content_type="image/png")
    elif extension == ".jpg" or extension == ".JPG":
        image_data = open(file_path, "rb").read()
        return HttpResponse(image_data, content_type="image/jpg")
    else:
        f = open(file_path, "r")
        file_content = f.read()
        f.close()
        return render(
            request,
            "consult_file.html",
            {
                "user_name": user_name,
                "user_username": user_username,
                "course_id": course_id,
                "course_name": course_name,
                "file_name": name,
                "file_path": file_path,
                "file_extension": extension,
                "file_content": file_content,
            },
        )


########################################################################


def consult_versions(request, name):
    # get data
    tool_conf = get_tool_conf()

    file_info = get_file_all_versions_public(course_id, name)

    return render(
        request,
        "consult_versions.html",
        {
            "user_name": user_name,
            "user_username": user_username,
            "course_id": course_id,
            "course_name": course_name,
            "file_name": name,
            "file_info": file_info,
        },
    )


########################################################################


def consult_file_version_for_date(request, name, date):
    # get data
    tool_conf = get_tool_conf()

    file_path = (
        MEDIA_ROOT + "/" + get_file_path_version_for_date_public(course_id, name, date)
    )
    print("FILE PATH = " + file_path)

    extension = os.path.splitext(name)[1]
    print("extension = " + extension)
    if extension == ".pdf" or extension == ".PDF":
        return FileResponse(open(file_path, "rb"), content_type="application/pdf")
    elif extension == ".png" or extension == ".PNG":
        image_data = open(file_path, "rb").read()
        return HttpResponse(image_data, content_type="image/png")
    elif extension == ".jpg" or extension == ".JPG":
        image_data = open(file_path, "rb").read()
        return HttpResponse(image_data, content_type="image/jpg")
    else:
        f = open(file_path, "r")
        file_content = f.read()
        f.close()
        return render(
            request,
            "consult_file.html",
            {
                "user_name": user_name,
                "user_username": user_username,
                "course_id": course_id,
                "course_name": course_name,
                "file_name": name,
                "file_path": file_path,
                "file_extension": extension,
                "file_content": file_content,
            },
        )


########################################################################


def delete_file(request, name):
    # get data
    tool_conf = get_tool_conf()

    full_path = MEDIA_ROOT + "/" + course_id + "/" + name
    print("FULL PATH = " + full_path)

    if os.path.exists(full_path):
        shutil.rmtree(full_path)
        print("files in path " + full_path + " removed")
        # db
        delete_file_public(course_id, name)
    else:
        raise Http404(
            "Something happened while deleting. Reload the page and try again. Sorry for the inconvenience."
        )

    return redirect("app-consult")


########################################################################


def download_file(request, name):
    # get data
    tool_conf = get_tool_conf()

    file_path = MEDIA_ROOT + "/" + get_file_path_last_version_public(course_id, name)
    if os.path.exists(file_path):
        with open(file_path, "rb") as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response["Content-Disposition"] = "inline; filename=" + os.path.basename(
                file_path
            )
            return response
    raise Http404(
        "Something happened while downloading. Reload the page and try again. Sorry for the inconvenience."
    )


########################################################################

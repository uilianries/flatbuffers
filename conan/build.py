#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan.packager import ConanMultiPackager
import os, re


def get_value_from_recipe(search_string):
    with open("conanfile.py", "r") as conanfile:
        contents = conanfile.read()
        result = re.search(search_string, contents)
    return result


def get_name_from_recipe():
    return get_value_from_recipe(r'''name\s*=\s*["'](\S*)["']''').groups()[0]


def get_version_from_recipe():
    return get_value_from_recipe(r'''version\s*=\s*["'](\S*)["']''').groups()[0]


def running_on_appveyor():
    return os.getenv("APPVEYOR", False)


def get_env_vars():
    username = os.getenv("CONAN_USERNAME", "flatbuffers")
    channel = os.getenv("CONAN_CHANNEL", "testing")
    name = get_name_from_recipe()
    version = get_version_from_recipe()
    return name, version, username, channel


def get_stable_branch_pattern():
    return "master" if running_on_appveyor() else r"v\d+\.\d+\.\d+"


if __name__ == "__main__":
    name, version, username, channel = get_env_vars()
    reference = "{0}/{1}".format(name, version)
    upload = "https://api.bintray.com/conan/{0}/conan".format(username)
    stable_branch_pattern = get_stable_branch_pattern()
    test_folder = "-tf %s" % os.path.join("conan", "test_package")

    builder = ConanMultiPackager(
        args=test_folder,
        username=username,
        channel=channel,
        reference=reference,
        upload=upload,
        remotes=upload,
        upload_only_when_stable=True,
        stable_branch_pattern=stable_branch_pattern)

    builder.add_common_builds(shared_option_name="%s:shared" % name, pure_c=False)

    if running_on_appveyor():
        filtered_builds = []
        ci_platform = os.getenv("Platform")
        ci_platform = "x86_64" if ci_platform == "x64" else "x86"
        ci_configuration = os.getenv("Configuration")
        compiler_version = os.getenv("CMAKE_VS_VERSION").split(" ")[0].replace('"', '')

        for settings, options, env_vars, build_requires, reference in builder.items:
            if settings['build_type'] != ci_configuration:
                continue
            if settings['arch'] != ci_platform:
                continue
            if settings['compiler.version'] != compiler_version:
                continue

            filtered_builds.append([settings, options, env_vars, build_requires])

        builder.builds = filtered_builds

    builder.run()

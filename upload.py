#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author : AloneMonkey
# blog: www.alonemonkey.com

import os
import sys
import re
import json
import plistlib
import argparse
import zipfile
import shutil
import subprocess
from qiniu import Auth, put_file, etag
import qiniu.config
from jinja2 import Environment, FileSystemLoader 

# Read user config file
script_dir = os.path.dirname(os.path.realpath(__file__))
user_config = os.path.join(script_dir, 'config', 'user.config')

with open(user_config, 'r') as read:
    config = json.load(read)  

q = Auth(config['access_key'], config['secret_key'])

def render_and_write(template_file, path, context):
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_file)))
    template = env.get_template(os.path.basename(template_file))
    rendered_content = template.render(context)
    if not rendered_content:
        print("Render returned None - skipping '%s'" % path)
        return

    with open(path, 'wb') as out:
        out.write(rendered_content.encode('utf-8').strip())

def get_file_size(filePath):
    fsize = os.path.getsize(filePath)
    unit = 'unknow'
    if fsize < 1024*1024:
        fsize = fsize/float(1024)
        unit = 'KB'
    elif fsize >= 1024*1024 and fsize < 1024*1024*1024:
        fsize = fsize/float(1024*1024)
        unit = 'MB'
    else:
        fsize = fsize/float(1024*1024*1024)
        unit = 'GB'
    return str(round(fsize,2)) + unit

class IPAParser(object):
    
    plist_file_rx = re.compile(r'Payload/.+?\.app/Info.plist$')

    def __init__(self, ipa_file_path):
        self.ipa_file_path = ipa_file_path
        self.zip_obj = zipfile.ZipFile(self.ipa_file_path, 'r')

    def get_files_from_ipa(self, file_regx):
        filenames = [file for file in self.zip_obj.namelist() if file_regx.search(file)]
        return filenames

    def get_info_plist_data(self):
        info_plists = self.get_files_from_ipa(self.plist_file_rx)
        if len(info_plists):
            info_plist_name = info_plists[0]
            info_plist_data = self.zip_obj.read(info_plist_name)
            plist_root = plistlib.loads(info_plist_data)
            return plist_root
        return None

    def main_icon_name(self):
        result = []
        icon_name = None
        plist_root = self.get_info_plist_data()
        if 'CFBundleIcons' in plist_root \
        and 'CFBundlePrimaryIcon' in plist_root['CFBundleIcons'] \
        and 'CFBundleIconFiles' in plist_root['CFBundleIcons']['CFBundlePrimaryIcon']:
            result =  plist_root['CFBundleIcons']['CFBundlePrimaryIcon']['CFBundleIconFiles']

        if not len(result) and 'CFBundleIconFiles' in plist_root :
            result = plist_root['CFBundleIconFiles']

        if len(result):
            filter_result = list(filter(lambda x: '@2x' in x, result))
            if not len(filter_result):
                filter_result = list(filter(lambda x: '60' in x, result))
                if len(filter_result) and os.path.splitext(filter_result[0])[1] == '' and (not filter_result[0].endswith('@2x')):
                    icon_name = filter_result[0] + '@2x'
            else:
                icon_name = filter_result[0]
        else:
            icon_name = plist_root['CFBundleIconFile']

        if icon_name and os.path.splitext(icon_name)[1] == '':
            icon_name += '.png'

        return icon_name
    
    def extra_file_to_path(self, filename, path):
        if not filename:
            return None

        filter_list = list(filter(lambda x : x.endswith(filename) ,self.zip_obj.namelist()))
        if len(filter_list):
            file_path = filter_list[0]
            self.zip_obj.extractall(path, members=[file_path])
            return os.path.join(path, file_path)
            
        return None

    def is_valid_zip_file(self):
        return zipfile.is_zipfile(self.ipa_file_path)

def upload_file_to_qiniu(file_path, file_name):
    print("[%s] uploading......" % file_name)
    token = q.upload_token(config['bucket_name'], file_name)
    ret, _ = put_file(token, file_name, file_path)
    assert ret['key'] == file_name
    assert ret['hash'] == etag(file_path)
    return os.path.join(config['bucket_url'], ret['key'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ipa-upload-script (by AloneMonkey v1.0)')
    parser.add_argument('target', nargs='?', help='The path of target ipa file')
    args = parser.parse_args()

    exit_code = 0
    failed_code = -1
    errors = []

    if not len(sys.argv[1:]):
        parser.print_help()
        sys.exit(exit_code)

    ipa_file_path = args.target 

    if not os.path.exists(ipa_file_path):
        print("[%s] is not existed!" % ipa_file_path)
        exit(failed_code)

    ipa_parser = IPAParser(ipa_file_path)

    if not ipa_parser.is_valid_zip_file():
        print('[%s] is not a valid zip file' % ipa_file_path)
        sys.exit(failed_code)

    plist_root = ipa_parser.get_info_plist_data()
    bundle_id = plist_root.get('CFBundleIdentifier')
    bundle_version = plist_root.get('CFBundleShortVersionString')
    bundle_version_build = plist_root.get('CFBundleVersion', 'build')
    display_name = plist_root.get('CFBundleDisplayName') or plist_root.get('CFBundleName')
    executable_name = plist_root.get('CFBundleExecutable')

    # upload ipa file
    upload_ipa_url = upload_file_to_qiniu(ipa_file_path, executable_name + ".ipa")

    icon_name = ipa_parser.main_icon_name() 

    upload_icon_url = 'http://o9slcszsf.bkt.clouddn.com/largeImage.png'

    local_icon_path = ipa_parser.extra_file_to_path(icon_name, os.path.join(script_dir, 'icons', executable_name))

    if local_icon_path:
        pngcrush_args = ('/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/usr/bin/pngcrush', '-q', '-e', '.fixed', '-revert-iphone-optimizations', local_icon_path)
        try:
            subprocess.check_call(pngcrush_args)
        except subprocess.CalledProcessError as err:
            print(err)
        shutil.move(os.path.splitext(local_icon_path)[0] + '.fixed', local_icon_path)   
        upload_icon_url = upload_file_to_qiniu(local_icon_path, executable_name + '-' + icon_name)

    plist_name = executable_name + '.plist'
    html_name = executable_name + '.html'

    write_plist_path = os.path.join(script_dir, 'plists', plist_name)
    write_html_path = os.path.join(script_dir, 'htmls', html_name)

    render_and_write(os.path.join(script_dir, 'template.plist'), write_plist_path, 
        {
            'ipa' : upload_ipa_url,
            'large' : upload_icon_url,
            'small' : upload_icon_url,
            'bundleid' : bundle_id,
            'version' : bundle_version,
            'name' : display_name
        })

    render_and_write(os.path.join(script_dir, 'template.html'), write_html_path,
        {
          'icon' : upload_icon_url,
          'name' : display_name,
          'version' : bundle_version,
          'build' : bundle_version_build,
          'size' : get_file_size(ipa_file_path),
          'plisturl' : os.path.join(config['repo_url'], 'plists', plist_name)
        })

    html_url = upload_file_to_qiniu(write_html_path, html_name)

    print("Please push local branch to remote, Then open %s install" % html_url)

    

    

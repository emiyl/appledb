#!/usr/bin/env python3

import hashlib
import json
import plistlib
import random
import subprocess
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse

import requests

from sort_os_files import sort_os_file
from update_links import update_links

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--version', type=int, default=17)
parser.add_argument('-b', '--beta', action='store_true')
args = parser.parse_args()

SESSION = requests.session()

mac_versions = [
    args.version - 5,
    args.version - 4
]

mac_codenames = json.load(Path("tasks/macos_codenames.json").open(encoding="utf-8"))

MAC_CATALOG_SUFFIX = ''
if args.beta:
    MAC_CATALOG_SUFFIX = 'seed'

SAFARI_DETAILS = {}

for mac_version in mac_versions:
    raw_sucatalog = SESSION.get(f'https://swscan.apple.com/content/catalogs/others/index-{mac_version}{MAC_CATALOG_SUFFIX}-1.sucatalog?cachebust{random.randint(100, 1000)}')
    raw_sucatalog.raise_for_status()

    plist = plistlib.loads(raw_sucatalog.content)['Products']
    catalog_safari = None
    for product in plist.values():
        if f"Safari{args.version}" not in product.get("ServerMetadataURL", ""):
            continue

        dist_response = SESSION.get(product['Distributions']['English']).text
        dist_version = dist_response.split('"SU_VERS" = "')[1].split('"')[0].replace('Seed', 'beta')
        catalog_safari = product
        break

    if not catalog_safari:
        print(f'Missing Safari for macOS {mac_version}')
        continue

    safari_destination_path = f'out/Safari_{dist_version.replace(" ", "_")}_{mac_version}'
    plist_path = ''
    file_hashes = {}
    sha1 = hashlib.sha1()
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with open(f'{safari_destination_path}.pkg', 'wb') as pkg_file:
        data = SESSION.get(catalog_safari['Packages'][0]['URL']).content
        pkg_file.write(data)
        sha1.update(data)
        sha256.update(data)
        md5.update(data)
        pkgutil_response = subprocess.run(['pkgutil', '--expand', f'{safari_destination_path}.pkg', f'{safari_destination_path}'])
        pkgutil_response.check_returncode()

        file_hashes['sha1'] = sha1.hexdigest()
        file_hashes['sha2-256'] = sha256.hexdigest()
        file_hashes['md5'] = md5.hexdigest()

        with open(f'{safari_destination_path}/Payload', 'rb') as payload_file:
            if mac_version <= 12:
                plist_path = 'Applications/Safari.app/Contents/version.plist'
            else:
                plist_path = 'Library/Apple/Safari/Cryptex/Restore/BuildManifest.plist'
            cpio_response = subprocess.run(['cpio', '-id', f'./{plist_path}'], stdin=payload_file, cwd=safari_destination_path, stderr=subprocess.DEVNULL)
            cpio_response.check_returncode()
    
    safari_plist = plistlib.loads(Path(f'{safari_destination_path}/{plist_path}').read_bytes())
    safari_build = safari_plist['ProductBuildVersion']
    print(mac_codenames[str(mac_version)])
    print(safari_build)
    safari_buildtrain = None
    if plist_path.endswith('BuildManifest.plist'):
        safari_buildtrain = safari_plist['BuildIdentities'][0]['Info']['BuildTrain']

    is_beta = 'beta' in dist_version
    if not SAFARI_DETAILS.get(safari_build):
        release_notes_link = ''
        if not is_beta and len(dist_version.split('.')) <= 2:
            release_notes_link = f'https://developer.apple.com/documentation/safari-release-notes/safari-{dist_version.removesuffix(".0").replace(".", "_")}-release-notes'

        SAFARI_DETAILS[safari_build] = {
            "osStr": "Safari",
            "version": dist_version,
            "build": safari_build,
            "released": catalog_safari['PostDate'].replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo('America/Los_Angeles')).strftime("%Y-%m-%d"),
            "deviceMap": [
                "Safari (macOS)"
            ],
            "osMap": [],
            "sources": []
        }

        if release_notes_link:
            SAFARI_DETAILS[safari_build]['releaseNotes'] = release_notes_link

        if is_beta:
            SAFARI_DETAILS[safari_build]['beta'] = True


    SAFARI_DETAILS[safari_build]["osMap"].append(f"macOS {mac_version}")

    if safari_buildtrain and not SAFARI_DETAILS[safari_build].get('buildTrain'):
        SAFARI_DETAILS[safari_build]['buildTrain'] = safari_buildtrain

    SAFARI_DETAILS[safari_build]["sources"].append({
        "type": "pkg",
        "deviceMap": [
            "Safari (macOS)"
        ],
        "osMap": [
            f"macOS {mac_version}"
        ],
        "hashes": file_hashes,
        "links": [
            {
                "url": catalog_safari['Packages'][0]['URL']
            }
        ]
    })

    Path(f'{safari_destination_path}.pkg').unlink()
    shutil.rmtree(safari_destination_path)

for build, details in SAFARI_DETAILS.items():
    safari_file = Path(f'osFiles/Software/Safari/{args.version}.x/{build}.json')
    if safari_file.exists():
        parsed_safari_file = json.load(safari_file.open(encoding="utf-8"))
        if parsed_safari_file['version'] != details['version'] or parsed_safari_file['osMap'] != details['osMap']:
            if parsed_safari_file.get('beta') and not details.get('beta'):
                build_suffix = parsed_safari_file['version'].split(" ", 1)[1].replace(" ", "")
                parsed_safari_file['key'] = f"{build}-{build_suffix}"
                old_safari_file = Path(f"osFiles/Software/Safari/{args.version}.x/{build}-{build_suffix}.json")
                json.dump(sort_os_file(None, parsed_safari_file), old_safari_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
            else:
                if details.get('beta'):
                    build_suffix = details['version'].split(" ", 1)[1].replace(" ", "")
                else:
                    build_suffix = mac_codenames[details['osMap'][0].split(" ", 1)[1]].replace(" ", "").lower()
                safari_file = Path(f"osFiles/Software/Safari/{args.version}.x/{build}-{build_suffix}.json")
                details['key'] = f"{build}-{build_suffix}"
                if safari_file.exists():
                    print(f"Skipping {build} for {', '.join(details['osMap'])}")
                    continue
        else:
            print(f"Skipping {build} for {', '.join(details['osMap'])}")
            continue
    json.dump(sort_os_file(None, details), safari_file.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
    update_links([safari_file])

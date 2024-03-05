from pathlib import Path
from datetime import datetime
import argparse
import json
import zoneinfo

from sort_os_files import sort_os_file
from support_page_info import get_release_notes_link

supported_subfolders = [
    'audioOS',
    'bridgeOS',
    'iOS',
    'iPadOS',
    'macOS',
    'tvOS',
    'visionOS',
    'watchOS',
    'Studio Display Firmware',
    'Rosetta',
    'Xcode',
    'Simulators/iOS',
    'Simulators/tvOS',
    'Simulators/visionOS',
    'Simulators/watchOS'
]

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--os', required=True, action='append', choices=supported_subfolders)
parser.add_argument('-b', '--build', required=True, action='append', nargs='+')
parser.add_argument('-d', '--exclude-devices', nargs='+')
args = parser.parse_args()

parsed_builds = dict(zip(args.os, args.build))

developer_beta_rc_link_rename = False

for (osStr, builds) in parsed_builds.items():
    if osStr == 'Xcode' or osStr.startswith('Simulators/'):
        developer_beta_rc_link_rename = True
    else:
        developer_beta_rc_link_rename = False
    for build in builds:
        if osStr in ['Rosetta', 'Xcode']:
            osStr = f'Software/{osStr}'
        file_path = list(Path(f'osFiles/{osStr}').rglob(f'{build}.json'))
        if not file_path:
            print(f"Invalid build: {osStr} {build}")
            continue
        file_path = file_path[0]
        file_data = json.load(file_path.open())
        duplicate_entry = {}
        if file_data.get('rc'):
            duplicate_entry['rc'] = True
            del file_data['rc']
            duplicate_entry['version'] = file_data['version']
            file_data['version'] = file_data['version'].split(' RC')[0]
            duplicate_entry['key'] = file_data['build'] + '-RC'
        elif file_data.get('beta'):
            duplicate_entry['beta'] = True
            del file_data['beta']
            duplicate_entry['version'] = file_data['version']
            file_data['version'] = file_data['version'].split(' beta')[0]
            duplicate_entry['key'] = file_data['build'] + '-beta'
        else:
            print(f"Skipping {osStr} {build} as it's not beta or RC")
            continue

        if developer_beta_rc_link_rename and file_data.get('sources', []):
            duplicate_entry['sources'] = file_data['sources']
            for source in file_data['sources']:
                for link in source['links']:
                    extension = link['url'].rsplit('.', 1)[1]
                    link['url'] = link['url'].replace('_Release_Candidate', '')
        duplicate_entry['released'] = file_data['released']
        file_data['released'] = datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
        release_notes_link = get_release_notes_link(file_data["osStr"], file_data["version"])
        if release_notes_link:
            file_data["releaseNotes"] = release_notes_link

        if args.exclude_devices:
            excluded_devices = list(set(args.exclude_devices).intersection(set(file_data['deviceMap'])))
            print(excluded_devices)
            if excluded_devices:
                duplicate_entry['deviceMap'] = file_data['deviceMap']
                file_data['deviceMap'] = [x for x in file_data['deviceMap'] if x not in excluded_devices]
                if file_data.get('sources'):
                    duplicate_entry['sources'] = file_data['sources']
                    file_data['sources'] = [source for source in file_data['sources'] if source['deviceMap'][0] not in excluded_devices]

        file_data.setdefault('createDuplicateEntries', [])
        file_data['createDuplicateEntries'].append(duplicate_entry)
        json.dump(sort_os_file(None, file_data), file_path.open("w", encoding="utf-8", newline="\n"), indent=4, ensure_ascii=False)
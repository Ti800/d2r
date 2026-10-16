"""Build an AltStore-format source (also read by Feather/SideStore) from this repository's IPA releases.

Usage: altstore_source.py <own releases.json> <upstream releases.json> <source url> > altstore.json
"""
import json, re, sys

BUNDLE_ID = 'org.d2rmobile.app'
UPSTREAM = 'jhaizhou-ops/d2r-mobile'
ICON = f'https://raw.githubusercontent.com/{UPSTREAM}/main/dm/ios/Assets.xcassets/AppIcon.appiconset/AppIcon1024.png'
TAG = re.compile(r'^(v(\d+(?:\.\d+)+))-build\.(\d+\.\d+)$')
KEEP = 10


def notes(upstream, tag):
    """The Chinese section of the upstream release notes, without build-input tables and verification details."""
    body = upstream.get(tag, '')
    start = body.find('## 中文')
    if start < 0:
        return f'https://github.com/{UPSTREAM}/releases/tag/{tag}'
    text = body[start + len('## 中文'):].split('### 这一版是怎么验的')[0]
    paragraphs = [p.strip() for p in text.split('\n\n')]
    kept = [p for p in paragraphs if p and not p.startswith('|') and 'd2rm_pack' not in p and '构建原料' not in p]
    text = '\n\n'.join(kept)
    if len(text) > 3000:
        text = text[:3000].rstrip() + '…'
    return f'{text}\n\nhttps://github.com/{UPSTREAM}/releases/tag/{tag}'.strip()


def main(own_path, upstream_path, source_url):
    own = json.load(open(own_path))
    upstream = {r['tag_name']: r.get('body') or '' for r in json.load(open(upstream_path))}
    versions = []
    for release in own:
        match = TAG.match(release['tag_name'])
        if release['draft'] or release['prerelease'] or not match:
            continue
        # The unsuffixed IPA is the iOS 26+ build; -ios18.ipa targets iOS 18-25.
        ipa = next((a for a in release['assets'] if a['name'].endswith('.ipa') and not a['name'].endswith('-ios18.ipa')), None)
        if not ipa:
            continue
        versions.append({
            'version': match[2],
            'buildVersion': match[3],
            'date': release['published_at'],
            'localizedDescription': notes(upstream, match[1]),
            'downloadURL': ipa['browser_download_url'],
            'size': ipa['size'],
            'minOSVersion': '26.0',
        })
    versions.sort(key=lambda v: v['date'], reverse=True)
    versions = versions[:KEEP]
    if not versions:
        sys.exit('No IPA releases found')
    latest = versions[0]
    owner = source_url.split('/')[3]
    source = {
        'name': f'D2R Mobile ({owner})',
        'identifier': f'io.github.{owner.lower()}.d2r',
        'sourceURL': source_url,
        'iconURL': ICON,
        'apps': [{
            'name': 'D2R Mobile',
            'bundleIdentifier': BUNDLE_ID,
            'developerName': UPSTREAM.split('/')[0],
            'subtitle': 'Diablo II: Resurrected 原生 iOS 移植',
            'localizedDescription': f'从 {UPSTREAM} 最新正式版自动构建（iOS 26 及以上）。游戏资源需另行导入。',
            'iconURL': ICON,
            'tintColor': '8B1A1A',
            'category': 'games',
            'versions': versions,
            # Legacy single-version fields for clients that predate `versions`.
            'version': latest['version'],
            'versionDate': latest['date'],
            'versionDescription': latest['localizedDescription'],
            'downloadURL': latest['downloadURL'],
            'size': latest['size'],
            'appPermissions': {'entitlements': [], 'privacy': {}},
        }],
        'news': [],
    }
    json.dump(source, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main(*sys.argv[1:])

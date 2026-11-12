"""从 test2 抓真实定义，落 definitions/。CDP 页面内 fetch（复用页面 cookie）。

关键：GraphQL query 必须用「graphqlLoader (」带空格 + 换行分隔字段，否则
Seeyon 自定义解析器报 "offending token ':'"。
"""
import sys, json, os
sys.path.insert(0, '.')
from providers.cdp import CdpClient

APP = '8704025620829192834'
APP_NAME = 'datamigration9000000000000000001'
OUT_DIR = 'definitions'

def gql(op, content_fields, variables):
    """构造 Seeyon GraphQL body。content_fields 是 content{} 内的多行字段串。"""
    q = (f'mutation graphqlLoader ($params0: {op}InputBody) {{ \n'
         f'  data0: {op}(body: $params0) {{ code data {{ \n'
         f'    content{{\n{content_fields}\n    }}\n'
         f'     }} message status }} }}')
    return {'query': q, 'variables': {'params0': variables}}

def fetch_gql(c, op, query_fields, variables):
    body = gql(op, query_fields, variables)
    js = ('(async()=>{const r=await fetch(location.origin+\'/service/udc/graphql?' + op +
          '\',{method:\'POST\',credentials:\'include\',headers:{\'Content-Type\':\'application/json\'},body:' +
          json.dumps(json.dumps(body)) + '});return await r.json();})()')
    return c.evaluate(js, await_promise=True)

def save(name, data):
    fp = os.path.join(OUT_DIR, name)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    json.dump(data, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已存', fp)

def main():
    c = CdpClient(9250, allow_network=True, timeout=30)
    c.connect(url_substr='microflow/editor')

    # 1. 实体 DTO attributes
    r = fetch_gql(c, 'udcMicroflowFindCustomDtoPost',
        '      attributes\n      caption\n      fullName\n      type\n      relationEntityId\n      methodLegals\n      dtoType\n      udcApp\n      refApp\n      entity',
        {'appId': APP, 'appName': APP_NAME,
         'dtoFullName': 'com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto',
         'needChildren': False})
    content = r.get('data', {}).get('data0', {}).get('data', {}).get('content')
    if content:
        save('entities/XzhExp950795Dto.json', content)
        attrs = content.get('attributes') or {}
        print('  实体字段数:', len(attrs))
    else:
        print('实体DTO 失败:', json.dumps(r, ensure_ascii=False)[:300])

    # 2. 服务方法 parameter/returnValue（文件复制）
    r = fetch_gql(c, 'udcMicroflowSearchMethodByNamePost',
        '      caption\n      customs\n      description\n      dubbo\n      dubboVersion\n      fullName\n      group\n      implClass\n      interfaceClass\n      md5\n      parameter{\n        caption\n        type\n        item{\n          enums\n          itemType\n          item{\n            enums\n            itemType\n            javaType\n            dataType\n            keyType\n          }\n        }\n      }\n      returnValue{\n        caption\n        type\n        item{\n          enums\n          itemType\n          item{\n            enums\n            itemType\n            javaType\n            dataType\n            keyType\n          }\n        }\n      }',
        {'appId': APP, 'appName': APP_NAME,
         'dtoFullName': 'com.seeyon.boot.starter.file.appservice.FileAppService.copy',
         'methodFullName': 'com.seeyon.boot.starter.file.appservice.FileAppService.copy'})
    content = r.get('data', {}).get('data0', {}).get('data', {}).get('content')
    if content:
        save('services/FileAppService.copy.json', content)
        print('  服务方法:', content.get('caption'), '| param.type=', (content.get('parameter') or {}).get('type'))
    else:
        print('服务方法 失败:', json.dumps(r, ensure_ascii=False)[:300])

    # 3. 选项集（枚举列表）
    r = fetch_gql(c, 'udcMicroflowSearchEnumByAppNamePost',
        '      caption\n      customs\n      description\n      enums\n      fullName\n      id\n      md5',
        {'appId': APP, 'appName': APP_NAME})
    content = r.get('data', {}).get('data0', {}).get('data', {}).get('content')
    if content:
        save('enums/list.json', content)
        print('  枚举列表条数:', len(content) if isinstance(content, list) else 'dict')
        # 抓第一个枚举的枚举项
        first_id = content[0]['id'] if isinstance(content, list) and content else None
        if first_id:
            r2 = fetch_gql(c, 'udcMetaDataSelectJavaEnumItemPost',
                '      id\n      name\n      code\n      enumId\n      caption\n      fullName\n      enable',
                {'id': first_id})
            items = r2.get('data', {}).get('data0', {}).get('data', {}).get('content')
            if items:
                save('enums/items_%s.json' % first_id, items)
                print('  枚举项:', len(items) if isinstance(items, list) else 'dict')
    else:
        print('枚举列表 失败:', json.dumps(r, ensure_ascii=False)[:300])

    # 4. 事件列表（应用内）
    r = fetch_gql(c, 'udcMicroflowSearchEventListPost',
        '      fullName\n      caption\n      source\n      dtoType\n      udcApp',
        {'appId': APP, 'appName': APP_NAME})
    content = r.get('data', {}).get('data0', {}).get('data', {}).get('content')
    if content:
        save('events/list.json', content)
        print('  事件列表条数:', len(content) if isinstance(content, list) else 'dict')
    else:
        print('事件列表 失败:', json.dumps(r, ensure_ascii=False)[:300])

    c.close()
    print('DONE')

if __name__ == '__main__':
    main()

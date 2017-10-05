def obj_to_dict(obj):
    '''把Leancloud 获取的对象转成字典。
    注意：如果使用了 include 获取对象的 pointer 字典，需要 pointer 单独进行一次转字典的处理。'''
    # 获取所有 pointer 的字段名。
    pointer_keys = []
    for k, v in obj.dump().items():
        if isinstance(v, dict) and v.get('__type') == 'Pointer':
            pointer_keys.append(k)
    # 重点：处理 pointer。把所有的 pointer dump 一次。
    pointers = {key: obj.get(key).dump() for key in pointer_keys}
    # 处理 object。
    obj = obj.dump()
    # 替换已经处理好的 pointer。
    for k, v in pointers.items():
        obj[k] = v
    return obj

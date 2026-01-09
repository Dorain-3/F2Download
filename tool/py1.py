from decimal import Decimal, getcontext, ROUND_FLOOR
import requests
import json

# 获取运算记录ID
# salesOrdersRowId = ["bceb8e20-9dc8-48f2-bdfe-49c603d82ddf"]
salesOrdersRowId = json.loads(input['salesOrdersRowId'])

headers = {
    'HAP-AppKey': '23ae64ee33f3b8ed',
    'HAP-Sign': 'MDY1NzhlZjg5Y2E4ODBiODZlNjJlZGFjNjdmM2I3NmU0ZjM4OTBjMzY5N2RjNWE4NGQ2MzQ4ZDc5MDE2ODk2NA==',
    'Content-Type': 'application/json'
}
# Decimal精度
getcontext().prec = 10
# 物料库存缓存
matInvCounter = {}
max_list = []
# 根据ID获取销售订单列表
payload1 = json.dumps({

    "viewId": "6936956e2d4e27224dd85ecb",
    "fields": ["670c9097af73df362e8ca9d2", "693693aa2d4e27224dd85e71", "693693aa2d4e27224dd85e72",
               "69378bf82d4e27224dd86217", "69378c062d4e27224dd8621d", "69378dd62d4e27224dd86251",
               "693695a72d4e27224dd85eeb"],
    "filter": {
        "type": "condition",
        "field": "rowid",
        "operator": "in",
        "value": salesOrdersRowId
    },
    "sorts": [
        {
            "field": "69378dd62d4e27224dd86251",
            "direction": "desc"
        }
    ],
})

response1 = requests.request(
    "POST",
    f"https://mes.lqxgroup.com/api/v3/app/worksheets/6936956e2d4e27224dd85eca/rows/list",
    headers=headers, data=payload1
)

salesOrdersList = json.loads(response1.text).get('data').get('rows')

# 循环遍历处理多条订单
for order in salesOrdersList:

    # 订单ID
    orderRowID = order.get('rowId')

    # 订单物料编码
    orderCode = order.get('69378bf82d4e27224dd86217')

    # 订单需求量
    orderQuantity = Decimal(order.get('670c9097af73df362e8ca9d2'))

    # 订单完成量
    reQuantity = Decimal(order.get('693693aa2d4e27224dd85e71'))

    # 订单下发量
    doQuantity = Decimal(order.get('693693aa2d4e27224dd85e72'))

    # 获取库存
    payload2 = json.dumps({

        "viewId": "6929806e41204cda2a36236f",
        "fields": ["657910920e5035c94e7c9eba", "658bdab98c3a8c942f125b6f", "657910920e5035c94e7c9ec1",
                   "657916560e5035c94e7c9f76", "657911b50e5035c94e7c9ee7", "657911b50e5035c94e7c9ee8",
                   "657911b50e5035c94e7c9ee6"],
        "filter": {
            "type": "group",
            "logic": "AND",
            "children": [
                {
                    "type": "condition",
                    "field": "657916560e5035c94e7c9f76",
                    "operator": "gt",
                    "value": "0"
                },
                {
                    "type": "condition",
                    "field": "658bdab98c3a8c942f125b6f",
                    "operator": "eq",
                    "value": [orderCode]
                }
            ]
        },
        "sorts": [
            {
                "field": "657911b50e5035c94e7c9ee6",
                "direction": "desc"
            }
        ],
    })

    response2 = requests.request(
        "POST",
        f"https://mes.lqxgroup.com/api/v3/app/worksheets/6929806e41204cda2a362238/rows/list",
        headers=headers, data=payload2)

    orderInv = json.loads(response2.text).get('data').get('rows')

    # 获取库存量
    orderInvQuantity = Decimal(orderInv[0].get('657916560e5035c94e7c9f76'))

    # 订单产品需求量
    resultOrderQuantity = orderQuantity - orderInvQuantity - reQuantity - doQuantity

    # print(order['693695a72d4e27224dd85eeb'])
    # 订单关联BOM列表
    orderBOMRowIDs = order['693695a72d4e27224dd85eeb']
    # 循环遍历处理多版本BOM
    for orderBOMRowID in orderBOMRowIDs:

        # 订单需求原料
        orderMList = []
        # 订单需求半成品和成品
        orderPList = []

        # 齐套分析
        analysis = {}
        # 结果清单
        result = []

        # 根据BOMID获取记录详情
        response3 = requests.request(
            "GET",
            f"https://mes.lqxgroup.com/api/v3/app/worksheets/69294eb441204cda2a35dff6/rows/{orderBOMRowID}?includeSystemFields=false",
            headers=headers, data="")

        BOMDetail = json.loads(response3.text).get('data')

        # BOM_Version
        BOMVersion = BOMDetail.get('69324ac72d4e27224dd84b40')
        # 获取BOM清单
        BOMRowIDList = BOMDetail.get('69212cf4e536e23b0934b8a6')

        # 根据BOMListID获取BOMList
        payload4 = json.dumps({
            "viewId": "69294eb441204cda2a35e519",
            "fields": ["693248682d4e27224dd84b2e", "69324ae92d4e27224dd84b44", "69212cd7e536e23b0934b889",
                       "69212cd7e536e23b0934b88b", "693242752d4e27224dd84a69", "693242752d4e27224dd84a6a",
                       "693242752d4e27224dd84a6e"],
            "filter": {
                "type": "condition",
                "field": "rowid",
                "operator": "in",
                "value": BOMRowIDList
            },
            "sorts": [
                {
                    "field": "createdAt",
                    "direction": "desc"
                }
            ],
        })

        response4 = requests.request(
            "POST",
            f"https://mes.lqxgroup.com/api/v3/app/worksheets/69294eb441204cda2a35dff5/rows/list",
            headers=headers, data=payload4)

        BOMList = json.loads(response4.text).get('data').get('rows')

        # 获取父项数量
        orderParentBOMQuantity = Decimal(BOMDetail.get('69212aebe536e23b0934b862'))

        for BOM in BOMList:
            if not BOM.get('693242752d4e27224dd84a6e'):
                # 子项编码
                code = BOM.get('69212cd7e536e23b0934b889')
                # 子项用量
                matQuantity = Decimal(BOM.get('69212cd7e536e23b0934b88b'))
                # 固定损耗
                fixedLoss = Decimal(BOM.get('693242752d4e27224dd84a69'))
                # 损耗系数
                attritionCoefficient = Decimal(BOM.get('693242752d4e27224dd84a6a'))
                # 单位产品消耗量
                unitConsumption = matQuantity / orderParentBOMQuantity
                orderMList.append(
                    {
                        'code': code,
                        'BOMCode': orderCode,
                        'quantity': matQuantity,
                        'fixedLoss': fixedLoss,
                        'attritionCoefficient': attritionCoefficient,
                        'sonBOM': BOM.get('693242752d4e27224dd84a6e'),
                        'parentQuantity': orderParentBOMQuantity,
                        'matQuantity': resultOrderQuantity / orderParentBOMQuantity * matQuantity,
                        'unitConsumption': unitConsumption
                    }
                )

                # 增加齐套分析对象
                if code not in analysis:
                    analysis[code] = {
                        'unitConsumption': Decimal('0'),
                        'inventory': Decimal('0'),
                        'maxProduction': Decimal('0'),
                        'missingAmount': Decimal('0'),
                        'consumption': Decimal('0'),
                        'is_bottleneck': None
                    }
                # 累计单耗
                analysis[code]['unitConsumption'] += unitConsumption

            else:
                # 68173de8-4d48-4408-b4d3-ffe78eb62886
                sonBOMID = BOM.get('693242752d4e27224dd84a6e')[0].get('sid')

                response5 = requests.request(
                    "GET",
                    f"https://mes.lqxgroup.com/api/v3/app/worksheets/69294eb441204cda2a35dff6/rows/{sonBOMID}?includeSystemFields=false",
                    headers=headers, data="")

                sonBOMDetail = json.loads(response5.text).get('data')

                sonBOMRowIDList = sonBOMDetail.get('69212cf4e536e23b0934b8a6')
                # 父项数量
                sonParentQuantity = Decimal(sonBOMDetail.get('69212aebe536e23b0934b862'))

                payload6 = json.dumps({
                    "viewId": "69294eb441204cda2a35e519",
                    "fields": ["693248682d4e27224dd84b2e", "69324ae92d4e27224dd84b44", "69212cd7e536e23b0934b889",
                               "69212cd7e536e23b0934b88b", "693242752d4e27224dd84a69", "693242752d4e27224dd84a6a",
                               "693242752d4e27224dd84a6e"],
                    "filter": {
                        "type": "condition",
                        "field": "rowid",
                        "operator": "in",
                        "value": sonBOMRowIDList
                    },
                    "sorts": [
                        {
                            "field": "createdAt",
                            "direction": "desc"
                        }
                    ],
                })

                response6 = requests.request(
                    "POST",
                    f"https://mes.lqxgroup.com/api/v3/app/worksheets/69294eb441204cda2a35dff5/rows/list",
                    headers=headers, data=payload6)

                sonBOMList = json.loads(response6.text).get('data').get('rows')

                # 子项物料编码
                sonCode = sonBOMDetail.get('693243052d4e27224dd84ac5')
                # 子项数量
                sonQuantity = Decimal(BOM.get('69212cd7e536e23b0934b88b'))
                # 固定损耗
                fixedLoss = Decimal(BOM.get('693242752d4e27224dd84a69'))
                # 损耗系数
                attritionCoefficient = Decimal(BOM.get('693242752d4e27224dd84a6a'))
                # 换算系数
                conversionFactor = (sonQuantity + fixedLoss) * (1 + attritionCoefficient) / sonParentQuantity
                # 半成品库存

                payload7 = json.dumps({

                    "viewId": "6929806e41204cda2a36236f",
                    "fields": ["657910920e5035c94e7c9eba", "658bdab98c3a8c942f125b6f", "657910920e5035c94e7c9ec1",
                               "657916560e5035c94e7c9f76", "657911b50e5035c94e7c9ee7", "657911b50e5035c94e7c9ee8",
                               "657911b50e5035c94e7c9ee6"],
                    "filter": {
                        "type": "group",
                        "logic": "AND",
                        "children": [
                            {
                                "type": "condition",
                                "field": "657916560e5035c94e7c9f76",
                                "operator": "gt",
                                "value": "0"
                            },
                            {
                                "type": "condition",
                                "field": "658bdab98c3a8c942f125b6f",
                                "operator": "eq",
                                "value": [sonCode]
                            }
                        ]
                    },
                    "sorts": [
                        {
                            "field": "657911b50e5035c94e7c9ee6",
                            "direction": "desc"
                        }
                    ],
                })

                response7 = requests.request(
                    "POST",
                    f"https://mes.lqxgroup.com/api/v3/app/worksheets/6929806e41204cda2a362238/rows/list",
                    headers=headers, data=payload7)

                productInv = json.loads(response7.text).get('data').get('rows')
                # 半成品库存量
                productInvQuantity = Decimal(productInv[0].get('657916560e5035c94e7c9f76'))
                # 半成品需求量
                productQuantity = resultOrderQuantity / orderParentBOMQuantity * sonQuantity

                orderPList.append(
                    {
                        'code': sonCode,
                        'pCode': orderCode,
                        'sonParentQuantity': sonParentQuantity,
                        'conversionFactor': format(conversionFactor, '.15f').rstrip('0').rstrip('.') if '.' in format(
                            conversionFactor, '.15f') else format(conversionFactor, '.15f'),
                        'sonBOM': BOM.get('693242752d4e27224dd84a6e'),
                        'productQuantity': productQuantity,
                    }
                )

                for item in sonBOMList:
                    if not item.get('693242752d4e27224dd84a6e'):
                        # 子项编码
                        code_ = item.get('69212cd7e536e23b0934b889')
                        # 子项用量
                        matQuantity = Decimal(item.get('69212cd7e536e23b0934b88b'))
                        # 固定损耗
                        fixedLoss = Decimal(item.get('693242752d4e27224dd84a69'))
                        # 损耗系数
                        attritionCoefficient = Decimal(item.get('693242752d4e27224dd84a6a'))
                        # 单位产品消耗量
                        unitConsumption = matQuantity / sonParentQuantity

                        orderMList.append(
                            {
                                'code': code_,
                                'BOMCode': sonCode,
                                'quantity': matQuantity,
                                'fixedLoss': fixedLoss,
                                'attritionCoefficient': attritionCoefficient,
                                'sonBOM': item.get('693242752d4e27224dd84a6e'),
                                'parentQuantity': sonParentQuantity,
                                'matQuantity': productQuantity / sonParentQuantity * matQuantity,
                                'unitConsumption': unitConsumption,
                            }
                        )

                        if code_ not in analysis:
                            analysis[code_] = {
                                'unitConsumption': Decimal('0'),
                                'inventory': Decimal('0'),
                                'maxProduction': Decimal('0'),
                                'missingAmount': Decimal('0'),
                                'consumption': Decimal('0'),
                                'is_bottleneck': None
                            }

                        analysis[code_]['unitConsumption'] += unitConsumption
        # 获取code
        orderPocCodeList = [item['code'] for item in orderPList]
        orderMatCodeList = [item['code'] for item in orderMList]

        # 查询库存
        payload8 = json.dumps({

            "viewId": "6929806e41204cda2a36236f",
            "fields": ["657910920e5035c94e7c9eba", "658bdab98c3a8c942f125b6f", "657910920e5035c94e7c9ec1",
                       "657916560e5035c94e7c9f76", "657911b50e5035c94e7c9ee7", "657911b50e5035c94e7c9ee8",
                       "657911b50e5035c94e7c9ee6"],
            "filter": {
                "type": "group",
                "logic": "AND",
                "children": [
                    {
                        "type": "condition",
                        "field": "657916560e5035c94e7c9f76",
                        "operator": "gt",
                        "value": "0"
                    },
                    {
                        "type": "condition",
                        "field": "658bdab98c3a8c942f125b6f",
                        "operator": "eq",
                        "value": orderMatCodeList
                    }
                ]
            },
            "sorts": [
                {
                    "field": "657911b50e5035c94e7c9ee6",
                    "direction": "desc"
                }
            ],
        })

        response8 = requests.request(
            "POST",
            f"https://mes.lqxgroup.com/api/v3/app/worksheets/6929806e41204cda2a362238/rows/list",
            headers=headers, data=payload8)

        orderMatInvList = json.loads(response8.text).get('data').get('rows')

        # 写入库存缓存
        for item in orderMatInvList:
            # 获取作为键的code
            code = item['658bdab98c3a8c942f125b6f']
            # 缓存中没有则新增
            if not matInvCounter.get(code, None):
                quantity = Decimal(item['657916560e5035c94e7c9f76'])
                matInvCounter[code] = quantity

        # print(analysis)

        # 读取缓存
        for code in orderMatCodeList:
            matInv = matInvCounter[code]
            analysis[code]['inventory'] = matInv

        # 最大可生产量设为需求量
        maxProduction = resultOrderQuantity

        for code, data in analysis.items():

            if data['unitConsumption'] > 0:

                # 计算最大可生产量，向下取整
                material_max = ((data['inventory'] / data['unitConsumption'])
                                .quantize(Decimal('1.'), rounding=ROUND_FLOOR))

                data['maxProduction'] = material_max

                if material_max < maxProduction:
                    # 计算缺差量
                    data['missingAmount'] = (resultOrderQuantity - material_max) * data['unitConsumption']
                    data['is_bottleneck'] = True
                else:
                    data['maxProduction'] = resultOrderQuantity
                    data['is_bottleneck'] = False

            else:
                data['maxProduction'] = resultOrderQuantity
                data['is_bottleneck'] = False

        # 根据最大可生产量从小到大排序
        sorted_materials = sorted(analysis.items(), key=lambda x: x[1]['maxProduction'])
        resultMaxProduction = sorted_materials[0][1]['maxProduction']

        # 原料计算结果
        for code, data in analysis.items():
            consumption = resultMaxProduction * data['unitConsumption']
            result.append(
                {
                    "fields": [
                        {
                            "id": "order",
                            "value": orderRowID,
                        },
                        {
                            "id": "BOM",
                            "value": orderBOMRowID,
                        },
                        {
                            "id": "BOMVersion",
                            "value": BOMVersion,
                        },
                        {
                            "id": "materialCode",
                            "value": code
                        },
                        {
                            "id": "quantity",
                            "value": str(consumption)
                        },
                        {
                            "id": "missingAmount",
                            "value": str(data['missingAmount'])
                        },
                        {
                            "id": "maxProduction",
                            "value": str(resultMaxProduction)
                        }],
                }
            )
            analysis[code]['consumption'] = consumption
            matInvCounter[code] -= consumption

        # 回写结果
        url = f"https://mes.lqxgroup.com/api/v3/app/worksheets/693a20062d4e27224dd86de8/rows/batch"

        payload9 = json.dumps(
            {
                "rows": result,
                "triggerWorkflow": True
            }
        )

        response9 = requests.request("POST", url, headers=headers, data=payload9)

        max_list.append(
            {
                'orderRowID': orderRowID,
                'orderCode': orderCode,
                'BOMVersion': BOMVersion,
                'maxProduction': resultMaxProduction,
            }
        )

        url = f"https://mes.lqxgroup.com/api/v3/app/worksheets/693a1c6f2d4e27224dd86db4/rows"

        payload10 = json.dumps(
            {
                "triggerWorkflow": True,
                "fields": [
                    {
                        "id": "orderRowID",
                        "value": orderRowID
                    },
                    {
                        "id": "BOMVersion",
                        "value": BOMVersion,
                    },
                    {
                        "id": "maxProduction",
                        "value": str(resultMaxProduction)
                    }
                ]
            }
        )

        response10 = requests.request("POST", url, headers=headers, data=payload10)

        resultOrderQuantity -= resultMaxProduction

        if resultOrderQuantity <= 0:
            break

output = {'msg': max_list}

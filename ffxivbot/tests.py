from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from ffxivbot.handlers.QQUtils import search_item, search_xivapi_items


class XIVAPISearchTests(SimpleTestCase):
    @patch("ffxivbot.handlers.QQUtils.requests.get")
    def test_v2_search_response_is_normalized(self, get):
        response = Mock()
        response.json.return_value = {
            "next": None,
            "results": [{
                "row_id": 5179,
                "fields": {
                    "Name": "紫水晶",
                    "Icon": {"path": "ui/icon/021000/021288.tex"},
                },
            }],
        }
        get.return_value = response

        result = search_xivapi_items("紫水晶", "cn")

        self.assertEqual(
            result,
            {
                "items": [{
                    "name": "紫水晶",
                    "id": 5179,
                    "icon_path": "ui/icon/021000/021288.tex",
                }],
                "has_more": False,
            },
        )

    @patch("ffxivbot.handlers.QQUtils.search_xivapi_items")
    def test_multiple_results_build_share_card_from_v2_fields(self, search):
        search.return_value = {
            "items": [
                {
                    "name": "紫水晶",
                    "id": 5179,
                    "icon_path": "ui/icon/021000/021288.tex",
                },
                {
                    "name": "水晶草",
                    "id": 5552,
                    "icon_path": "ui/icon/022000/022682.tex",
                },
            ],
            "has_more": False,
        }

        result = search_item("水晶", "https://ff14.huijiwiki.com")

        self.assertEqual(result["title"], "水晶 的搜索结果")
        self.assertEqual(result["content"], "在最终幻想XIV中找到了 2 个物品")
        self.assertEqual(
            result["image"],
            "https://v2.xivapi.com/api/asset"
            "?path=ui%2Ficon%2F021000%2F021288.tex&format=png",
        )



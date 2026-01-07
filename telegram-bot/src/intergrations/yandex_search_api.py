from typing import Any, Literal

import asyncio
import base64
import json
import re
import time
import xml.etree.ElementTree as ET  # noqa: S405

import aiohttp

from ..settings import settings

BASE_URL = "https://searchapi.api.cloud.yandex.net/v2/"
OPERATIONS_URL = "https://operation.api.cloud.yandex.net/operations/"

FamilyMode = Literal[
    "FAMILY_MODE_NONE",
    "FAMILY_MODE_MODERATE",
    "FAMILY_MODE_STRICT"
]


class YandexSearchAPIError(Exception):
    pass


class YandexSearchTimeoutError(YandexSearchAPIError):
    pass


def _build_payload(
        query: str, family_mode: FamilyMode = "FAMILY_MODE_NONE", page: int | None = None
) -> dict[str, Any]:
    return {
        "query": {
            "searchType": "SEARCH_TYPE_RU",
            "queryText": query,
            "familyMode": family_mode,
            "page": page if page is not None else 0,
            "fixTypoMode": "FIX_TYPO_MODE_ON"
        },
        "l10n": "LOCALIZATION_RU",
        "responseFormat": "FORMAT_XML"
    }


def _clean_xml_tags(text: str) -> str:
    """Очищает текст от XML тегов и лишних пробелов"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    html_entities = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&apos;": "'",
        "&nbsp;": " ",
    }
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    return " ".join(text.split())


def _extract_element_text(element: ET.Element) -> str:
    if element is None:
        return ""
    texts = []
    if element.text:
        texts.append(element.text.strip())
    for child in element:
        if child.text:
            texts.append(child.text.strip())
        if child.tail and child.tail.strip():
            texts.append(child.tail.strip())
    return " ".join(" ".join(texts).split())


def _parse_xml_response(xml_content: str) -> list[dict[str, Any]]:
    results = []
    root = ET.fromstring(xml_content)  # noqa: S314
    groups = root.findall(".//grouping/group")
    for group in groups:
        category = group.find("categ")
        category_name = category.get("name") if category is not None else ""
        docs = group.findall("doc")
        for doc in docs:
            result = {
                "url": doc.find("url").text if doc.find("url") is not None else "",
                "domain": doc.find("domain").text if doc.find("domain") is not None else "",
                "title": _extract_element_text(doc.find("title")),
                "snippet": _extract_element_text(doc.find("passages/passage")),
                "category": category_name,
                "modtime": doc.find("modtime").text if doc.find("modtime") is not None else "",
                "size": doc.find("size").text if doc.find("size") is not None else "",
                "charset": doc.find("charset").text if doc.find("charset") is not None else "",
            }
            extended = doc.find("properties/extended-text")
            if extended is not None and extended.text:
                result["extended_text"] = _clean_xml_tags(extended.text)
            passages = doc.find("passages")
            if passages is not None:
                passages_texts = [
                    _extract_element_text(passage)
                    for passage in passages.findall("passage")
                    if _extract_element_text(passage)
                ]
                result["passages"] = passages_texts
            results.append(result)
    return results


async def search(query: str) -> list[dict[str, Any]]:
    headers = {
        "Authorization": f"Api-Key {settings.yandexcloud.apikey}",
        "Content-Type": "application/json",
    }
    payload = _build_payload(query)
    async with aiohttp.ClientSession(base_url=BASE_URL) as session, session.post(
        url="web/search", headers=headers, json=payload
    ) as response:
        data = await response.text()
        xml_content = base64.b64decode(json.loads(data)["rawData"]).decode("utf-8")
        return _parse_xml_response(xml_content)


async def _check_operation_status(operation_id: str) -> dict[str, Any]:
    headers = {"Authorization": f"Api-Key {settings.yandexcloud.apikey}"}
    async with aiohttp.ClientSession(base_url=OPERATIONS_URL) as session, session.get(
        url=f"{operation_id}", headers=headers
    ) as response:
        return await response.json()


async def _get_search_results(operation_id: str) -> list[dict[str, Any]]:
    status = await _check_operation_status(operation_id)
    if not status.get("done", False):
        raise YandexSearchAPIError("No response data available")
    if "response" not in status or "rawData" not in status["response"]:
        raise YandexSearchAPIError("No response data available")
    xml_content = base64.b64decode(status["response"]["rawData"]).decode("utf-8")
    return _parse_xml_response(xml_content)


async def search_async(query: str, interval: int = 1, max_wait: int = 300) -> list[dict[str, Any]]:
    headers = {
        "Authorization": f"Api-Key {settings.yandexcloud.apikey}",
        "Content-Type": "application/json",
    }
    payload = _build_payload(query)
    async with aiohttp.ClientSession(base_url=BASE_URL) as session, session.post(
            url="web/searchAsync", headers=headers, json=payload
    ) as response:
        data = await response.json()
        operation_id = data["id"]

    start_time = time.time()
    while time.time() - start_time < max_wait:
        status = await _check_operation_status(operation_id)
        if status.get("done", False):
            return await _get_search_results(operation_id)
        await asyncio.sleep(interval)
    raise YandexSearchTimeoutError(f"Timeout waiting for search results after {max_wait} seconds")

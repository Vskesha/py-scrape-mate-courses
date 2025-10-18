import time
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

URL = "https://mate.academy/"
REQUEST_DELAY = 0.5
TIMEOUT = 10


session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
})


@dataclass
class Module:
    name: str
    topics: list[str]


@dataclass
class Course:
    name: str
    short_description: str
    duration: str
    modules: list[Module]


def fetch_page(page_url: str) -> bytes | None:
    print(f"Fetching page: {page_url}")
    try:
        response = session.get(page_url, timeout=TIMEOUT)
        response.raise_for_status()
        time.sleep(REQUEST_DELAY)
        return response.content
    except requests.RequestException as err:
        print(f"Failed to fetch {page_url}: {err}")
        return None


def parse_single_module(module_element: Tag) -> Module:
    name = module_element.select_one(
        "p.CourseModulesList_topicName__7vxtk"
    ).get_text()

    topics = []
    topic_list = module_element.select_one(
        "ul.CourseModulesList_topicsList__NJTKz"
    )
    if topic_list:
        topics = [
            topic_element.get_text(strip=True)
            for topic_element in topic_list.select(
                "li.CourseModulesList_topicItem__8wNTG"
            )
        ]

    return Module(name=name, topics=topics)


def parse_course_modules(page: bytes) -> list[Module]:
    soup = BeautifulSoup(page, "html.parser")

    module_list = soup.select_one("ul.CourseModulesList_modulesList__C86yL")
    if not module_list:
        return []

    modules = [
        parse_single_module(element)
        for element in module_list.select("li.color-dark-blue")
    ]
    return modules


def parse_single_course(element: Tag) -> Course:
    name = element.select_one(
        "h3.ProfessionCard_title__m7uno"
    ).get_text(strip=True)
    short_description = element.select_one(
        "p.ProfessionCard_description__K8weo"
    ).get_text(strip=True)
    duration = element.select_one(
        "p.ProfessionCard_duration__13PwX"
    ).get_text(strip=True)
    course_info_page = element.get("href")

    modules = []
    if course_info_page:
        couse_info_link = urljoin(URL, course_info_page)
        page = fetch_page(couse_info_link)
        modules = parse_course_modules(page)

    return Course(
        name=name,
        short_description=short_description,
        duration=duration,
        modules=modules,
    )


def parse_page(page: bytes) -> list[Course]:
    result = []

    soup = BeautifulSoup(page, "html.parser")

    for element in soup.select("a.ProfessionCard_cardWrapper__BCg0O"):
        result.append(parse_single_course(element))

    return result


def get_all_courses() -> list[Course]:
    courses: list[Course] = []

    page = fetch_page(URL)
    courses.extend(parse_page(page))

    return courses


if __name__ == "__main__":
    for course in get_all_courses():
        print(course.name)
        print(f"    description: {course.short_description}")
        print(f"    duration: {course.duration}")
        print("    modules:")
        for module in course.modules:
            print(f"        {module.name}")
            print(f"            topics: {', '.join(module.topics)}")

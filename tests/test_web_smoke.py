from django.test import Client


def test_home_page_renders() -> None:
    response = Client().get("/")

    assert response.status_code == 200
    assert b"Solve Shapez 2 production chains" in response.content
    assert b"Quick Solver" in response.content
    assert b"flowbite.min.js" in response.content


def test_gallery_page_renders() -> None:
    response = Client().get("/gallery/")

    assert response.status_code == 200
    assert b"Screenshots" in response.content
    assert b"Factory templates" in response.content
    assert b"Open original" in response.content
    assert b"gallery-viewer" in response.content
    assert b"gallery-viewer-prev" in response.content
    assert b"gallery-viewer-next" in response.content
    assert b"gallery-viewer.js" in response.content


def test_demo_page_renders() -> None:
    response = Client().get("/demo/")

    assert response.status_code == 200
    assert b"Example production plan" in response.content
    assert b"How it works" in response.content


def test_home_nav_links_to_split_pages() -> None:
    response = Client().get("/")

    assert response.status_code == 200
    assert b'href="/gallery/"' in response.content
    assert b'href="/demo/"' in response.content

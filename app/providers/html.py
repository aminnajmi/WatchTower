from bs4 import BeautifulSoup


def tables(html: str) -> list[list[list[str]]]:
    soup = BeautifulSoup(html, "html.parser")
    result = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if rows:
            result.append(rows)
    return result

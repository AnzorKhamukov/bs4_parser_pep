import logging
import re
import requests_cache

from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin

from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag
from constants import BASE_DIR, MAIN_DOC_URL, MAIN_PEP_URL, EXPECTED_STATUS


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    main_section = find_tag(soup, 'section', {'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(
        main_section, 'div', {'class': 'toctree-wrapper compound'}
        )
    sections_by_python = div_with_ul.find_all('li', {'class': 'toctree-l1'})

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python, desc='Сбор ссылок на обновления'):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

        response_for_version = get_response(session, version_link)
        if response_for_version is None:
            continue

        soup_for_version = BeautifulSoup(
            response_for_version.text, features='lxml'
        )

        h1 = find_tag(soup_for_version, 'h1')
        dl = find_tag(soup_for_version, 'dl')
        dl_text = dl.text.replace('\n', ' ')

        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    sidebar = find_tag(soup, 'div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:

        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Список с версиями Python не найден.')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)

        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''

        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')

    response = get_response(session, downloads_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    table_tag = find_tag(soup, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)

    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename

    response = session.get(archive_url)
    logging.info('Началась загрузка архива.')
    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    counter = {
        'Accepted': 0,
        'Active': 0,
        'Deferred': 0,
        'Draft': 0,
        'Final': 0,
        'Provisional': 0,
        'Rejected': 0,
        'Superseded': 0,
        'Withdrawn': 0
    }

    response = get_response(session, MAIN_PEP_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')

    section_tag = find_tag(soup, 'section', {'id': 'numerical-index'})
    tr_tags = section_tag.find_all('tr')

    for tr_tag in tqdm(tr_tags[1:], desc='Подсчет статусов PEP'):
        pep_link = tr_tag.td.find_next_sibling().find('a')['href']
        pep_url = urljoin(MAIN_PEP_URL, pep_link)

        response_for_pep = get_response(session, pep_url)
        if response_for_pep is None:
            return

        soup_for_pep = BeautifulSoup(response_for_pep.text, features='lxml')

        dl_tag = find_tag(soup_for_pep, 'dl')
        dt_tag = find_tag(
            dl_tag, lambda tag: tag.name == 'dt' and 'Status' in tag.text
        )
        pep_status = dt_tag.find_next_sibling().text

        counter[pep_status] = counter.get(pep_status, 0) + 1

        try:
            pep_list_status = EXPECTED_STATUS[tr_tag.td.text[1:]]
        except KeyError:
            logging.info(f'Неизвестный статус у PEP: '
                         f'"{pep_url}".'
                         f'Статус в карточке: {pep_status}, '
                         f'код статуса в списке PEP: {tr_tag.td.text[1:]}.'
                         )
            pep_list_status = [pep_status, ]

        if pep_status not in pep_list_status:
            logging.info(f'Несовпадающие статусы у PEP: '
                         f'"{pep_url}".'
                         f'Статус в карточке: {pep_status}, '
                         f'ожидаемые статусы: {pep_list_status}.'
                         )

        results = [('Статус', 'Количество')]
        total = 0
        for key, value in counter.items():
            results.append((key, value))
            total += value
        results.append(('Total:', total))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()

    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)

    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()

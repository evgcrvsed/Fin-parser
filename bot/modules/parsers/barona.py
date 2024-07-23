import requests
import dateutil.parser as date_parser
from modules.DataBase import DataBase
from .base import ParserBase


class Barona(ParserBase):

    def __init__(self, url='https://barona.fi/api/job-postings'):
        super().__init__()
        self.url = url
        self.orm = DataBase('data/database.db')

    async def parse(self, keyword=None, location=None) -> None:
        await self.orm.clear_old_records(table=Barona.__name__)
        total_pages = await self.get_total_pages()
        for page in range(1, total_pages + 1):

            pre_setted_parameters = {'page': page, 'sort': 'relevance'}
            setted_parameters = {}

            if keyword:
                setted_parameters.update({'keyword': keyword})

            if location:
                setted_parameters.update({'location': location})

            response = requests.get(
                url=self.url,
                params={
                    **pre_setted_parameters,
                    **setted_parameters
                }
            ).json()

            if not response:
                return

            for index, vacancy in enumerate(response.get('jobPostings')):
                posted = date_parser.isoparse(vacancy.get('updated')).date()
                slug = vacancy.get('slug')
                description = vacancy.get('description').get('leadText')
                employment_types = vacancy.get('employmentTypes')
                language = vacancy.get('language')
                title = vacancy.get('name')
                deadline = date_parser.isoparse(vacancy.get('validThrough')).date()
                locations = vacancy.get('location')

                await self.orm.save_vacancy(
                    table=Barona.__name__,
                    posted_at=posted,
                    slug=slug,
                    title=title,
                    locations=locations,
                    deadline=deadline,
                    description=description,
                    employment_types=employment_types,
                    language=language
                )

    async def get_total_pages(self) -> int:
        response = requests.get(
            url=self.url
        ).json()

        if response:
            return int(response.get('paging').get('pages'))
        return 1


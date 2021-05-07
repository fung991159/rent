import json
import re

import scrapy
from scrapy.shell import inspect_response
from scrapy import Selector


class HseSpider(scrapy.Spider):
    name = 'hse'
    allowed_domains = ['28hse.com']
    start_urls = ['https://www.28hse.com/en/rent']
    fetch_next_page = None
    page = 1
    form_data = {'form_data': 'buyRent=rent&sortBy=&plan_id=0&plan_id_more_search_open=&page=1&location=hk&district_ids=0&district_group_ids=10&cat_ids=&house_main_type_ids=5&house_other_main_type_ids=&house_other_main_type_id_fix=0&house_other_sub_main_type_ids=&price_selection_index=0&price_low=0&price_high=0&rentprice_selection_index=0&rentprice_low=0&rentprice_high=0&area_selection_index=1&area_build_sales=build&area_low=0&area_high=&noOfRoom=&estate_age_low=0&estate_age_high=0&house_search_tag_ids=&myfav=&myvisited=&property_ids=&is_return_newmenu=0&is_grid_mode=0&landlordAgency=&estate_age_index=&temp_house_search_tag_ids=&search_words_value=&search_words_thing=&search_words=&sortByBuy=&sortByRent='}

    def parse(self, response):
        """send form reqeust with desired criteria"""
        yield scrapy.FormRequest(
            url='https://www.28hse.com/en/property/dosearch',
            formdata=self.form_data,
            callback=self.parse_properties
        )

    def parse_properties(self, response):
        """fetch properties id in page if any,
        if there is no next page (regex match none), then the scraper would stop itself"""
        self.fetch_next_page = False # in the new page assume there is no item
        out = json.loads(response.text)['data']['results']['resultContentHtml']
        url_regex = re.compile(r".*attr1=\'(\d*)\'.* target=\"_blank\">$")
        for line in out.splitlines():
            if m:=url_regex.match(line):
                fetch_next_page = True
                properties_id = m.group(1)
                yield scrapy.FormRequest(
                    url=f'https://www.28hse.com/en/rent/residential/property-{properties_id}',
                    callback=self.parse_property_info
                )

        # get next page
        if fetch_next_page:
            self.form_data['form_data'] = self.form_data['form_data'].replace(f'&page={self.page}&location',
                                                                              f'&page={self.page+1}&location')
            self.page += 1
            yield scrapy.FormRequest(
            url='https://www.28hse.com/en/property/dosearch',
            formdata=self.form_data,
            callback=self.parse_properties
        )

    def parse_property_info(self, response):
        """parse property page infos"""

        def xpath_parser(x_path, getall=False):
            """parse all items extracted by x_path, with comma as seperator
            ignore newline character within a item as well as standalone newline item

            Args:
                html_response ([type]): [description]
                x_path ([type]): [description]
                getall(str): scrapy getall() instead of the default get()

            Returns:
                [type]: [description]
            """
            try:
                xpath_parser.response
            except AttributeError:
                raise ('response not attached to function')

            sel = Selector(text=xpath_parser.response.text)
            getter = 'getall' if getall else 'get'
            output = getattr(sel.xpath(x_path), getter)()
            if isinstance(output, str):
                output = output.replace('\n', '')
            else:
                exclude = {'\n', ' '}
                output = ', '.join([i.strip() for i in output if i not in exclude])
            return output

        output = {}
        from scrapy import Selector
        sel = Selector(text=response.text)

        output['url'] = response.url
        xpath_parser.response = response
        output['title'] = xpath_parser("//h3/following-sibling::div//div[@class='header']/text()")
        output['desc'] = xpath_parser("//div[@id='desc_normal']/p/text()")
        output['tag'] = xpath_parser("//div[contains(@class,'labels')]//text()", getall=True)

        # table content
        # there is no consistent html hierachy here, so fetch everything in table
        # there could be nested table here, so the xpath selector need to be precise
        desc_col_xpath = "//table//tr[{}]/td[{}]//text()"
        value_col_xpath = "//table//tr[{}]/td[{}]/div//text()"

        i=2  # first row in the table is "qr_code", which I don't need
        while sel.xpath(desc_col_xpath.format(i, 1)):
            row_desc = xpath_parser(desc_col_xpath.format(i, 1))
            row_desc = row_desc.replace(' ', '_').lower()
            row_val = xpath_parser(value_col_xpath.format(i, 2), getall=True)
            output[row_desc] = row_val
            i+=1

        yield output

#TODO: class attr "form_data" should be parametized to have a handle of what to fetch


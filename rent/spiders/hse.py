import scrapy
import json
from pprint import pprint
from scrapy.http import HtmlResponse
import re

from scrapy.shell import inspect_response

class HseSpider(scrapy.Spider):
    name = 'hse'
    allowed_domains = ['28hse.com']
    start_urls = ['https://www.28hse.com/en/rent']
    base = 'https://www.28hse.com/en/rent'

    def parse(self, response):
        form_data = {'form_data': 'buyRent=rent&sortBy=&plan_id=0&plan_id_more_search_open=&page=1&location=hk&district_ids=0&district_group_ids=10&cat_ids=&house_main_type_ids=5&house_other_main_type_ids=&house_other_main_type_id_fix=0&house_other_sub_main_type_ids=&price_selection_index=0&price_low=0&price_high=0&rentprice_selection_index=0&rentprice_low=0&rentprice_high=0&area_selection_index=1&area_build_sales=build&area_low=0&area_high=300&noOfRoom=&estate_age_low=0&estate_age_high=0&house_search_tag_ids=&myfav=&myvisited=&property_ids=&is_return_newmenu=0&is_grid_mode=0&landlordAgency=&estate_age_index=&temp_house_search_tag_ids=&search_words_value=&search_words_thing=&search_words=&sortByBuy=&sortByRent='}
        yield scrapy.FormRequest(
            url='https://www.28hse.com/en/property/dosearch',
            formdata=form_data,
            callback=self.parse_properties
        )

# https://www.28hse.com/en/rent/residential/property-989755\
    def parse_properties(self, response):
        # print(type(response.text))
        # inspect_response(response, self)
        out = json.loads(response.text)['data']['results']['resultContentHtml']

        # fetch properties_id
        output = []
        for o in out.splitlines():
            if m:=re.match(r".*href.*attr1=\'(\d*)\'.*", o):
                # print(o)
                properties_id = m.group(1)
                output.append(properties_id)
        yield {'property_id': output}
   

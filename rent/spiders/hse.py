import json
import re
from pprint import pprint

import scrapy
from scrapy.shell import inspect_response
from scrapy import Selector


def xpath_parser(x_path):
    """parse all items extracted by x_path, with comma as seperator
    ignore newline character within a item as well as standalone newline item

    Args:
        html_response ([type]): [description]
        x_path ([type]): [description]

    Returns:
        [type]: [description]
    """    
    if not xpath_parser.response:
        raise ValueError('response not attached to function')

    sel = Selector(text=xpath_parser.response.text)
    elements = sel.xpath(x_path).getall()
    output = ', '.join([e.strip() for e in elements if e != '\n'])
    return output

class HseSpider(scrapy.Spider):
    name = 'hse'
    allowed_domains = ['28hse.com']
    start_urls = ['https://www.28hse.com/en/rent']
    base = 'https://www.28hse.com/en/rent'

    def parse(self, response):
        """send form reqeust with desired criteria"""
        form_data = {'form_data': 'buyRent=rent&sortBy=&plan_id=0&plan_id_more_search_open=&page=1&location=hk&district_ids=0&district_group_ids=10&cat_ids=&house_main_type_ids=5&house_other_main_type_ids=&house_other_main_type_id_fix=0&house_other_sub_main_type_ids=&price_selection_index=0&price_low=0&price_high=0&rentprice_selection_index=0&rentprice_low=0&rentprice_high=0&area_selection_index=1&area_build_sales=build&area_low=0&area_high=300&noOfRoom=&estate_age_low=0&estate_age_high=0&house_search_tag_ids=&myfav=&myvisited=&property_ids=&is_return_newmenu=0&is_grid_mode=0&landlordAgency=&estate_age_index=&temp_house_search_tag_ids=&search_words_value=&search_words_thing=&search_words=&sortByBuy=&sortByRent='}
        yield scrapy.FormRequest(
            url='https://www.28hse.com/en/property/dosearch',
            formdata=form_data,
            callback=self.parse_properties
        )

    def parse_properties(self, response):
        """fetch properties id in page"""
        out = json.loads(response.text)['data']['results']['resultContentHtml']
        for line in out.splitlines():
            if m:=re.match(r".*attr1=\'(\d*)\'.* target=\"_blank\">$", line):
                # print(o)
                properties_id = m.group(1)
                yield scrapy.FormRequest(
                    url=f'https://www.28hse.com/en/rent/residential/property-{properties_id}',
                    callback=self.parse_property_info
                )

    def parse_property_info(self, response):
        """parse
        """
        output = {}
        from scrapy import Selector        
        sel = Selector(text=response.text)

        output['url'] = response.url
        xpath_parser.response = response
        output['title'] = xpath_parser("//h3/following-sibling::div//div[@class='header']/text()")
        output['desc'] = xpath_parser("//div[@id='desc_normal']/p/text()")
        output['tag'] = xpath_parser("//div[contains(@class,'labels')]//text()")

        # table content
        # there is no consistent html hierachy here, so fetch everythign in table
        tr_xpath = "//table//tr[{}]/td[{}]//text()"
        i=1
        while sel.xpath(tr_xpath.format(i, 1)):
            row_desc = sel.xpath(tr_xpath.format(i, 1)).getall()
            row_desc = ', '.join([i.strip() for i in row_desc if i != '\n'])
            row_desc = row_desc.replace(' ', '_').lower()
            row_val = sel.xpath(tr_xpath.format(i, 2)).getall()
            row_val = ', '.join([i.strip() for i in row_val if i != '\n'])
            # print(row_desc, row_val, sep='\n')
            output[row_desc] = row_val
            i+=1

        # monthly rental
        # rent_amt_xpath = "//td[contains(text(), 'Monthly Rental')]/following-sibling::td/div/text()"
        # rent_amt = sel.xpath(rent_amt_xpath).re(r"Lease \$(.*)")[0]
        # rent_amt = int(rent_amt.replace(',', ''))

        # inspect_response(response, self)
        yield output
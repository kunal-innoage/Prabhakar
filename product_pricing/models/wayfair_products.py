from odoo import fields, models,api
import logging

import requests
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)


class WayfairProduct(models.Model):
    _name = "wayfair.product"
    _description = "Wayfair Product"
    _rec_name="supplier_part_number"

    supplier_part_number=fields.Char("SKU")
    brand_catalog=fields.Char("Brand Catalog")
    retail_price=fields.Float("Retail Price")
    status=fields.Char("Status")
    link=fields.Char("Link")
    wayfair_uk=fields.Char("Waifair UK" , invisible='0')
    wayfair_de=fields.Char("Wayfair DE" , invisible='0')
    wayfair_shop_id = fields.Many2one("wayfair.shops","Wayfair Shop")
    product_id = fields.Many2one("product.product","Wayfair Product")
    recommended_retail_price = fields.Float("Recommended Retail Price" , invisible = True)
    # product_status = fields.Selection([('active','Active'),('inactive','Inactive'),('unavailable', 'Out Of Stock'),('price_unavailable', 'Price Not Found'),('link_absent' , 'URL Missing') ] ,"Product Status")
    # last_updated_on = fields.Datetime("Last Updated on" , readonly = True)
   

    # currency_id = fields.Many2one("wayfair.shops","Currency")
    is_odoo_product = fields.Boolean("Is Odoo Product")
    # currency_difference = fields.Float("Currency")

    ###################
    # product listing #
    ###################


    @api.model_create_multi
    def create(self, vals):
        res = super(WayfairProduct, self).create(vals)

        if res._context.get('import_file'):
            # difference = self.env['wayfair.shops'].browse(['])
            for product in res:
            #     if product.brand_catalog == "Wayfair UK":
                    
            #         product.retail_price = round((float(product.retail_price)*difference) , 2)
                wayfair_shop_id= self.env['wayfair.shops'].search([('id','=',res._context.get('active_id'))])
                product.wayfair_shop_id = wayfair_shop_id.id
                if product.wayfair_shop_id.difference:
                    product.retail_price = (product.wayfair_shop_id.difference)*(product.retail_price)


                product_id= self.env['product.product'].search([('default_code','=',product.supplier_part_number)])
                if product_id:
                    product.product_id = product_id
                    product.is_odoo_product = True 
                    # _logger.info(">>>>>>>>>PRE............  %r ,...........",len(product_id))
 
                if not product_id :
                    product.unlink()

                    
                wayfair_shop_id =self.env['wayfair.shops'].search([('id','=',res._context.get('active_id'))])
                product.wayfair_shop_id = wayfair_shop_id.id

                
                    # _logger.info(">>>>>>>>>PRE>>>>>>>............  %r ,...........",(product.retail_price))

                # else:
                #     pass
        return res
    
    #############################
    # Get Product Price Updates #
    #############################

    # @api.depends('name')
    # def update_product_price_via_web_scrap(self):
        # for product in self:
        #     # product.last_updated_on = fields.Datetime.now()
        #     if product.link:

        #         response = False
        #         # url =  "https://"+ product.link
        #         link = product.link
        #         headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'}


        #         try:
        #             _logger.info("......... Price Check Call - %r  %r ...........", link, headers)
        #             response = requests.get(link , headers)

        #             if response.status_code == 200:
        #                 product.product_status = "active"
        #                 self.process_product_page_data_for_price_wayfair(product , response)
                        
        #             else:
        #                 product.product_status = "inactive"
        #                 _logger.info(".......... Product URL Inactive with status code %r for product - %r.........!!!!!!!!",response.status_code, product.supplier_part_number)

        #         except Exception as e:
        #             _logger.info(".......Error while checking product url - %r",e)

        #     else:
        #         product.product_status = "link_absent"
        #         _logger.info("............Missing Url for -  %r ,......!!!!!!!!!",product.supplier_part_number)
        #         pass
        # pass
    
    ##########################
    # Process Product Prices #
    ##########################

    # def process_product_page_data_for_price_wayfair(self , product , response):

        # soup = BeautifulSoup(response.content , 'html.parser')
        # _logger.info("````````%r```````````", soup)
        # out_of_stock_product = soup.find('div', {'class':'a-size-medium a-color-price'})

        # if out_of_stock_product is not None:

        #     product.product_status = 'unavailable'
        #     _logger.info("............ Product Stock Unavailable -  %r ,........",product.supplier_part_number)

        # else:

        #     # product.product_status = 'active'
        #     price_element = soup.find('div', {'class': 'oakhm64z_6101 oakhm627_6101 oakhm6y5_6101 oakhm610g_6101 oakhm6aj_6101'})
        #     _logger.info("............ccccccccccccccccccccccccc.......",price_element)
        #     if price_element is not None:

        #         product.product_status = 'active'
        #         product.retail_price = price_element.text.strip()
        #         _logger.info("............ Updated Product %r's Price -  %r ,........", product.supplier_part_number, product.retail_price)

        #     else:
            
        #         product.product_status = 'price_unavailable'
        #         _logger.info("............ Product Price Unavailable -  %r ,......!!!!!!!!!",product.supplier_part_number)
        # pass



    



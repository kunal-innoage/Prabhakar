from odoo import fields, models, api
import logging
import requests
from bs4 import BeautifulSoup

_logger = logging.getLogger(__name__)

class AmazonSKU(models.Model):
    _name = "amazon.sku"
    _description = "Amazon SKU"
    _rec_name="vendor_sku"

    vendor_sku=fields.Char("Vendor SKU")
    list_price_currency=fields.Char("List Price Currency")
    list_price_with_tax=fields.Float("List Price with Tax")
    cost_price=fields.Char("Cost Price")
    cost_price_currency=fields.Char("Cost Price Currency")
    amazon_shop_id = fields.Many2one("amazon.shops", "Amazon Shop")
    product_url=fields.Char("Product URL")
    product_id = fields.Many2one("product.product","Amazon Product")
    product_status = fields.Selection([('active','Active URLs'),('inactive', 'Inactive URLs'),('unavailable', 'Out Of Stock'),('price_unavailable', 'Price Not Found')] ,"Product Status")
    last_updated_on = fields.Datetime("Last Updated on" , readonly = True)
    merchant_suggested_asin=fields.Char("Merchant Suggested Asin")
    # is_odoo_product = fields.Boolean("Is Odoo Product")
    

    ###################
    # product listing #
    ###################
    
    @api.model_create_multi
    def create(self, vals):
        res = super(AmazonSKU, self).create(vals)
        if res._context.get('import_file'):
            for product in res:
                # product_id = self.env['product.product'].search([('default_code','=',product.vendor_sku)])
                # if product_id:
                #     product.product_id = product_id
                #     product.is_odoo_product  = True
                # if not product_id:
                #     product.unlink()

                amazon_shop_id =self.env['amazon.shops'].search([('id', '=', res._context.get('active_id'))])
                product.amazon_shop_id = amazon_shop_id.id
                if product.amazon_shop_id.url:
                    # _logger.info("............  %r ,.....%r......",product.merchant_suggested_asin, product.amazon_shop_id.url)
                    product.product_url = product.amazon_shop_id.url + product.merchant_suggested_asin
        return res
    

    #############################
    # Get Product Price Updates #
    #############################

    @api.depends('name')
    def update_product_status_and_price(self):

        for product in self:
            product.last_updated_on = fields.Datetime.now()
            if product.product_url:


                response = False
                url = product.product_url
                header = {"User-Agent":"Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.0.0 Mobile Safari/537.36", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
                # header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
                # HEADERS = ({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36', 'Accept-Language': 'en-US, en;q=0.5'})
                
                try:

                    # Check if URL is working 
                    _logger.info("......... Price Check Call - %r  %r ...........", url)
                    response = requests.get(url, header)
                    
                    
                    if response.status_code == 200:

                        product.product_status = "active"
                        self.process_product_page_data_for_price(product, response)

                    else:

                        product.product_status = 'inactive'
                        _logger.info(".......... Product URL Inactive with status code %r for product - %r.........!!!!!!!!",response.status_code, product.vendor_sku)

                except Exception as e:
                    _logger.info(".......Error while checking product url - %r",e)
            else:
                _logger.info("............Missing Url for -  %r ,......!!!!!!!!!",product.vendor_sku)
                

    ##########################
    # Process Product Prices #
    ##########################

    
    def process_product_page_data_for_price(self, product, response):
    
        soup = BeautifulSoup(response.content, 'html.parser')
        # _logger.info("~~~~~~~~~~~~%r~~~~~~~~~~", soup)
        out_of_stock_product = soup.find('div', {'class':'a-size-medium a-color-price'})

        if out_of_stock_product is not None:

            product.product_status = 'unavailable'
            _logger.info("............ Product Stock Unavailable -  %r ,........",product.vendor_sku)

        else:

            product.product_status = 'active'
            price_element = soup.find('span', {'class': 'a-price-whole'})
            _logger.info(">>>>>>>>>>>>>>%r,<<<<<<<<<<",price_element)
            
            if price_element is not None:
                
                _logger.info("............ Updated Product %r's Price -  %r ,........", product.vendor_sku, product.list_price_with_tax)

            else:
            
                product.product_status = 'price_unavailable'
                _logger.info("............ Product Price Unavailable -  %r ,......!!!!!!!!!",product.vendor_sku)
